import pickle
import traceback

import IPython

from form import Ui_MainWindow
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from part3 import ServerMessage
from user import User
import pandas as pd
from threading import Thread
from util import qt_get_host_port
import uuid
from blogDialog import Ui_Dialog


class ListTableModel(QAbstractTableModel):
    def __init__(self, columns):
        super().__init__()
        self.table = []
        self.columns = columns  # ['uuid', 'host', 'port']

    def rowCount(self, parent=None):
        return len(self.table)

    def columnCount(self, parent=None):
        return len(self.columns)

    def data(self, index, role=None):
        if role != Qt.DisplayRole:
            return QVariant()
        if index.row() < 0 or index.column() < 0:
            return QVariant()
        if len(self.table) <= index.row() or len(self.columns) <= index.column():
            return QVariant()
        return self.table[index.row()][index.column()]

    def headerData(self, section, orientation, role=None):
        if role != Qt.DisplayRole or orientation != Qt.Horizontal:
            return QVariant()
        return self.columns[section]


class ApplicationWindow(QMainWindow):
    def __init__(self):
        super(ApplicationWindow, self).__init__()
        self.inited = False
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        try:
            with open('style.qss', 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except:
            pass
        bind_host, bind_port = qt_get_host_port(self, '0.0.0.0', 22321)
        if bind_host is None or bind_port is None:
            return
        self.user = User(bind_host, bind_port, 'MagHSK')
        self.serverModel = ListTableModel(['uuid', 'host', 'port'])
        self.ui.serverTable.setModel(self.serverModel)
        self.blogModel = ListTableModel(['date', 'id', 'text'])
        self.ui.blogTable.setModel(self.blogModel)
        self.ui.refreshBlogButton.clicked.connect(self.refreshBlogButtonAction)
        self.ui.detailButton.clicked.connect(self.detailButtonAction)
        self.ui.subscribeButton.clicked.connect(self.subscribeButtonAction)
        self.ui.unsubscribeButton.clicked.connect(self.unsubscribeButtonAction)
        self.ui.updateButton.clicked.connect(self.updateButtonAction)
        self.ui.keywordButton.clicked.connect(self.keywordButtonAction)
        self.ui.refreshServerButton.clicked.connect(self.refreshServerButtonAction)
        self.ui.clearButton.clicked.connect(self.clearButtonAction)
        self.select_server = None
        self.select_blog = None
        self.client_thread = ClientThread(self)
        self.client_thread.serverUpdated.connect(self.refreshServer)
        self.client_thread.blogUpdated.connect(self.refreshBlog)
        self.client_thread.start()
        self.inited = True

    def clearButtonAction(self):
        try:
            confirm = QMessageBox.question(self, '请确认', '确认删除所有内容吗？')
            print(confirm)
            if confirm == QMessageBox.Yes:
                self.clearAll()
        except:
            traceback.print_exc()

    def clearAll(self):
        self.user.mblog_dict = {}
        self.refreshBlog()

    def refreshBlogButtonAction(self):
        try:
            self.user.positive_ask_blog()
            self.refreshBlog()

        except:
            traceback.print_exc()

    def detailButtonAction(self):
        try:
            row = self.getTableSelectedRow(self.ui.blogTable, len(self.blogModel.table))
            print(row)
            if row is not None:
                date, blog_id, text = self.blogModel.table[row]
                subwindow = QDialog(self)
                dialog = Ui_Dialog()
                dialog.setupUi(subwindow)
                dialog.IDLabel.setText(str(blog_id))
                dialog.blogContentEdit.setPlainText(text)
                subwindow.setWindowTitle("微博发表日期：" + date)
                subwindow.exec_()
                print('[** DEBUG **]  Sub window return:', subwindow.result())
                if subwindow.result() == QDialog.Accepted:
                    self.user.mblog_dict[int(blog_id)]['text'] = dialog.blogContentEdit.toPlainText()
                    self.refreshBlog()
        except:
            traceback.print_exc()


    def updateButtonAction(self):
        try:
            topic = self.ui.updateEdit.text().strip().split()
            row = self.getTableSelectedRow(self.ui.serverTable, len(self.serverModel.table))
            if row is not None:
                server_uuid = self.getServerUUIDbyRow(row)
                if server_uuid is not None:
                    self.user.send_topic_list(server_uuid, topic)
        except:
            traceback.print_exc()

    def keywordButtonAction(self):
        try:
            kwds = self.ui.keywordEdit.text().strip().split()
            row = self.getTableSelectedRow(self.ui.serverTable, len(self.serverModel.table))
            if row is not None:
                server_uuid = self.getServerUUIDbyRow(row)
                if server_uuid is not None:
                    mblog, topic = self.user.keyword_query(server_uuid, kwds)
                    if mblog:
                        blog_id, text = int(mblog['id']), mblog['text']
                        subwindow = QDialog(self)
                        dialog = Ui_Dialog()
                        dialog.setupUi(subwindow)
                        dialog.IDLabel.setText(str(blog_id))
                        dialog.blogContentEdit.setPlainText(text)
                        subwindow.setWindowTitle("类别：" + topic)
                        subwindow.exec_()
                        print('[** DEBUG **]  Sub window return:', subwindow.result())
                        if subwindow.result() == QDialog.Accepted:
                            mblog['text'] = dialog.blogContentEdit.toPlainText()
                            self.user.mblog_dict[int(blog_id)] = mblog
                            self.refreshBlog()
                            pass
                    else:
                        alert = QMessageBox(parent=self)
                        alert.setText('No such blog match your keywords.')
                        alert.exec_()
        except:
            traceback.print_exc()

    def getServerUUIDbyRow(self, row):
        if row < len(self.serverModel.table):
            try:
                server_uuid = uuid.UUID(self.serverModel.table[row][0])
            except Exception as e:
                alert = QMessageBox(parent=self)
                alert.setText('UUID invalid!')
                alert.exec_()
                return None
            print('You selected UUID', str(server_uuid))
            return server_uuid
        return None

    def getTableSelectedRow(self, target, maximum):
        lst = target.selectedIndexes()
        if len(lst) == 1:
            row = lst[0].row()
            if row < maximum:
                print('You selected row', row)
                return row
            pass
        alert = QMessageBox(parent=self)
        alert.setText('Please select exactly one server!')
        alert.exec_()
        return None

    def unsubscribeButtonAction(self):
        try:
            row = self.getTableSelectedRow(self.ui.serverTable, len(self.serverModel.table))
            if row is not None:
                server_uuid = self.getServerUUIDbyRow(row)
                print(server_uuid)
                if server_uuid is not None:
                    self.user.logout(server_uuid)
                    pass
                del self.serverModel.table[row]
                self.ui.serverTable.model().layoutChanged.emit()
        except:
            traceback.print_exc()
            pass

    def refreshServer(self):
        self.serverModel.table = [
            (str(server), v[0], v[1])
            for server, v in self.user.server_dict.items()
        ]
        self.ui.serverTable.model().layoutChanged.emit()

    def refreshBlog(self):
        print('Refresh blog!')
        self.blogModel.table = [
            (mblog['time'], str(blog_id), mblog['text'])
            for blog_id, mblog in self.user.mblog_dict.items()
        ]
        self.ui.blogTable.model().layoutChanged.emit()

    def refreshServerButtonAction(self):
        try:
            self.refreshServer()
        except:
            traceback.print_exc()

    def subscribeButtonAction(self):
        try:
            host, port = qt_get_host_port(self, '127.0.0.1', 23432)
            if host is None or port is None:
                return
            server_uuid = self.user.register((host, port))
            if server_uuid is not None:
                self.serverModel.table.append((str(server_uuid), host, port))
                self.ui.serverTable.model().layoutChanged.emit()
            else:
                alert = QMessageBox(parent=self)
                alert.setText('Register failed!')
                alert.exec_()
        except:
            traceback.print_exc()

    def receiveNewBlogs(self, mblog_list):
        for mblog in enumerate(mblog_list):
            self.user.mblog_dict[mblog['id']] = mblog


class ClientThread(QThread):
    serverUpdated = pyqtSignal()
    blogUpdated = pyqtSignal()

    def __init__(self, parent: ApplicationWindow = None):
        super().__init__()
        self.running = False
        self.window = parent

    def run(self):
        self.running = True
        print('client thread waiting connection ...')
        self.window.user.socket.listen()
        while self.running:
            conn, _ = self.window.user.socket.accept()
            server_uuid, msg, data = pickle.loads(User.large_recv(conn))
            conn.close()
            if msg == ServerMessage.ASK_ALIVE:
                self.window.user.response_alive(server_uuid, data)
                pass
            elif msg == ServerMessage.NEW_BLOG:
                self.window.user.response_blog(server_uuid, data)
                self.blogUpdated.emit()
                pass
            elif msg == ServerMessage.KICK:
                self.window.user.response_kick(server_uuid, data)
                self.serverUpdated.emit()
                pass


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    window = ApplicationWindow()
    if not window.inited:
        sys.exit(0)
    window.show()
    sys.exit(app.exec_())
