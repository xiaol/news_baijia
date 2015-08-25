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

def randomword(length):
   return ''.join(random.choice(string.lowercase) for i in range(length))

#The typical text for a news topic, usually includes title and main body, etc.
class NewsArticle:
    def __init__(self):
        dbstore = dbConn.GetDateStore()
        conn = dbstore._connect_news
        # result_doc = conn["news_ver2"]["googleNewsItem"].find({"eventId": {"$exists": 1}, "text": {"$exists":1}}).sort([("createTime", -1)]).limit(10)
        result_doc = conn["news_ver2"]["googleNewsItem"].find({"eventId": {"$exists": 1}, "text": {"$exists":1}, 'createTime':{"$gte": '2015-07-26 06:00:00',"$lt": '2015-07-27 06:00:00'}, "eventId":{'$exists': True}, "duplicate_check":{'$exists': True}}).sort([("createTime", -1)]).skip(10).limit(1000)
        self.sens_and_ids = {}
        sorted_docs = {}
        for result_elem in result_doc:

            eventId = result_elem["eventId"]
            article = result_elem["text"]
            article_id = result_elem["sourceUrl"]
            article = article.encode('utf-8')
            setences = re.split(r'\.|。', article)
            if eventId not in sorted_docs.keys():
                sorted_docs[eventId] = {article_id: setences}
            else:
                sorted_docs[eventId][article_id] = setences


        self.sorted_docs = sorted_docs

    def get_article_main_body(self):
        pass

#sorted_docs = {eventId_01:{article_id_01: [sen1, sen2,sen3, ...], article_id_02: article_02}, eventId_02:{...},...}
    def get_article_sentences(self):
        return self.sorted_docs


    def get_data_ready(self):
# One SID coppresonds to nouns of one sentence   i.e. SID_01 = [n1, n2, n3,...]
#sorted_docs = {eventId_01:{article_id_01: [[n1, n2, n3,...], SID_02, SID_03, ...], article_id_02: article_02}, eventId_02:{...},...}
        pass


#News topic features are normally nouns or noun phrases in news article sentences
class Feature:
    def __init__(self):
        self.artcile_sens = NewsArticle().get_article_sentences()
        self.noun = ['i', 'n', 'nh', 'ni', 'ns', 'nz', 'l', 'ng', 'nr', 'nt']
        # pos   part of speech

    def get_pos(self):
        ars = self.artcile_sens
        article_with_pos = {}
        for k, v in ars.iteritems():
            ars_with_pos = {}
            # article_id is the positional number of an article within a set of articles corresponding to one event.
            article_id = 0
            for kk, vv in v.iteritems():
                sens_with_pos = []
                article_id += 1
                #sen_id is the positional number of a sentence within an article.
                sen_id = 0
                for ele in vv:
                    sen_id += 1
                    sen_with_pos = []
                    words = pseg.cut(ele)
                    #tag_id is the pos tag positional number of a word within a sentence.
                    tag_id = 0
                    for w in words:
                        tag_id += 1
                        if w.flag in self.noun:
                            wf = article_id, sen_id, tag_id, w.word, w.flag
                            sen_with_pos.append(wf)
                    sens_with_pos.append(sen_with_pos)
                ars_with_pos[kk] = sens_with_pos
            article_with_pos[k] = ars_with_pos
        return article_with_pos



class FrequentFeature:

    def __init__(self):
        self.get_raw_feature_data = Feature().get_pos()
    #sentences is a list of lists
    def dataFromFile(self, fname):

        for line in fname:
            record = frozenset(line)
            yield record

    def find_freq_feature_candidates(self, data, minSupport=0.15, minConfidence=0.6):
        items, rules = runApriori(data, minSupport, minConfidence)
        return items

    def get_freq_feature_candidates(self):
        xx = Feature().get_pos()
        fe = []
        for key, value in xx.iteritems():
            allall = []

            for hk, x in value.iteritems():
                # print(x)
                for y in x:
                    if y:
                        a = []
                        for ww in y:
                            # print(ww)
                            a.append(ww[3])
                            # print(y[3])
                        a.append(randomword(10).decode('utf8'))
                        allall.append(a)
            # print(allall)
            data = self.dataFromFile(allall)

            fe.append(self.find_freq_feature_candidates(data))
        # print(fe)
        return fe

    def remove_one_word(self):
        men = self.get_freq_feature_candidates()
        without_single_word = []
        for me in men:
            me = [m for m in me if len(m[0]) != 1]
            # print(me)
            ear = []
            for op in me:
                ear.append(op[0])
                # for oo in op:
                #     if oo in
            without_single_word.append(ear)
        # print(without_single_word)
        return without_single_word

    def compactify(self):

        new = NewsArticle()
        opq = new.get_article_sentences()
        # print(opq)
        candidates = self.remove_one_word()
        eids = []
        for uji in opq.keys():
            eids.append(uji)
        candis = {}
        for tyu, eid in zip(candidates, eids):
            candis[eid] = tyu
        for opqk, candisk in zip(opq, candis):
            print(opqk)
            print('@@@@@@@@@@@@@@@@@@@@@@@@')
            print(opq[opqk])
            #wer is a list of all sentences within articles w.r.t. an event.
            wer = []
            for opo, opp in opq[opqk].iteritems():
                for sop in opp:
                    # print(sop)
                    # print('-----------------------')
                    sen = sop.decode('utf8')
                    sen = list(jieba.cut(sen))
                    wer.append(sen)
            print(wer)

            print('********************')
            #cany is a list of valid compact feature phrases
            cany = []
            for can in candis[candisk]:
                print(can)
                #count sentences if they have feature phrase(word distance <= 3) 'can'
                swf = 0
                for we in wer:
                    if set(can).issubset(set(we)):
                        print('yes')
                        ind = []
                        for sw in we:
                            if sw in can:
                                # print(sw)
                                print(we.index(sw))
                                ind.append(we.index(sw))
                        print(ind)
                        combi = combinations(ind, 2)
                        scb = []
                        for cb in combi:
                            # print(cb)
                            #word distance
                            wd = abs(cb[1] - cb[0])
                            scb.append(wd)
                        #     print('sutraction calculation: ' + str(wd))
                        #     if wd <= 3:
                        #         print('word distance ya')
                        #
                        #     else:
                        #         print('word distance nein')
                        # print('wds: ' + str(scb))
                        # check if word distance is less or equal to 3
                        ben = all(i <= 3 for i in scb)

                        if ben:
                            print(ben)
                            swf += 1

                print('swf: ' + str(swf))
                if swf >= 2:
                    cany.append(can)
            print('valid feature phrases: ' + str(cany))

                    # else:
                    #     print('no')


    def removeRedundancy(self):
        pass

class InfrequentFeature:
    pass


class Opinion:
    pass


class OpinionWord:
    pass


class OpinionSentence:
    pass


class OpinionClassifier:
    pass


class Evaluator:
    pass


if __name__ == '__main__':
    # xyz = FrequentFeature()
    # # happy = xyz.remove_one_word()
    # # print(len(happy))
    # xyz.compactify()
    mnq = NewsArticle()
    sss = mnq.get_article_sentences()
    for key, value in sss.iteritems():
        print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
        print('Event ID: ' + key)
        for ke, va in value.iteritems():
            print('*****************************')
            print('Article ID: ' + ke)
            for v in va:
                v = v.decode('utf8')
                print('~~~~~~~~~~~~~~~~~~~~~~~')
                #print sentence
                v = v.replace(' ', '')
                if not v:
                    print('empty sentence')
                else:

                    print(v)
                    v = SnowNLP(v)
                    senti = v.sentiments
                    print('sentiment value: ' + str(senti))
                    if senti > 0.5:
                        print('sentiment label: positive')
                    elif senti == 0.5:
                        print('sentiment label: neutral')
                    else:
                        print('sentiment label: negative')






