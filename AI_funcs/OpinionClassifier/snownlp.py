# -*- coding:utf8 -*-
from __future__ import print_function
__author__ = 'Weiliang Guo'

import sys
reload(sys)
sys.setdefaultencoding('utf8')
from controller.config import dbConn
import re
import jieba.posseg as pseg
from Apriori_Test.apriori import runApriori, printResults
import random, string
import json
import jieba
from itertools import combinations
from AI_funcs.snownlp.snownlp import SnowNLP


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


def sentiment(documents):
    for key, value in documents.iteritems():
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
                va = va.replace(' ', '')
                v = SnowNLP(va)
                senti = v.sentiments
                print('sentiment value: ' + str(senti))
                if senti > 0.5:
                    print('sentiment label: positive')
                else:
                    print('sentiment label: negative')
                print(va)


if __name__ == '__main__':
    sentiment(docs())