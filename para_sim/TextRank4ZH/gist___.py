#-*- encoding:utf-8 -*-
"""
Created on May 30, 2015
@author: Gavin
"""

import sys
import codecs
from textrank4zh import TextRank4Keyword, TextRank4Sentence
reload(sys)
sys.setdefaultencoding('utf-8')
import jieba
from gensim import corpora, models, similarities

class Gist:

    def __init__(self, stop_words_file='stopword.data'):
            self.stop_words_file=stop_words_file
            self.tr4w = TextRank4Keyword(self.stop_words_file)  # 导入停止词

    def get_keyword(self, text):
            self.tr4w = TextRank4Keyword(self.stop_words_file)  # Import stopwords
            #Use word class filtering，decapitalization of text，window is 2.
            self.tr4w.train(text=text, speech_tag_filter=True, lower=True, window=2)
            # 20 keywords The min length of each word is 1.
            self.wresult = ' '.join(self.tr4w.get_keywords(20, word_min_len=1))
            return self.wresult

    def get_keyphrase(self):
            #Use 20 keywords for contructing phrase, the phrase occurrence in original text is at least 2.
            self.presult = ' '.join(self.tr4w.get_keyphrases(keywords_num=20, min_occur_num= 2))
            self.tr4s = TextRank4Sentence(self.stop_words_file)
            return self.presult

    def get_gist(self, text):
            # self.tr4w = TextRank4Keyword(self.stop_words_file)  # 导入停止词
            #使用词性过滤，文本小写，窗口为2
            self.tr4w.train(text=text, speech_tag_filter=True, lower=True, window=2)
            # 20个关键词且每个的长度最小为1
            self.wresult = ' '.join(self.tr4w.get_keywords(20, word_min_len=1))
            # 20个关键词去构造短语，短语在原文本中出现次数最少为2
            self.presult = ' '.join(self.tr4w.get_keyphrases(keywords_num=20, min_occur_num= 2))
            self.tr4s = TextRank4Sentence(self.stop_words_file)
            # 使用词性过滤，文本小写，使用words_all_filters生成句子之间的相似性
            self.tr4s.train(text=text, speech_tag_filter=True, lower=True, source = 'all_filters')
            self.gresult = ' '.join(self.tr4s.get_key_sentences(num=1)) # 重要性最高的三个句子
            return self.gresult

from pprint import pprint
def cal_sim(textList):

    textList = [list(jieba.cut(text)) for text in textList]
    dictionary = corpora.Dictionary(textList)
    corpus = [dictionary.doc2bow(text) for text in textList]
    corpora.MmCorpus.serialize('gist.mm', corpus)
    corpus = corpora.MmCorpus('gist.mm')
    print corpus
    tfidf = models.TfidfModel(corpus) # step 1 -- initialize a model
    # corpus_tfidf = tfidf[corpus]

    lsi = models.LsiModel(corpus, id2word=dictionary, num_topics=2) # initialize an LSI transformation
    index = similarities.MatrixSimilarity(lsi[corpus]) # transform corpus to LSI space and index it
    sims_list =[]
    for x in range(len(textList)):
        corpus[x] = dictionary.doc2bow(textList[x])
        vec_lsi = lsi[corpus[x]]
        sims = index[vec_lsi]
        sims_list.append(list(enumerate(sims)))
    r = {}
    w = []
    for sl in sims_list:
        for v,k in sl:
            r[v] = k
        w.append(r)
    dl = [dict(t) for t in sims_list]
    # for m in dl:
    #     if min()
    mdl = []


    for x in dl:
        min_v = min(x.itervalues())
        mdlo = {k:v for k,v in x.iteritems() if v == min_v}
        # mdl.append(min_v)
        mdl.append(mdlo)
    smdl = sorted(mdl, key = lambda k:k)
    # fr = sorted(dl)

    print smdl
    print sims_list

if __name__ == "__main__":
    a = Gist().get_gist(codecs.open('/Users/Gavin/work/news_baijia_AI/para_sim/TextRank4ZH/text/01.txt', 'r', 'utf-8').read())
    b = Gist().get_gist(codecs.open('/Users/Gavin/work/news_baijia_AI/para_sim/TextRank4ZH/text/02.txt', 'r', 'utf-8').read())
    c = Gist().get_gist(codecs.open('/Users/Gavin/work/news_baijia_AI/para_sim/TextRank4ZH/text/05.txt', 'r', 'utf-8').read())

    x = '上个周末，吉林农业科技学院经济管理学院赵同学。'
    y = '这小偷还挺有职业道德，只偷钱，又把钱包放回去了。'

    textList = []
    textList.append(x)
    textList.append(y)
    # textList.append(c)
    cal_sim(textList)











