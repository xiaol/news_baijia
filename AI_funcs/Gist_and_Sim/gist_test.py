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
    doc = """第二名嫌疑人落网 泰移民官涉嫌受贿\n女嫌疑人联系警方\n警方发言人巴武・塔翁西里说，那名女性名为婉娜・“米沙罗”・逊讪，现年26岁，已经逃离泰国。塔翁西里没有说明婉娜眼下身在哪个国家。\n法新社记者1日下午设法联系上婉娜，电话那头自称婉娜的女子说，她现与丈夫居住在土耳其开塞利市。这名女子没有透露丈夫的国籍。那是一个土耳其手机号码。泰国警察总监颂育・蓬汶孟说，婉娜已经联系警方，将与警方会面。\n婉娜的家人认定婉娜无辜，称婉娜先前嫁给一名土耳其男子，两三个月前与丈夫和孩子一起前往土耳其工作，现居住在土耳其。\n泰国法院1日签发对婉娜和一名不明身份男子的逮捕令。那名男子与婉娜同住曼谷明武里地区一处公寓，警方先前在公寓房内发现制造炸弹的材料，随即通缉两人。\n婉娜在电话中告诉法新社记者，她与爆炸案无关，那处公寓早已被租给她丈夫的一个朋友，她已经有一年没去过那儿了。\n另外，巴武说，警方1日向法院申请对另外3名男性嫌疑人的逮捕令，其中两人是土耳其人，另一人国籍不明。他们先前住在发现制造炸弹材料的公寓的同一栋居民楼内。也就是说，爆炸案嫌疑人增加至7人。\n“重要成员”落网\n泰国警方1日中午在东部边境的沙缴府抓获另一名嫌疑人，他当时试图经由一片森林入境柬埔寨，被捕后即被转移至曼谷接受讯问。巴武说，警方在调查中得知那名男子打算出逃，随后追踪到沙缴府边境。那名男子说英语，长相与先前通缉的“黄衣男子”相像，据信是爆炸案幕后团伙的一名“重要成员”。\n电视画面显示，落网男子身材瘦削，戴着眼镜，留着短胡须，头戴棒球帽。\n就那名男子是否是主要嫌疑人，泰国总理巴育・占奥差说：“我们正在进行调查。他是外籍人士、一名主要嫌疑人。”\n男子落网后，一张据称是那名男子护照的照片在社交网站流传，标出男子的国籍。不过，巴武说，泰国政府没有发布类似照片，不清楚那张照片来自何处。\n警方说，他们先前从一辆“摩的”和一辆三轮出租车上收集了爆炸案案犯的脱氧核糖核酸(DNA)样本，将同新抓获嫌疑人的脱氧核糖核酸样本进行比对，以确认是否是他实施爆炸。\n移民官员被调离\n泰国《泰叻报》1日报道，沙缴府一处边防检查站的6名移民官员已经被调离原岗位，包括一名高级官员，原因是他们据信收受贿赂，放曼谷爆炸案一名外籍嫌疑人入境。\n警察总监颂育证实他将那几名官员调往曼谷一些“闲岗”，但没有说明他们移职的原因。他说，暂时没有证据显示移民官员的行为牵涉爆炸案，如果证实他们有任何牵连，将受到严惩。\n"""
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

