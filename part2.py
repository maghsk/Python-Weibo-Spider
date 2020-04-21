import random

from part1 import Crawler
from part1 import MBLOG_PICKLE_DIR
import pickle
import os
import datetime
import jieba
import jieba.analyse
import numpy as np
from sklearn.naive_bayes import MultinomialNB
import MinEditDist
from util import same_category, set_label_list, OTHER_NAME

MIN_TRAIN_FILES = 20            # 训练所需最少文件数
MIN_TRAIN_SIZE = 100            # 每个tag训练所需最少文章数

# 设4个类


class Saver(object):
    def __init__(self, trainer):
        self.total_words = trainer.total_words
        self.word_dict = trainer.word_dict
        self.model = trainer.model

class Trainer(object):
    def __init__(self, model_path, train_data_path):
        # model_path 是模型的保存路径
        self.train_data_path = train_data_path
        self.total_words = 0
        self.word_dict = {}
        self.model_path = model_path
        self.model = MultinomialNB()

    def nearest(self, kwd):
        ans = len(kwd)
        lst = []
        for word in self.word_dict:
            tmp = MinEditDist.dis(kwd, word)
            if tmp == ans:
                lst.append(word)
            elif ans > tmp:
                ans = tmp
                lst = [word]
        if len(lst) == 0:
            return None
        return random.choice(lst)

    def prepare_data(self, min_size=None, max_size=None):
        # return a list with dict structure
        lst = os.listdir(self.train_data_path)
        if (not os.path.exists(self.train_data_path)) or (min_size is not None and len(lst) < min_size):
            for i in lst:
                os.remove(self.train_data_path+'/'+i)
            craw = Crawler(min_size, myid=1800013097, nowtime=datetime.date.today().strftime('%Y%m%d'), craw_comments=False)
            craw.saveWeibo(self.train_data_path)
            return craw.info
        else:
            ret = []
            for fname in lst:
                if fname.endswith('.pkl'):
                    with open(self.train_data_path+'/'+fname, 'rb') as fp:
                        ret.append(pickle.load(fp))
                        if max_size is not None and len(ret) == max_size:
                            break
            return ret

    def load_model(self):
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                saver = pickle.load(f)
            if type(saver) != Saver:
                print('Load failed!')
                return False
            print('Load successful!')
            self.total_words = saver.total_words
            self.word_dict = saver.word_dict
            self.model = saver.model
            return True
        else:
            print('Load failed!')
            return False

    def convert_weight_to_nparray(self, tfidf):
        ret = np.zeros(self.total_words)
        for word, weight in tfidf:
            if word in self.word_dict:
                ret[self.word_dict[word]] = weight
        return ret

    def save_model(self):
        with open(self.model_path, 'wb') as f:
            pickle.dump(Saver(self), f)
        print('Model saved!')

    def convert_select_form_to_XY(self, select):
        X = []
        Y = []
        for k,v in select.items():
            for tfidf in v:
                X.append(self.convert_weight_to_nparray(tfidf))
                Y.append(set_label_list[k])
        return X, Y

    def convert_select_slice_form_to_X(self, select_slice):
        X = []
        for tfidf in select_slice:
            X.append(self.convert_weight_to_nparray(tfidf))
        return X

    @staticmethod
    def get_select_form(mblog_info_list, max_train_size=None):
        jieba.analyse.set_stop_words('./stopword.txt')
        prime_select = {tag: [] for tag in set_label_list}
        for idx, mblog in enumerate(mblog_info_list):
            if any([(max_train_size is None or len(lst) < max_train_size) for lst in prime_select.values()]):
                for k, v in prime_select.items():
                    if len(v) < MIN_TRAIN_SIZE and same_category(k, mblog['tag']):
                        v.append(jieba.analyse.extract_tags(mblog['text'], withWeight=True, topK=None))
        return prime_select

    @staticmethod
    def get_select_slice_form(mblog_info_list, max_train_size=None):
        jieba.analyse.set_stop_words('./stopword.txt')
        ret = []
        for idx, mblog in enumerate(mblog_info_list):
            if max_train_size is None or len(ret) < max_train_size:
                ret.append(jieba.analyse.extract_tags(mblog['text'], withWeight=True, topK=None))
        return ret

    def train(self, min_size, max_size, need_test=False, train_ratio=1.0):
        # 爬取数据进行训练
        jieba.analyse.set_stop_words('./stopword.txt')
        train_data = self.prepare_data(min_size, max_size)
        prime_select = self.get_select_form(train_data, MIN_TRAIN_SIZE)
        for k, v in prime_select.items():
            for post in v:
                for word, _ in post:
                    if word not in self.word_dict:
                        self.word_dict[word] = self.total_words
                        self.total_words += 1

        if need_test:
            train_select = {tag : prime_select[tag][:int(len(prime_select[tag])*train_ratio)] for tag in set_label_list}
            test_select = {tag : prime_select[tag][int(len(prime_select[tag])*train_ratio):] for tag in set_label_list}
        else:
            train_select = test_select = prime_select

        X, Y = self.convert_select_form_to_XY(train_select)

        # print(train_select)
        print([len(lst) for lst in train_select.values()])
        self.model.fit(X, Y)
        print('Finished training!')
        if need_test:
            self.test(test_select)

    def classify(self, X):
        # X: 2d-array like
        return self.model.predict(X)

    def test(self, mblog_info_list, show_output=True):
        test_X, test_Y = self.convert_select_form_to_XY(mblog_info_list)
        pred_Y = self.classify(test_X)
        res = np.zeros(shape=(4, 4))
        acc = 0
        for t,p in zip(test_Y,pred_Y):
            res[t][p] += 1
            if t == p:
                acc += 1
        acc = acc / len(test_Y)
        if show_output:
            print(res)
            print("Acc:", acc)
        return acc


class NewBlog(object):
    def __init__(self, model_path, train_data_path=MBLOG_PICKLE_DIR, train_now=False):
        # model_path 是模型的保存路径
        self.trainer = Trainer(model_path, train_data_path)
        self.dictionary = {v: k for k, v in set_label_list.items()}
        if train_now:
            self.trainer.train(min_size=None, max_size=2000, need_test=True, train_ratio=0.5)

    def get(self, blog_num=8, do_page_pickle=False, sleep_every_craw=True):
        # 爬取数据用已训练好的模型进行分类
        craw = Crawler(blog_num, myid=1800013097, nowtime=datetime.date.today().strftime('%Y%m%d'),
                       do_page_pickle=do_page_pickle, sleep_every_craw=sleep_every_craw, craw_comments=False)
        mblog_info_list = craw.info
        select_slice = self.trainer.get_select_slice_form(mblog_info_list)
        X = self.trainer.convert_select_slice_form_to_X(select_slice)
        Y = self.trainer.classify(X)
        for idx, pred in enumerate(Y):
            mblog_info_list[idx]['tag'] = [self.dictionary[pred]]
        return mblog_info_list

    def keyword_query(self, keyword_list):
        mblog_info_list = [{'text' : '$#$@'.join(keyword_list)}]
        select_slice = self.trainer.get_select_slice_form(mblog_info_list)
        X = self.trainer.convert_select_slice_form_to_X(select_slice)
        return self.trainer.classify(X)[0]

    def keyword_query_str(self, keyword_list):
        tmp = []
        for kwd in keyword_list:
            if kwd in self.trainer.word_dict:
                tmp.append(kwd)
            else:
                try:
                    alter = self.trainer.nearest(kwd)
                    if alter:
                        print(kwd, 'not found, use', alter, 'for alternative.')
                        tmp.append(alter)
                except:
                    pass

        if len(tmp) == 0:
            return OTHER_NAME
        return self.dictionary[self.keyword_query(tmp)]


if __name__ == '__main__':
    nblog = NewBlog('./nlp-classifier.model', MBLOG_PICKLE_DIR, train_now=True)
    nblog.trainer.load_model()
    # print(nblog.trainer.word_dict)
    for lst in [['科研'], ['燕园'], ['欧洲'], ['量子'], ['蛋白酶']]:
        print('Input:', lst)
        print('Output:', nblog.keyword_query_str(lst))
