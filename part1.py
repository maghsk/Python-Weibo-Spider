# -*- coding:utf-8 -*-
from urllib.parse import urlencode
import requests
import pickle
import jieba
from bs4 import BeautifulSoup
import jieba.analyse
import datetime
import os
import json
import time
import random

from util import OnlyChinese, WeiboTime2ISO

DO_PAGE_PICKLE = False                  # 是否保留每次抓取的页面（本地测试可加快速度）
PAGE_PICKLE_DIR = './page_pkl'          # 抓取页面保存路径

DO_MBLOG_PICKLE = True                  # 是否保存每条微博（**基础要求**）
MBLOG_PICKLE_DIR = './weibo_pkl'        # 每条微博保存路径

CRAW_COMMENTS = True                    # 是否爬取评论（**进阶要求**）
STOP_WORDS_PATH = './stopword.txt'      # TF-IDF 分析中停表的路径

SLEEP_EVERY_CRAW = 3                    # 每次爬取新页面，暂停的时长


class PageGetter:
    def __init__(self, base_url, headers, base_params, do_page_pickle, sleep_every_craw):
        self.base_url = base_url
        self.headers = headers
        self.params = base_params
        self.curPage = 0
        self.do_page_pickle = do_page_pickle
        self.mblog_set = set()
        self.sleep_every_craw = sleep_every_craw

    def get_page(self, page):
        if self.sleep_every_craw:
            time.sleep(random.random() + SLEEP_EVERY_CRAW)
        self.params['page'] = page
        url = self.base_url + urlencode(self.params)
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
        except requests.ConnectionError as e:
            print('Error', e.args)

    def get_next_mblog(self, craw_comments=False):
        jieba.analyse.set_stop_words(STOP_WORDS_PATH)
        if not os.path.exists(PAGE_PICKLE_DIR):
            os.mkdir(PAGE_PICKLE_DIR)
        while True:
            self.curPage += 1
            if self.do_page_pickle:
                pickle_name = PAGE_PICKLE_DIR + '/' + 'weibo-page.' + str(self.curPage) + '.pkl'
                if os.path.exists(pickle_name):
                    with open(pickle_name, 'rb') as f:
                        json = pickle.load(f)
                else:
                    json = self.get_page(self.curPage)
                    with open(pickle_name, 'wb') as f:
                        pickle.dump(json, f)
            else:
                json = self.get_page(self.curPage)

            for card in json['data']['cards']:
                if 'mblog' not in card:
                    continue
                if 'text' not in card['mblog']:
                    continue
                mblog = card['mblog']
                blog_id = int(mblog['id'])
                if blog_id in self.mblog_set:
                    continue
                else:
                    self.mblog_set.add(blog_id)
                html = mblog['text']
                soup = BeautifulSoup(html, features="lxml")
                tags = []
                for a in soup.findAll('a'):
                    st = a.get_text()
                    if st.startswith('#') and st.endswith('#'):
                        tags.append(st[1:-1])
                        a.decompose()
                    if st.startswith('@') or st == '全文':
                        a.decompose()

                ret = dict(tag=tags, id=blog_id, text=soup.get_text().strip(), time=WeiboTime2ISO(mblog['created_at']),
                           comment=mblog['comments_count'], forward=mblog['reposts_count'],
                           like=mblog['attitudes_count'], other=[], keyword=[word for word in
                                                                             jieba.analyse.extract_tags(
                                                                                 OnlyChinese(soup.get_text()),
                                                                                 topK=8)])
                if craw_comments:
                    comment_params = {
                        'id': blog_id,
                        'page': 1
                    }
                    comment_base_url = 'https://m.weibo.cn/api/comments/show?'
                    cgetter = PageGetter(comment_base_url, self.headers, comment_params, do_page_pickle=False, sleep_every_craw=SLEEP_EVERY_CRAW)
                    json = cgetter.get_page(1)
                    if 'data' in json and 'data' in json['data']:
                        for comment in json['data']['data']:
                            if 'text' in comment:
                                ret['other'].append(comment['text'])
                                break
                yield ret


class Crawler(object):
    def __init__(self, num, myid, nowtime, prefix='testhw', craw_comments=False, do_page_pickle=DO_PAGE_PICKLE, sleep_every_craw=True):
        self.num = num  # 需要爬取的微博数目
        self.id = myid  # 学生证
        self.prefix = prefix  # 保存的文件名，可自定义记录，不可重复
        self.time = nowtime  # 调用crawler的日期，格式例如'20200401'
        self.info = []

        base_url = 'https://m.weibo.cn/api/container/getIndex?'
        headers = {
            'Host': 'm.weibo.cn',
            'Referer': 'https://m.weibo.cn/u/3237705130',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0',
            'X-Requested-With': 'XMLHttpRequest',
        }
        timeline_params = {
            'type': 'uid',
            'value': '3237705130',
            'containerid': '1076033237705130',
        }
        self.pgetter = PageGetter(base_url, headers, timeline_params, do_page_pickle, sleep_every_craw)
        self.mblog_iter = self.pgetter.get_next_mblog(craw_comments)
        for i in range(self.num):
            self.info.append(next(self.mblog_iter))

    def saveWeibo(self, path, start_from=0):
        if not os.path.exists(path):
            os.mkdir(path)
        for i in range(self.num):
            if i < start_from:
                continue
            with open(path+'/id_{id}_prefix_{pre}_time_{time}_no_{no}.pkl'.format(pre=self.prefix, id=self.id, time=self.time,
                                                                            no=i), 'wb') as wf:
                pickle.dump(self.info[i], wf)


if __name__ == '__main__':
    craw = Crawler(10, myid=1800013097, nowtime=datetime.date.today().strftime('%Y%m%d'), craw_comments=CRAW_COMMENTS)
    # print(craw.info)
    # 爬虫及相关处理
    with open('weibos.json', 'w', encoding='utf-8') as fp:
        json.dump(craw.info, fp, ensure_ascii=False)
    if DO_MBLOG_PICKLE:
        craw.saveWeibo(MBLOG_PICKLE_DIR)


