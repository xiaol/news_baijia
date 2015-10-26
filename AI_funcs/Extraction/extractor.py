# -*- coding:utf8 -*-
from __future__ import print_function
__author__ = 'Weiliang Guo'

import sys
reload(sys)
sys.setdefaultencoding('utf8')
from controller.config import dbConn
import re
import jieba.posseg as pseg
import random, string
import json
import jieba
from itertools import combinations
from AI_funcs.snownlp.snownlp import SnowNLP
from AI_funcs.sen_compr.text_handler import SentenceCompressor

def docs():
    dbstore = dbConn.GetDateStore()
    conn = dbstore._connect_news
    # result_doc = conn["news_ver2"]["googleNewsItem"].find({"eventId": {"$exists": 1}, "text": {"$exists":1}}).sort([("createTime", -1)]).limit(10)
    result_doc = conn["news_ver2"]["googleNewsItem"].find({"eventId": {"$exists": 1}, "text": {"$exists":1}, 'createTime':{"$gte": '2015-08-01 06:00:00',"$lt": '2015-08-25 06:00:00'}, "eventId":{'$exists': True}, "duplicate_check":{'$exists': True}}).sort([("createTime", -1)]).skip(10).limit(200)
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


#txt_str is an article text with multiple sentences
def get_quote_text(txt_str=''):
    sentences = re.split(r'\.|。', txt_str)
    signs = ['：“', ':"', ":'", '表示，', '表示,', '表态,', '表态，', '，“', '认为，',
             '认为,', '表明,', '表明，', '表明:', '表明：', '说，', '说,']
    quotes = []

    for sen in sentences:
        for sign in signs:
            if sign in sen:
                if ('：“' in sen or '，“' in sen):
                    sen += '。”'
                    quotes.append(sen)
                else:
                    sen += '。'
                    quotes.append(sen)
                break
    return quotes


def extract_summary(text):
    sn_obj = SnowNLP(text)
    summary = sn_obj.summary(3)
    return summary




#The methods in this class are able to extract sentences with conjunction words from a document.
class ConjExtraction:
    def __init__(self):
        pass

#This method gets a list of sentences by splitting a document.
    def get_split_sentences(self, text=''):
        sentences = re.split(r'\.|。', text)
        return sentences

    #extract and return a list of sentences with causality words
    def extract_causal_sen(self, text=''):
        sens = self.get_split_sentences(text)
        causality_signs = ['原来', '因为', '由于', '以便', '因此', '所以',
                           '是故', '以致', '既然', '既然', ',就', '，就',
                           ', 就', '， 就', '因而', ',那么', ', 那么',
                           '，那么', '， 那么', ',便', ', 便', '，便', '， 便',
                           ',则', ', 则', '，则', '， 则', '导致']
        causality_sentences = []
        for sen in sens:
            for causality_sign in causality_signs:
                if causality_sign in sen:
                    causality_sentences.append(sen)
        return causality_sentences

    #extract and return a list of sentences with assumption words
    def extract_assumption_sentences(self, text):
        sens = self.get_split_sentences(text)
        assumption_signs = [',若', ', 若', '，若''， 若'' 若', '.若', '. 若', '。若', '。 若', '；若', '； 若', ';若', '; 若'
                            '如果', '若是', '假如', '只要', '除非', '假使', '倘若', '即使', '假若', '要是', '譬如']
        assumption_sentences = []
        for sen in sens:
            for assumption_sign in assumption_signs:
                if assumption_sign in sen:
                    assumption_sentences.append(sen)
        return assumption_sentences

    def extract_transition_sentences(self, text):
        sens = self.get_split_sentences(text)
        transition_signs = ['却', '虽然', '但是', '然而', ',而' ', 而' '，而' '， 而', '偏偏', '只是', '不过', '至于', '不料', '岂知']
        transition_sentences = []
        for sen in sens:
            for transition_sign in transition_signs:
                if transition_sign in sen:
                    transition_sentences.append(sen)
        return transition_sentences

    def extract_comparison_sentences(self, text):
        sens = self.get_split_sentences(text)
        comparison_signs = ['像', '好比', '如同', '似乎', '等于', '不如', '不及', '与其 ']
        comparison_sentences = []
        for sen in sens:
            for comparison_sign in comparison_signs:
                if comparison_sign in sen:
                    comparison_sentences.append(sen)
        return comparison_sentences


if __name__ == '__main__':
    doc = '另据“苏越号”打捞总监透露，“为防止，目前完成安装”。'
    get_quote_text(doc)
   # docs = docs()
   # co = ConjExtraction()
   # for key, value in docs.iteritems():
   #     print('@@@@@@@@@@@Event@@@@@@@@@@@@@@@@')
   #     print('Event ID: ' + key)
   #     print('================================')
   #     for ke, va in value.iteritems():
   #         print('~~~~~~~~~~Article~~~~~~~~~~~~~')
   #         print('Article ID: ' + ke)
   #     #     for v in va:
   #     #         v = v.decode('utf8')
   #     #         print('~~~~~~~~~~~~~~~~~~~~~~~')
   #     #         #print sentence


   #         if not va:
   #             print('Oops! Empty article!')
   #         else:
   #             va = va.replace(' ', '')

   #             #.replace("\r","").replace("\n","")
   #             print('ooooooooooooARTICLEoooooooooooooooo')
   #             print(va)
   #             quotes = get_quote_text(va)
   #             if quotes:
   #                 for quo in quotes:
   #                     print('mmmmmmmmmmmmQUOTEmmmmmmmmmmmmmmmmm')
   #                     print(quo)
   #                     cquo = (SentenceCompressor().get_compression_result(quo))["result"]
   #                     print('------------Compressed------------------')
   #                     print(cquo)
   #             else:
   #                 print('No Quote Sentence Found.')

   #             paragraphs = va.split()
   #             for para in paragraphs:
   #                 print('paragraph')
   #                 print(para)

   #             ca_sens = co.extract_causal_sen(va)
   #             as_sens = co.extract_assumption_sentences(va)
   #             ts_sens = co.extract_transition_sentences(va)
   #             cm_sens = co.extract_comparison_sentences(va)
   #             # if ca_sens:
   #             #     for cs in ca_sens:
   #             #         print('--------Causal-Sentence----------')
   #             #         print(cs)
   #             #         print('-----------Compressed------------')
   #             #         ccs = (SentenceCompressor().get_compression_result(cs))["result"]
   #             #         print(ccs)
   #             # else:
   #             #     print('No Causal Sentence Found.')
   #             print('###################################')
   #             if as_sens:
   #                 for ass in as_sens:
   #                     print('--------Assumption-Sentence----------')
   #                     print(ass)
   #                     print('-----------Compressed------------')
   #                     cass = (SentenceCompressor().get_compression_result(ass))["result"]
   #                     print(cass)

   #             else:
   #                 print('No Assumption Sentence Found.')
   #             print('###################################')
   #             if ts_sens:
   #                 for ts in ts_sens:
   #                     print('--------Transition-Sentence----------')
   #                     print(ts)
   #                     print('-----------Compressed------------')
   #                     cts = (SentenceCompressor().get_compression_result(ts))["result"]
   #                     print(cts)

   #             else:
   #                 print('No Transition Sentence Found.')
   #             print('###################################')
   #             if cm_sens:
   #                 for cm in cm_sens:
   #                     print('--------Comparison-Sentence----------')
   #                     print(cm)
   #                     print('-----------Compressed------------')
   #                     ccm = (SentenceCompressor().get_compression_result(cm))["result"]
   #                     print(ccm)
   #             else:
   #                 print('No Comparison Sentence Found.')
