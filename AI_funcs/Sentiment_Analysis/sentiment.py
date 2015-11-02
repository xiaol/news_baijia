# -*- coding:utf8 -*-
from __future__ import print_function
__author__ = 'Weiliang Guo'

import sys
reload(sys)
sys.setdefaultencoding('utf8')
from controller.config import dbConn
import re
import jieba.posseg as pseg
from AI_funcs.OpinionClassifier.Apriori_Test.apriori import runApriori, printResults
import random, string
import json
import jieba
from itertools import combinations
from AI_funcs.snownlp.snownlp import SnowNLP
from AI_funcs.Extraction.extractor import get_quote_text
from AI_funcs.snownlp.snownlp import sentiment

def docs():
    dbstore = dbConn.GetDateStore()
    conn = dbstore._connect_news
    # result_doc = conn["news_ver2"]["googleNewsItem"].find({"eventId": {"$exists": 1}, "text": {"$exists":1}}).sort([("createTime", -1)]).limit(10)
    result_doc = conn["news_ver2"]["googleNewsItem"].find({"eventId": {"$exists": 1}, "text": {"$exists":1}, 'createTime':{"$gte": '2015-07-26 06:00:00',"$lt": '2015-07-27 06:00:00'}, "eventId":{'$exists': True}, "duplicate_check":{'$exists': True}}).sort([("createTime", -1)]).skip(10).limit(1000)
    sens_and_ids = {}
    sorted_docs = {}
    for result_elem in result_doc:

        eventId = result_elem["eventId"]
        article = result_elem["text"]
        article_id = result_elem["sourceUrl"]
        article = article.encode('utf-8')
        # setences = re.split(r'\.|。', article)
        if eventId not in sorted_docs.keys():
            sorted_docs[eventId] = {article_id: article}
        else:
            sorted_docs[eventId][article_id] = article
    return sorted_docs


class Sentiment:
    def __init__(self, neg_train_file='neg.txt', pos_train_file='pos.txt'):
        sentiment.train(neg_train_file, pos_train_file)
        sentiment.save('sentiment.marshal')

    def get_sentiment(self,text=''):
        if text:
            txt = text.decode('utf8')
            txt = txt.replace(' ', '').strip()
            sn_obj = SnowNLP(txt)
            senti_score = sn_obj.sentiments
            print('Sentiment score: ' + str(senti_score))
            return senti_score
        else:
            print('Empty text!')

if __name__ == '__main__':
    """
    docs = docs()
    for key, value in docs.iteritems():
        print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
        print('Event ID: ' + key)
        for ke, va in value.iteritems():
            print('~~~~~~~~~~~~~~~~~~~~~~~~~~~')
            print('Article ID: ' + ke)
        #     for v in va:
        #         v = v.decode('utf8')
        #         print('~~~~~~~~~~~~~~~~~~~~~~~')
        #         #print sentence

            if not va:
                print('Oops! Empty article!')
            else:
                quotes = get_quote_text(va)
                for quo in quotes:
                    print('-------------------')
                    print('Quote: ' + quo)
                    get_sentiment(quo)
    """
    neg = open("negative.txt", "r")
    print(type(neg))
    pos = open("positive.txt", "r")
    print(type(pos))
    sen_obj = Sentiment(neg_train_file='negative.txt', pos_train_file='positive.txt')
    sen_obj.get_sentiment('微信公众号上发布的广告已纳入监管视野')
    sen_obj.get_sentiment('工商部门执法成本巨大')
    # for n in neg:
    #     print(n)
    #     sen_obj.get_sentiment(n)
    # print('**********************')
    # for p in pos:
    #     print(p)
    #     sen_obj.get_sentiment(p)

