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


class Gist:

    def __init__(self, stop_words_file='TextRank4ZH/stopword.data'):
            self.stop_words_file=stop_words_file
            self.tr4w = TextRank4Keyword(self.stop_words_file)  # 导入停止词

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

    def get_gist(self, text_dict={}):
        gresult = {}
        for key, value in text_dict.iteritems():
            value = value.replace(' ', '')
            quotes = get_quote_text(value)
            if quotes:
                sims = cal_sim(value, quotes)
                for a, s in zip(quotes, sims):
                    if s == max(sims):
                        gresult[key] = a
            else:
                # print('No Quote Sentence Found. Use TextRank algorithm to get gist.')
                tr4s = TextRank4Sentence(self.stop_words_file)
                # 使用词性过滤，文本小写，使用words_all_filters生成句子之间的相似性
                tr4s.train(text=value, speech_tag_filter=True, lower=True, source = 'all_filters')
                gresult.update({key: (' '.join(tr4s.get_key_sentences(num=1)))})

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
    docs = docs()
    co = ConjExtraction()
    gist = Gist()
    for key, value in docs.iteritems():
        print('@@@@@@@@@@@Event@@@@@@@@@@@@@@@@')
        print('Event ID: ' + key)
        print('================================')
        gis = gist.get_gist(value)
        for kk, vv in gis.iteritems():
            print('~~~~~~~~~~Article~~~~~~~~~~~~~')
            print(value[kk])
            print('          Gist                 ')
            print(vv)
        """
        for ke, va in value.iteritems():
            print('~~~~~~~~~~Article~~~~~~~~~~~~~')
            print('Article ID: ' + ke)
        #     for v in va:
        #         v = v.decode('utf8')
        #         print('~~~~~~~~~~~~~~~~~~~~~~~')
        #         #print sentence


            if not va:
                print('Oops! Empty article!')
            else:
                va = va.replace(' ', '')

                #.replace("\r","").replace("\n","")
                print('ooooooooooooARTICLEoooooooooooooooo')
                print(va)
                quotes = get_quote_text(va)
                if quotes:
                    q_g = gist.get_new_gist(va, quotes)
                    print('-----------Gist---------------')
                    print(q_g)
                    for quo in quotes:
                        print('mmmmmmmmmmmmQUOTEmmmmmmmmmmmmmmmmm')
                        print(quo)
                        cquo = (SentenceCompressor().get_compression_result(quo))["result"]
                        print('------------Compressed------------------')
                        print(cquo)
                else:
                    print('No Quote Sentence Found.')

                paragraphs = va.split()
                for para in paragraphs:
                    print('paragraph')
                    print(para)
                    """

"""
                ca_sens = co.extract_causal_sen(va)
                as_sens = co.extract_assumption_sentences(va)
                ts_sens = co.extract_transition_sentences(va)
                cm_sens = co.extract_comparison_sentences(va)
                # if ca_sens:
                #     for cs in ca_sens:
                #         print('--------Causal-Sentence----------')
                #         print(cs)
                #         print('-----------Compressed------------')
                #         ccs = (SentenceCompressor().get_compression_result(cs))["result"]
                #         print(ccs)
                # else:
                #     print('No Causal Sentence Found.')
                print('###################################')
                if as_sens:
                    for ass in as_sens:
                        print('--------Assumption-Sentence----------')
                        print(ass)
                        print('-----------Compressed------------')
                        cass = (SentenceCompressor().get_compression_result(ass))["result"]
                        print(cass)

                else:
                    print('No Assumption Sentence Found.')
                print('###################################')
                if ts_sens:
                    for ts in ts_sens:
                        print('--------Transition-Sentence----------')
                        print(ts)
                        print('-----------Compressed------------')
                        cts = (SentenceCompressor().get_compression_result(ts))["result"]
                        print(cts)

                else:
                    print('No Transition Sentence Found.')
                print('###################################')
                if cm_sens:
                    for cm in cm_sens:
                        print('--------Comparison-Sentence----------')
                        print(cm)
                        print('-----------Compressed------------')
                        ccm = (SentenceCompressor().get_compression_result(cm))["result"]
                        print(ccm)
                else:
                    print('No Comparison Sentence Found.')
                    """












