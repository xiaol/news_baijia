# -*- coding: utf-8 -*-
__author__ = 'Gavin'

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
import os
import jieba
import jieba.posseg as pseg
import sys
import string
from sklearn import feature_extraction
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
reload(sys)
sys.setdefaultencoding('utf8')
import math
from sklearn.metrics.pairwise import cosine_similarity
import copy



#list_of_dicts ==> [{'url':'url_str','text':'text_str'}...]
def doc_cluster(list_of_dicts=[]):
    corpus = []
    result = []
    for element in list_of_dicts:
        for key, value in element.iteritems():
            if key == 'content':
                seg_list = jieba.cut(element[key], cut_all=False)
                for seg in seg_list:
                    seg = ''.join(seg.split())
                    if seg != '' and seg != "\n" and seg != "\n\n":
                        result.append(seg)
                corpus.append(' '.join(result))
    vectorizer = CountVectorizer()
    transformer = TfidfTransformer()
    tfidf = transformer.fit_transform(vectorizer.fit_transform(corpus))
    #‘k-means++’ : selects initial cluster centers for k-mean clustering
    # in a smart way to speed up convergence.
    # k is # of initial clusters. Here we use rule of thumb:  k= sqrt(n/2), n is the # of docs.
    n = len(corpus)
    k = int(math.ceil(math.sqrt(n/2)))
    model = KMeans(n_clusters=k, init='k-means++', max_iter=100, n_init=1)
    #convert from numpy array to python list format.
    predict_result = list(model.fit_predict(tfidf))
    print predict_result
    print cosine_similarity(tfidf)

    result = []
    for i in range(n):
        result_dict = {}
        result_dict["url"]=list_of_dicts[i]["url"]
        result_dict["content"]=list_of_dicts[i]["content"]
        result_dict["cluster"]=predict_result[i]
        result.append(result_dict)
    # print result
    return result


def doc_similarity(list_of_dicts=[]):
    corpus = []
    result = []
    for element in list_of_dicts:
        for key, value in element.iteritems():
            if key == 'content':
                seg_list = jieba.cut(element[key], cut_all=False)
                for seg in seg_list:
                    seg = ''.join(seg.split())
                    if seg != '' and seg != "\n" and seg != "\n\n":
                        result.append(seg)
                corpus.append(' '.join(result))
    vectorizer = CountVectorizer()
    transformer = TfidfTransformer()
    tfidf = transformer.fit_transform(vectorizer.fit_transform(corpus))

    n = len(corpus)
    cosine_array=cosine_similarity(tfidf)
    result = []
    for i in range(n):
        result_dict = {}
        result_dict["url"]=list_of_dicts[i]["url"]
        result_dict["content"]=list_of_dicts[i]["content"]
        result_dict["cluster"]=list_of_dicts[i]["cluster"]
        result_dict["similarity"]=cosine_array[0][i]
        result.append(result_dict)
    # print result
    return result





#list_of_dicts ==> [{'url':'url_str', 'cluster': cluster_index, 'sim_val': cos-sim}...]

if __name__ == "__main__":
    doc_cluster([{'url': 'aaa.com', 'text': '有媒体报道成都离职协警向3名女子强行注射不明液体，导致1人身亡。'},
                 {'url': 'bbb.com', 'text': '成都一离职协警强行向女子注射不明液体致其死亡。'},
                 {'url': 'ccc.com', 'text': '限娱令市场供过于求，明星上真人秀的根本原因还是电视节目需要，并非艺人一厢情愿地在找“出口”，而这种需要也让明星的身价顺势水涨船高。'},
                 {'url': 'ddd.com', 'text': '限娱令市场供过于求，明星上真人秀的原因是节目需要更是源自观众窥私欲和虐星心态，正是这些原因让明星身价水涨船高。'}])


