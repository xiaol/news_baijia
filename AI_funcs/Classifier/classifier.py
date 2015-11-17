# -*- coding: utf-8 -*-
"""
Created on Jun, 08, 2015
@author: Gavin
"""

#  http://textgrocery.readthedocs.org/zh/latest/quick-start.html
from tgrocery import Grocery
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
from math import sqrt
import gensim
from sklearn.svm import SVC
import os
import jieba
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import math
import numpy as np
from AI_funcs.Extraction.db_handler import Mongodb
import time
import uniout


class TextClassifier:
    def __init__(self):
        self.classifier = Grocery('classifier')

    #train_src is a list of sets which are 'channel: text' pairs
    def classify(self, train_src=[], test_src=''):
        c_trained = self.classifier.train(train_src)
        c_trained.load()
        label_predicted = c_trained.predict(test_src)
        return label_predicted


def vec2dense(vec, num_terms):

    '''Convert from sparse gensim format to dense list of numbers'''
    return list(gensim.matutils.corpus2dense([vec], num_terms=num_terms).T[0])

#training_data can be a a dictionary of different paragraphs,data_to_classify can be a
# a dictionary of different commnents to be classified to those paragraphs.
def doc_classify(training_data, data_to_classify):
    if len(training_data) == 1 or not training_data:
        message = "The number of classes has to be greater than one; got 1 or 0."
        print message
        return
    #Load in corpus, remove newlines, make strings lower-case
    docs = {}
    docs.update(training_data)
    docs.update(data_to_classify)
    names = docs.keys()
    print(names)
    preprocessed_docs = {}
    for name in names:
        preprocessed_docs[name] = list(jieba.cut(docs[name]))

    #Build the dictionary and filter out rare terms
    #Perform Chinese words segmentation.
    dct = gensim.corpora.Dictionary(preprocessed_docs.values())
    unfiltered = dct.token2id.keys()
    dct.filter_extremes(no_below=2)
    filtered = dct.token2id.keys()
    filtered_out = set(unfiltered) - set(filtered)
    """
    print "\nThe following super common/rare words were filtered out..."
    print list(filtered_out), '\n'

    print "Vocabulary after filtering..."
    print dct.token2id.keys(), '\n'

    #Build Bag of Words Vectors out of preprocessed corpus
    print "---Bag of Words Corpus---"
    """
    bow_docs = {}
    for name in names:

        sparse = dct.doc2bow(preprocessed_docs[name])
        bow_docs[name] = sparse
        dense = vec2dense(sparse, num_terms=len(dct))
        #print name, ":", dense

    #Dimensionality reduction using LSI. Go from 6D to 2D.
    """
    print "\n---LSI Model---"
    """

    lsi_docs = {}
    num_topics = 2
    lsi_model = gensim.models.LsiModel(bow_docs.values(),
                                       num_topics=num_topics)
    for name in names:
        vec = bow_docs[name]
        sparse = lsi_model[vec]
        dense = vec2dense(sparse, num_topics)
        lsi_docs[name] = sparse
        #print name, ':', dense

    #Normalize LSI vectors by setting each vector to unit length
    """"
    print "\n---Unit Vectorization---"
    """
    unit_vecs = {}

    for name in names:

        vec = vec2dense(lsi_docs[name], num_topics)

        #print vec
        norm = sqrt(sum(num ** 2 for num in vec))
        with np.errstate(invalid='ignore'):
            unit_vec = [num / norm for num in vec]
        if math.isnan(unit_vec[0]) | math.isnan(unit_vec[1]):
            unit_vec = [0.0,0.0]

        unit_vecs[name] = unit_vec
       # print name, ':', unit_vec
    #Take cosine distances between docs and show best matches
    #print "\n---Document Similarities---"

    index = gensim.similarities.MatrixSimilarity(lsi_docs.values())
    for i, name in enumerate(names):

        vec = lsi_docs[name]
        sims = index[vec]
        sims = sorted(enumerate(sims), key=lambda item: -item[1])

        #Similarities are a list of tuples of the form (doc #, score)
        #In order to extract the doc # we take first value in the tuple
        #Doc # is stored in tuple as numpy format, must cast to int

        if int(sims[0][0]) != i:
            match = int(sims[0][0])
        else:
            match = int(sims[1][0])

        match = names[match]
       # print name, "is most similar to...", match

    print "\n---Classification---"

    train = [unit_vecs[key] for key in training_data.keys()]

    labels = [(num+1) for num in range(len(training_data.keys()))]
    label_to_name = dict(zip(labels, training_data.keys()))
    classifier = SVC()
    classifier.fit(train, labels)
    result = {}
    for name in names:

        vec = unit_vecs[name]
        label = classifier.predict([vec])[0]
        cls = label_to_name[label]
        if name in data_to_classify.keys():
            result[name]= cls
    print result
    # print r'\xe5\xbe\xae\xe8\xbd\xaf' + " is " + '\xe5\xbe\xae\xe8\xbd\xaf'
    # print r'\xe8\xb0\xb7\xe6\xad\x8c' + " is " + '\xe8\xb0\xb7\xe6\xad\x8c'
    return result
    print '\n'




if __name__ == '__main__':

    a = {"M": "公司于1975年由比尔·盖茨和保罗·艾伦创立。初期主要为阿尔塔8800发展和销售BASIC解释器，在1980年代中期凭借MS-DOS在家用电脑操作系统市场上获取长足进步，后来出现的Windows使得微软逐渐统治了家用桌面电脑操作系统市场。同时微软也开始扩张业务，进军其他行业和市场：创建MSN门户网站；计算机硬件市场上，微软商标及Xbox、Xbox 360、Surface、Zune和MSN TV家庭娱乐设备也在不同的年份出现在市场上[3]。微软于1986年首次公开募股，此后不断走高的股价为微软缔造了四位亿万富翁和12,000位百万富翁[5][6][7]。",
         "G": "是一家美国的跨国科技企业，业务范围涵盖互联网搜索、云计算、广告技术等领域，开发并提供大量基于互联网的产品与服务，[8]其主要利润来自于AdWords等广告服务。[9][10] Google由当时在斯坦福大学攻读理工博士的拉里·佩奇和谢尔盖·布林共同创建，因此两人也被称为“Google Guys”。[11][12][13]1998年9月4日，Google以私营公司的形式创立，设计并管理一个互联网搜索引擎“Google搜索”；Google网站则于1999年下半年启用。2004年8月19日，Google公司的股票在纳斯达克上市，后来被称为“三驾马车”的公司两位共同创始人与出任首席执行官的埃里克·施密特在当时承诺：共同在Google工作至少二十年，即至2024年止。[14]创始之初，Google官方的公司使命为“集成全球范围的信息，使人人皆可访问并从中受益”（To organize the world's information and make it universally accessible and useful）；[15]而非正式的口号则为“不作恶”（Don't be evil），由工程师阿米特·帕特尔（Amit Patel）所创，[16]并得到了保罗·布赫海特的支持。[17][18] Google公司的总部称为“Googleplex”，位于美国加州圣克拉拉县的芒廷维尤。2011年4月，佩奇接替施密特担任首席执行官[19]。"

    }
    b = {"微软": "微软公司于1975年由比尔·盖茨和保罗·艾伦创立。他们是小时候认识的朋友及高中同学，并对在计算机编程充满激情。利用其演讲技能，追求一个成功的企业。在1975年01月发布MITS公司的牛郎星8800大众化微电脑和遥测系统令他们注意到，他们可以编写一个BASIC解释器赚钱，他致电给Altair 8800的发明者（MITS），提出示范在该系统中运行BASIC。[10]完成后，MITS公司感到兴趣，更要求艾伦和盖茨进行示范。之后MITS公司聘请艾伦为“牛郎星”进行模拟器（解释器中的组件）的开发工作，而盖茨则开发解释器。它们的工作十分完美，在1975年3月MITS公司同意贩买出售牛郎星BASIC解释器[11]。然后他们顺利赚了第一桶金。于是，盖茨离开哈佛大学，并搬到MITS在新墨西哥州阿布奎基的总部。1975年04月04日，微软正式成立，盖茨为微软首席运行官。原名“Micro-Soft”是艾伦想出来的，之后更改为“Microsoft”[12]。在1995年《财富》杂志的一篇文章中回忆，在1977年08月，公司和日本ASCII杂志签署了一个协议，成立了其首个国际办事处“ASCII Microsoft”[13]。在1979年01月，公司搬迁到在华盛顿州的比尔维尤的新办公室。微软在1981年06月25日于华盛顿州改组成注册公司（“Microsoft,Inc.”）。盖茨于改组中成为公司的总裁和董事长，保罗·艾伦则成为运行副总裁。",
         "Microsoft": "微软公司于1975年由比尔·盖茨和保罗·艾伦创立。他们是小时候认识的朋友及高中同学，并对在计算机编程充满激情。利用其演讲技能，追求一个成功的企业。在1975年01月发布MITS公司的牛郎星8800大众化微电脑和遥测系统令他们注意到，他们可以编写一个BASIC解释器赚钱，他致电给Altair 8800的发明者（MITS），提出示范在该系统中运行BASIC。[10]完成后，MITS公司感到兴趣，更要求艾伦和盖茨进行示范。之后MITS公司聘请艾伦为“牛郎星”进行模拟器（解释器中的组件）的开发工作，而盖茨则开发解释器。它们的工作十分完美，在1975年3月MITS公司同意贩买出售牛郎星BASIC解释器[11]。然后他们顺利赚了第一桶金。于是，盖茨离开哈佛大学，并搬到MITS在新墨西哥州阿布奎基的总部。1975年04月04日，微软正式成立，盖茨为微软首席运行官。原名“Micro-Soft”是艾伦想出来的，之后更改为“Microsoft”[12]。在1995年《财富》杂志的一篇文章中回忆，在1977年08月，公司和日本ASCII杂志签署了一个协议，成立了其首个国际办事处“ASCII Microsoft”[13]。在1979年01月，公司搬迁到在华盛顿州的比尔维尤的新办公室。微软在1981年06月25日于华盛顿州改组成注册公司（“Microsoft,Inc.”）。盖茨于改组中成为公司的总裁和董事长，保罗·艾伦则成为运行副总裁。",
         "谷歌": "据估计，Google在全世界的数据中心内运营着超过百万台的服务器，[20]每天处理数以亿计的搜索请求[21]和约二十四PB用户生成的数据。[22][23][24][25] Google自创立起开始的快速成长同时也带动了一系列的产品研发、并购事项与合作关系，而不仅仅是公司核心的网络搜索业务。Google公司提供丰富的线上软件服务，如云硬盘、Gmail电子邮件，包括Orkut、Google Buzz以及Google+在内的社交网络服务。Google的产品同时也以应用软件的形式进入用户桌面，例如Google Chrome网页浏览器、Picasa图片整理与编辑软件、Google Talk即时通讯工具等。另外，Google还进行了移动设备的Android操作系统以及上网本的Google Chrome OS操作系统的开发。",
         "Google":"1996年1月，身为加州斯坦福大学理学博士生的拉里·佩奇和谢尔盖·布林在学校开始一项关于搜索的研究项目。[30]区别于传统的搜索靠搜索字眼在页面中出现次数来进行结果排序的方法，两人开发了一个对网站之间的关系做精确分析的搜寻引擎。[31]这个名为PageRank的引擎通过检查网页中的反向链接以评估站点的重要性，此引擎的精确度胜于当时的基本搜索技术。[32][33]最初，佩奇和布林将这个搜索引擎命名为‘BackRub’，直到后来改为‘Google’。[34][35][36]这个新名字来源于一个数学大数googol（数字1后有100个0，即自然数10100）单词错误的拼写方式，[37][38]象征着为人们提供搜索海量优质信息的决心。[39] Google搜索引擎在斯坦福大学的网站上启用，域名为google.stanford.edu。[40]"
    }

    def get_time_hms(seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        result = str(h) + 'h' + str(m) + 'm' + str(s) + 's'
        return result

    start_time_point = time.time()

    mg = Mongodb()
    mg.retrieve_channel_items()
    print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
    docs = mg.retrieve_news_items()
    end_time_point_DB = get_time_hms(time.time() - start_time_point)
    print('time used for retrieving data from DB:' + end_time_point_DB)

    start_time_point_data_set_prep = time.time()
    docs_to_train = docs[:2800]
    docs_to_predict = docs[2801:]
    end_time_point_data_set_prep = get_time_hms(time.time() - start_time_point_data_set_prep)
    print('time used for seperating data set for training, predicting and testing: ' + end_time_point_data_set_prep)

    start_time_point_data_classifier_train = time.time()
    classifier = Grocery('sample')
    classifier.train(docs_to_train)
    classifier.save()
    c = Grocery('sample')
    c.load()
    end_time_point_data_classifier_train = get_time_hms(time.time() - start_time_point_data_classifier_train)
    print('time used for classifier training: ' + end_time_point_data_classifier_train)

    start_time_point_data_classifier_predict = time.time()
    correct_prediction_num = 0
    for doc in docs_to_predict:
        txt = doc[1]
        # print('--------------------')
        # print('Correct label: ' + doc[0])
        l = c.predict(txt)
        # print('Predicted label: ' + l)
        if l == doc[0]:
            correct_prediction_num += 1
    end_time_point_data_classifier_predict = get_time_hms(time.time() - start_time_point_data_classifier_predict)
    print('time used for predicting: ' + end_time_point_data_classifier_predict)
    print('# of trained docs:               ' + str(len(docs_to_train)))
    print('# of docs to predict:            ' + str(len(docs_to_predict)))
    print('# of correctly predicted docs:   ' + str(correct_prediction_num))


