import os
import pickle
import socket
import time
import uuid
from multiprocessing import Manager, Process, Pool

from part2 import NewBlog
from util import same_category
from part3 import ServerMessage, ClientMessage


def still_alive(client, addr, uuid):
    ret = True
    try:
        s = socket.socket()
        s.settimeout(5)
        s.connect(addr)
        s.send(pickle.dumps((uuid, ServerMessage.ASK_ALIVE, client)))
    except:
        ret = False

    if not ret:
        print('Should remove', client)
    return ret


def send_for_reader(reader, mblog_dict, server_uuid):
    """
    :param reader:
    :param mblog_dict:
    :param server_uuid:
    :return:
    """
    addr, topics = reader['addr'], reader['topics']
    snd = [mblog for mblog in mblog_dict.values() if any(same_category(kwd, mblog['tag']) for kwd in topics)]
    print('To send:', addr)
    print('User topic:', topics)
    print('Send length:', len(snd))
    for mblog in mblog_dict.values():
        print(mblog['tag'])

    try:
        with socket.socket() as client:
            client.settimeout(2)
            client.connect(addr)
            client.send(pickle.dumps((server_uuid, ServerMessage.NEW_BLOG, snd)))
    except:
        return False
    return True


class WeiBo(object):
    def __init__(self, file_path, listen_host, listen_port, uuid=None):
        """
        初始化服务器类
        :param file_path:str 微博用来保存微博用户的本地文档
        :param listen_host:str 监听 host name
        :param listen_port:int 监听端口
        """
        self.manager = Manager()
        self.addr = (listen_host, listen_port)
        self.socket = None
        self.mblog_dict = {}
        self.blog_source = NewBlog('./nlp-classifier.model')
        self.file_path = file_path
        if os.path.exists(file_path):
            print('[** DEBUG **]  Reading client list from file.')
            with open(file_path, 'rb') as fp:
                self.client_dict = self.manager.dict(pickle.load(fp))
            print('[** DEBUG **]  Read client list ', dict(self.client_dict))
        else:
            self.client_dict = self.manager.dict()  # (key=UUID, val= {'addr': addr, 'topics' = []} )
        self.listen_thread = None
        self.poll_thread = None
        self.still_pool = False
        self.accept_register = False
        if uuid:
            self.uuid = uuid
        else:
            self.uuid = uuid.uuid4()

    def server_poll(self, num, wait_sec=30, do_send=True):
        """
        服务器轮询更新微博函数
        :param num: 每次更新微博数目
        :param wait_sec: 轮询间隔时长
        :param do_send: 是否将结果发送给客户端
        :return: 无返回值
        """
        self.still_pool = True
        while self.still_pool:
            self.get_new_blogs(num)
            if do_send:
                self.send()
            time.sleep(wait_sec)

    def enable_register(self):
        self.accept_register = True

    def get_new_blogs(self, num):
        mblog_list = self.blog_source.get(blog_num=num, do_page_pickle=False, sleep_every_craw=True)
        for mblog in mblog_list:
            if mblog['id'] not in self.mblog_dict:
                self.mblog_dict[mblog['id']] = mblog

    def send(self):
        pool = Pool(4)
        for client,reader in self.client_dict.items():
            pool.apply_async(send_for_reader, args=(reader, self.mblog_dict, self.uuid))

        pool.close()
        pool.join()

    def server_wait(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.addr)
        self.socket.listen()
        print('Start waiting')
        while True:
            conn, addr = self.socket.accept()
            p = Process(target=handle, args=(conn, self, addr))
            p.daemon = True
            p.start()
            conn.close()

    def alive_check(self):
        """
        简单的客户端存活检测
        :return: 无
        """
        lst = []
        pool = Pool(4)
        for client,data in self.client_dict.items():
            lst.append((client, pool.apply_async(still_alive, args=(client, data['addr'], self.uuid))))

        pool.close()
        pool.join()

        for client, result in lst:
            if not result.get():
                print('[** DEBUG **]  Removing', client, self.client_dict[client]['addr'])
                del self.client_dict[client]

    def kick(self, client_uuid):
        if client_uuid in self.client_dict:
            print('[** DEBUG **]  Kicking', str(client_uuid))
            try:
                addr = self.client_dict[client_uuid]['addr']
                with socket.socket() as client:
                    client.settimeout(1)
                    client.connect(addr)
                    client.send(pickle.dumps((self.uuid, ServerMessage.KICK, client_uuid)))
            except:
                pass
            del self.client_dict[client_uuid]


def handle(conn:socket.socket, self: WeiBo, addr):
    conn.send(pickle.dumps((self.uuid, ServerMessage.WELCOME)))

    client_uuid, op, data = pickle.loads(conn.recv(4096))
    print(op)
    assert type(op) == ClientMessage
    if op == ClientMessage.SUBSCRIBE:
        if self.accept_register:
            self.client_dict[client_uuid] = {'addr': (addr[0], data[1]), 'topics': []}
            conn.send(pickle.dumps(ServerMessage.DONE))
            with open(self.file_path, 'wb') as fp:
                pickle.dump(dict(self.client_dict), fp)
        else:
            conn.send(pickle.dumps(ServerMessage.UNAVAILABLE))
    elif op == ClientMessage.UNSUBSCRIBE:
        if client_uuid in self.client_dict:
            del self.client_dict[client_uuid]
        conn.send(pickle.dumps(ServerMessage.DONE))
    elif op == ClientMessage.UPDATE_TOPIC:
        self.client_dict[client_uuid] = {'addr': self.client_dict[client_uuid]['addr'], 'topics': data}
        # client_dict[client_uuid]['topics'] = data
        conn.send(pickle.dumps(ServerMessage.DONE))
        with open(self.file_path, 'wb') as fp:
            pickle.dump(dict(self.client_dict), fp)
        print('[** DEBUG **]  UPDATE TOPIC Data', data)
        print('[** DEBUG **]  CLIENT DICT', self.client_dict)
    elif op == ClientMessage.GET_BLOG:
        send_for_reader(self.client_dict[client_uuid], self.mblog_dict, self.uuid)
        conn.send(pickle.dumps(ServerMessage.DONE))
    elif op == ClientMessage.DIED or op == ClientMessage.ALIVE and (data != self.uuid or client_uuid not in self.client_dict):
        if client_uuid in self.client_dict:
            del self.client_dict[client_uuid]
        pass
    elif op == ClientMessage.STRING:
        pass
    elif op == ClientMessage.KEYWORD_QUERY:
        topic = self.blog_source.keyword_query_str(data)
        snd = next(iter(mblog for _,mblog in sorted(self.mblog_dict.items(), reverse=True) if same_category(topic, mblog['tag'])), None)
        # 因为微博已经按id从大到小排序完毕，所以next返回的就是最新的微博
        conn.send(pickle.dumps((ServerMessage.DONE, (snd, topic))))
        pass
