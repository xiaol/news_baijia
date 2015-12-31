# -*- coding:utf8 -*-
__author__ = 'Weiliang Guo'

import sys
reload(sys)
sys.setdefaultencoding('utf8')
from controller.config import dbConn
import re
import pymongo
import jieba
import simplejson
import _uniout
import uniout


class Mongodb:
    def __init__(self):
        self.conn = pymongo.MongoClient('h213', 27017)
        self.db = self.conn['AI_funcs']

    def retrieve_channel_items(self):
        db = self.conn['news_ver2']
        cursor_obj = db.ChannelItems.find()
        channels = {}
        for c in cursor_obj:
            ch_id = float(c['channel_id'])
            channel_name = c['channel_name']
            channels[channel_name] = ch_id
        return channels

    def retrieve_news_items(self):
        db = self.conn['news_ver2']
        cursor_obj = db.NewsItems.find().skip(1).limit(10)
        texts = []
        for cuo in cursor_obj:
            try:
                content = cuo['content']
                channel = cuo['channel']
                obj_id = cuo['_id']
                # print(content)
                # print('***************************************************************')
                # print(channel)
                text = []
                for cu in content:
                    # print('------------------------------------------------------------')
                    for k, v in cu.iteritems():
                        for kk, vv in v.iteritems():
                            if kk == 'txt':
                                text.append(vv)
                                # print(vv)
                text = ''.join(text)
                if text:
                    # print('text True')
                    text = (channel, text)
                    texts.append(text)
                    # print(text)
                    # print('***************************************************************')
                else:
                    continue
            except:
                continue
        print('all texts')
        print(len(texts))
        print(type(texts))
        # print(texts)
        # texts is a list of dictionaries which are 'channel: text' pairs.
        return texts

    def prepare_data_for_naive_bayes_model(self):
        nbmtd = open('naive_bayes_model_training_data.data', 'w+r')
        stopwords_raw = open('stopword.data', 'r').readlines()
        stopwords = []
        for sw in stopwords_raw:
            ll = sw.strip()
            stopwords.append(ll)
        print(stopwords)

        db = self.conn['news_ver2']
        cursor_obj = db.NewsItems.find().limit(1000)
        for cuo in cursor_obj:
            try:
                content = cuo['content']
                channel_id = float(cuo['channel_id'])
                obj_id = cuo['_id']
                # print(content)
                # print('***************************************************************')
                # print(channel)
                text = []
                for cu in content:
                    # print('------------------------------------------------------------')
                    for k, v in cu.iteritems():
                        for kk, vv in v.iteritems():
                            if kk == 'txt':
                                text.append(vv)
                                # print(vv)
                text = ''.join(text)
                if text:
                    # print('text True')
                    text = jieba.cut(text)
                    text = [x.strip() for x in text]
                    for w in text:
                        if w in stopwords:
                            text.remove(w)
                    text = ' '.join(text)
                    text = {'text': text, 'label': channel_id}
                    print(text)
                    # texts.append(text)
                    # print(text)
                    # text = _uniout.unescape(str(text), 'utf8')
                    nbmtd.write(str(text) + '\n')
                    # print('***************************************************************')
                else:
                    continue
            except:
                continue
        # nn = {'model': 'naive_bayes', 'data': texts}
        # self.db.model_data.insert_one(nn)
        # return texts

if __name__ == '__main__':
    mg = Mongodb()
    print(mg.retrieve_channel_items())
    print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
    mg.prepare_data_for_naive_bayes_model()
    print('Nice!!!')
    # ddd = mg.db.model_data.find_one({"model": "naive_bayes"})
    # if ddd['data']:
    #     print('Nice!!!')

