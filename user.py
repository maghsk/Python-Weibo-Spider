import pickle
import socket
import uuid

from part3 import ServerMessage, ClientMessage


class User(object):
    def __init__(self, listen_host: str, listen_port: int, user_name: str):
        # 微博用户的初始化方法
        self.addr = (listen_host, listen_port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.addr)
        self.name = user_name
        self.uuid = uuid.uuid4()
        self.server_dict = {}
        self.mblog_dict = {}

    def register(self, server_addr: (str, int), force: bool=False):
        # 注册服务器
        print('Register to', server_addr)
        if (not force) and server_addr in self.server_dict:
            print("Already registered.")
            return None

        try:
            client = socket.socket()
            client.connect(server_addr)
            server_uuid, msg = pickle.loads(client.recv(4096))
            assert msg == ServerMessage.WELCOME
            client.send(pickle.dumps((self.uuid, ClientMessage.SUBSCRIBE, self.addr)))
            msg = pickle.loads(client.recv(4096))
            client.close()
        except:
            print('Network error')
            return None

        if msg == ServerMessage.UNAVAILABLE:
            print('Registering on server not supported.')
            return None

        self.server_dict[server_uuid] = server_addr
        print('Register successful.')
        return server_uuid

    def logout(self, server_uuid: uuid.UUID, force=False):
        if (not force) and server_uuid not in self.server_dict:
            print("Already logged out.")
            return -1

        try:
            with socket.socket() as client:
                client.connect(self.server_dict[server_uuid])
                server_uuid, msg = pickle.loads(client.recv(4096))
                assert msg == ServerMessage.WELCOME

                client.send(pickle.dumps((self.uuid, ClientMessage.UNSUBSCRIBE, None)))
                msg = pickle.loads(client.recv(4096))
                assert msg == ServerMessage.DONE
        except:
            pass

        if server_uuid in self.server_dict:
            del self.server_dict[server_uuid]
        print("Logout successful.")
        return 0

    def send_topic_list(self, server_uuid, topic_list):
        # 用户向微博注册并发送自己的兴趣
        if server_uuid not in self.server_dict:
            return "Not registered yet."

        with socket.socket() as client:
            client.connect(self.server_dict[server_uuid])
            server_uuid, msg = pickle.loads(client.recv(4096))
            assert msg == ServerMessage.WELCOME
            client.send(pickle.dumps((self.uuid, ClientMessage.UPDATE_TOPIC, topic_list)))
            msg = pickle.loads(client.recv(4096))
            assert msg == ServerMessage.DONE

        print('Sent topic to', str(server_uuid))

    def response_alive(self, server_uuid, client_uuid):
        if server_uuid in self.server_dict:
            try:
                with socket.socket() as client:
                    if self.uuid == client_uuid:
                        client.connect(self.server_dict[server_uuid])
                        client.send(pickle.dumps((self.uuid, ClientMessage.ALIVE, server_uuid)))
                    else:
                        del self.server_dict[server_uuid]
                        client.send(pickle.dumps((self.uuid, ClientMessage.DIED, server_uuid)))
            except:
                pass

    def response_blog(self, server_uuid, mblog_list):
        print('Response blog')
        if server_uuid in self.server_dict:
            print("Server updated !!!")
            for idx, mblog in enumerate(mblog_list):
                self.mblog_dict[mblog['id']] = mblog
                print('%d. %s' % (idx, mblog['text']))
                pass
        else:
            print("Received message but server is not known !!!")

    def response_kick(self, server_uuid, data):
        if server_uuid in self.server_dict:
            self.logout(self.server_dict[server_uuid], force=True)
            del self.server_dict[server_uuid]

    def positive_ask_blog(self):
        print(self.server_dict)
        for server_uuid, v in self.server_dict.items():
            server_addr = v
            s = socket.socket()
            try:
                s.connect(server_addr)
                server_uuid, msg = pickle.loads(s.recv(4096))
                assert msg == ServerMessage.WELCOME
                s.send(pickle.dumps((self.uuid, ClientMessage.GET_BLOG, None)))
                msg = pickle.loads(s.recv(4096))
                assert msg == ServerMessage.DONE
            except ConnectionRefusedError as e:
                print('Connection refused')
            except:
                print('Server response meaningless things')

    def get_blog_text_list(self):
        ret = []
        for v in self.mblog_dict.values():
            ret.append(v['text'])
        return ret

    def reader_wait(self):
        self.socket.listen()
        while True:
            conn, _ = self.socket.accept()
            server_uuid, msg, data = pickle.loads(User.large_recv(conn))
            conn.close()
            if msg == ServerMessage.ASK_ALIVE:
                self.response_alive(server_uuid, data)
                pass
            elif msg == ServerMessage.NEW_BLOG:
                self.response_blog(server_uuid, data)
                pass
            elif msg == ServerMessage.KICK:
                self.response_kick(server_uuid, data)
                pass

    @staticmethod
    def large_recv(conn):
        data = []
        while True:
            packet = conn.recv(4096)
            if not packet: break
            data.append(packet)
        return b"".join(data)

    def keyword_query(self, server_uuid: uuid.UUID, kwds: list):
        assert server_uuid in self.server_dict
        with socket.socket() as client:
            client.connect(self.server_dict[server_uuid])
            server_uuid, msg = pickle.loads(client.recv(4096))
            assert msg == ServerMessage.WELCOME

            client.send(pickle.dumps((self.uuid, ClientMessage.KEYWORD_QUERY, kwds)))
            msg, data = pickle.loads(client.recv(4096))
            assert msg == ServerMessage.DONE
        return data
