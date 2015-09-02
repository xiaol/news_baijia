#-*- encoding:utf-8 -*-
"""
Created on May 30, 2015
@author: Gavin
"""

import codecs
from TextRank4ZH.textrank4zh import TextRank4Keyword, TextRank4Sentence
import sys

reload(sys)
sys.setdefaultencoding('utf-8')
import jieba
from gensim import corpora, models, similarities
from AI_funcs.sen_compr.text_handler import SentenceCompressor
from AI_funcs.Extraction.extractor import docs
from AI_funcs.Extraction.extractor import ConjExtraction
from AI_funcs.Extraction.extractor import get_quote_text
import os
import pymongo
from pymongo.read_preferences import ReadPreference
import datetime
import urllib
import requests


conn = pymongo.MongoReplicaSetClient("h44:27017, h213:27017, h241:27017", replicaSet="myset",read_preference=ReadPreference.SECONDARY)

docs_find = conn["news_ver2"]["googleNewsItem"].find_one({"sourceUrl": "http://it.people.com.cn/n/2015/0902/c1009-27539987.html"})
# for kk, vv in docs_find.iteritems():
#     print('----------')
#     print(kk)
#     print('~~~~~~~~~~~')
#     print(vv)
# text = "".join(docs_find['description'].split('\n'))
# text = text.replace(" ","")
# params_key = {"article": text.encode('utf-8')}
# data = urllib.urlencode(params_key)
# search_url = "http://121.40.34.56/news/baijia/fetchGist?" + data
# text = requests.post(search_url)
# text = (text.json())
# print text


stopwords = os.path.join(os.path.dirname(__file__), 'TextRank4ZH/stopword.data')
print(stopwords)


class Gist:

    def __init__(self, stop_words_file=stopwords):

            self.stop_words_file=stop_words_file
            self.tr4w = TextRank4Keyword(self.stop_words_file)  # Import stopwords

    def get_keyword(self, text):
            self.tr4w = TextRank4Keyword(self.stop_words_file)  # Import stopwords
            #Use word class filtering，decapitalization of text，window is 2.
            self.tr4w.train(text=text, speech_tag_filter=True, lower=True, window=2)
            # 20 keywords The min length of each word is 1.
            self.wresult = ' '.join(self.tr4w.get_keywords(20, word_min_len=1))
            print self.wresult
            return self.wresult

    def get_keyphrase(self, text):
            self.tr4w = TextRank4Keyword(self.stop_words_file)  # Import stopwords
            #Use word class filtering，decapitalization of text，window is 2.
            self.tr4w.train(text=text, speech_tag_filter=True, lower=True, window=2)
            #Use 20 keywords for contructing phrase, the phrase occurrence in original text is at least 2.
            self.presult = ' '.join(self.tr4w.get_keyphrases(keywords_num=20, min_occur_num= 2))
            print self.presult
            return self.presult

    def get_gist(self, article=''):
        gresult = ''
        article = article.replace(' ', '')
        quotes = get_quote_text(article)
        if quotes:
            sims = cal_sim(article, quotes)
            for a, s in zip(quotes, sims):
                if s == max(sims):
                    gresult = a
        else:
            tr4s = TextRank4Sentence(self.stop_words_file)
            # Use part-of-speech filtering, use words_all_filters to genearte similarity between sentences.
            tr4s.train(text=article, speech_tag_filter=True, lower=True, source='all_filters')
            gresult = ' '.join(tr4s.get_key_sentences(num=1))

        return gresult


#query is a string, textList is a list of strings.
#If a query only compares itself against itself or only one another document, the result is always 1.
def cal_sim(query, text_list):

    text_list = [list(jieba.cut(text)) for text in text_list]

    dictionary = corpora.Dictionary(text_list)
    corpus = [dictionary.doc2bow(text) for text in text_list]
    lsi = models.LsiModel(corpus, id2word=dictionary, num_topics=2) # initialize an LSI transformation
    query_bow = dictionary.doc2bow(list(jieba.cut(query)))

    query_lsi = lsi[query_bow]
    index = similarities.MatrixSimilarity(lsi[corpus]) # transform corpus to LSI space and index it
    sims = index[query_lsi]
    return sims


if __name__ == "__main__":
    doc = """中新网9月2日电 互联网公司奇虎360正式公布2015年第二季度未经审计的财务数据。二季度的净利润同比增长一倍多；PC端和无线端的产品和服务继续保持增长势头，主要产品持续保持领先优势；四大新领域强势推进、进展顺利，智能硬件、手机、搜索和无线业务商业化、企业安全表现抢眼。\n图1：奇虎360公司总部\n二季度收入达到4.38亿美元，比去年同期的3.18亿美元增长37.9%。二季度净利润为8135万美元，去年同期为3912万美元，同比增长108.0%。非美国会计准则下，二季度净利润约为1.17亿美元，去年同期为6925万美元，同比增长69.0%。\n图2：360公司主要的安全类软件产品\n主要产品持续增长势头\n2015年6月，公司PC端产品和服务的月活跃用户数到达5.14亿，去年同期该数据为4.96亿。PC端的产品和服务在2015年6月的市场渗透率为96.6%，去年同期的市场渗透率为93.9%。\n在移动端，使用360手机卫士的智能手机用户总数在2015年6月达约7.99亿，2014年6月为6.41亿，同比增长24.6%。\n图3：奇虎360公司2011年在美国上市\n公司总裁齐向东表示：“企业安全业务发展也很顺利，不断获得新的大客户。”\n智能硬件是未来万物互联时代的主要入口，公司董事长兼CEO周鸿?t就认为：“智能硬件和万物互联的设备将是紧密链接广大移动终端用户的重要契机。”\n在智能硬件领域，360早就发力，如360随身wifi等智能硬件早在2013年就已开始销售，都取得不俗甚至是令业界惊叹的战绩。进入今年二季度，360更是发布了行车记录仪和儿童卫士智能手表第三代等智能硬件，受到市场热烈追捧，产品供不应求。\n如果说智能硬件是万物互联时代的主要入口，那么智能手机则是最重要入口之一。上周，360旗下奇酷手机发布了三款智能手机，新手机无论设计还是工艺都十分优秀，其创新功能得到业内一致好评，也获得市场强烈认可，开启预约后，预约火爆。\n周鸿?t表示：“奇酷手机拥有的安全的硬件，加上内置的安全功能将360的安全服务再次从线上拓展到线下，从虚拟拓展到现实感受中。360认为手机和智能硬件将是公司长期移动发展战略中的重要组成部分。”\n"""
    docs = docs()
    gist_obj = Gist()
    gist = gist_obj.get_gist(doc)
    print(gist)
    """
    num_articles = 0
    for key, value in docs.iteritems():
        print('@@@@@@@@@@@Event@@@@@@@@@@@@@@@@')
        print('Event ID: ' + key)
        print('================================')
        for ke, va in value.iteritems():
            print('~~~~~~~~~~Article~~~~~~~~~~~~~')
            print('Article ID: ' + ke)

            if not va:
                print('Oops! Empty article!')
            else:
                num_articles += 1
                va = va.replace(' ', '')

                #.replace("\r","").replace("\n","")
                print('ooooooooooooARTICLEoooooooooooooooo')
                print(va)
                print('Gist')
                gist = gist_obj.get_gist(va)
                print(gist)
    print('Number of articles: ' + str(num_articles))
"""

