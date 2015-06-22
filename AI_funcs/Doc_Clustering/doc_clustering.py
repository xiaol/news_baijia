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





#list_of_dicts ==> [{url-1:text-1},{url-2:text2},{url-3:text-3}...]
def doc_cluster(list_of_dicts=[]):
    corpus = []
    result = []
    for element in list_of_dicts:
        for key, value in element.iteritems():
            seg_list = jieba.cut(value, cut_all=False)
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
    outcome = model.fit_predict(tfidf)
    print outcome
    return


if __name__ == "__main__":
    doc_cluster([{1: '你是什么东西？'}, {2: '他在干什么?'}, {3: '她是个美女。'}, {4: '让我们荡起双桨。'}])