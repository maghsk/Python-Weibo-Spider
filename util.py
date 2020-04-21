import datetime
import re
import uuid

from PyQt5.QtWidgets import QInputDialog


def get_host_port(default_host='0.0.0.0', default_port=22321):
    ret_host = input('Bind host(%s)' % default_host)
    if len(ret_host) <= 0:
        ret_host = default_host
    try:
        ret_port = int(input('Bind port(%d)' % default_port))
        assert 0 < ret_port < 65536
    except:
        ret_port = default_port
    return ret_host, ret_port


def qt_get_host_port(parent, default_host, default_port):
    host, ok = QInputDialog.getText(parent, 'Input Dialog', 'Enter bind host:', text=default_host)
    if not ok:
        return None, None
    port, ok = QInputDialog.getInt(parent, 'Input Dialog', 'Enter bind port:', value=default_port, min=1, max=65535, step=1)
    if not ok:
        return None, None
    return host, port


def get_one_uuid(default_uuid=None):
    try:
        HINT = 'Input UUID:'
        if default_uuid:
            HINT = 'Input UUID (%s):' % default_uuid
        server_uuid = uuid.UUID(input(HINT))
    except:
        if default_uuid:
            return default_uuid, True
        print('Check your input!')
        return None, False
    return server_uuid, True


def OnlyChinese(text):
    return re.sub(u"[^\u4e00-\u9fa5]+", " ", text)


def WeiboTime2ISO(text):
    now = datetime.datetime.now()
    ree = re.match(YEST, text)
    if ree:
        tmp = ree.groups()
        ret = now - datetime.timedelta(days=1)
        return ret.strftime('%Y-%m-%d')

    ree = re.match(HOUR, text)
    if ree:
        tmp = ree.groups()
        ret = now - datetime.timedelta(hours=int(tmp[0]))
        return ret.strftime('%Y-%m-%d')

    ree = re.match(MD, text)
    if ree:
        tmp = ree.groups()
        return "%04d-%02d-%02d" % (now.year, int(tmp[0]), int(tmp[1]))
    ree = re.match(YMD, text)
    if ree:
        tmp = ree.groups()
        return "%04d-%02d-%02d" % (int(tmp[0]), int(tmp[1]), int(tmp[2]))
    return now.strftime('%Y-%m-%d')

def inout_decorator(func):
    def work(*args):
        print(' --- Calling func: %s --- ' % func.__name__)
        print(args)
        ret = func(*args)
        print(' --- Return Value:', ret, '--- ')
    return work


def same_category(kwd, mblog_tags):
    return kwd in mblog_tags or (kwd == OTHER_NAME and not any(mblog_tag in set_label_list for mblog_tag in mblog_tags))


HOUR = u'^([0-9]+).*小时前$'
YEST = u'^昨天.*$'
MD = '^([0-9]+)-([0-9]+)$'
YMD = '^([0-9]+)-([0-9]+)-([0-9]+)$'
OTHER_NAME = '其他'
set_label_list = {
    '北大科研': 0,
    '高校学堂计划': 1,
    '大美北大': 2,
    '其他': 3
}