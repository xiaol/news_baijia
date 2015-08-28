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

pwd = os.getcwd()
# print(pwd)
# pwd = pwd.split('/')
# pwd = pwd[:-1]
# abs_path = '/'.join(pwd)
print(pwd)

stopwords = pwd + '/AI_funcs/Gist_and_Sim/TextRank4ZH/stopword.data'


class Gist:

    def __init__(self, stop_words_file='TextRank4ZH/stopword.data'):
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
        """
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
        """

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
    doc = """财政部部长楼继伟6月28日在向十二届全国人大常委会第十五次会议作2014年中央决算报告时称：“要配合做好房地产税立法工作。”随后，有专家就透露，房地产税立法初稿已基本成型，现阶段应在全国人大、财政部内部征求意见，进行完善。
但据《华夏时报》记者多方了解，房地产税改革这项工作今年一直在进行，只是至今改革的路径还不明晰。最新的说法是，房地产税是把现有的房产税和城镇土地使用税合并起来，也就是增加房地产保有环节的税负，而且是以房地产的评估值为征税基础，其他诸如土地增值税、契税等暂不纳入。
“市场所传‘房地产税立法初稿’，既非官方文件所发，又无官方代表所讲，基本可以判断不靠谱。”7月23日，住建部政策咨询专家、亚太城市房地产研究院院长谢逸枫接受《华夏时报》记者采访时直言。记者当天两次致电国家税务总局财产行为税司的综合处、业务处两个处室，均未获得房地产税初稿成型的确切消息，而财政部则未予回应。
“还不好说，这项工作一直在开展，我们最多也只是配合。”国家税务总局财产行为税司业务处一位工作人员面对记者的求证时说。多位受访专家均表示，房地产税立法初稿已基本成型的消息还不靠谱。
之所以不靠谱，谢逸枫有四点理由：一是房地产税立法初稿的形成，一般是由国税局、财政部、人大法工委汇合相关专家组成一个小组，如未形成统一意见，基本是不会公布的；二是房地产税的立法初稿意见是内部意见，肯定不会外透；三是初稿意见形成统一后，才会通过国务院发布公开咨询意见；四是最后才由全国人大或人大常委会决定是否通过立法案，并由国税局、财政部统一实施。
据谢逸枫分析，作为国家财税制度的一项改革，目前并未实质性全面开展立法工作，仅仅是房地产税的理论研究与立法意见的内部讨论而已，“房地产税立法没有提交到立法规划层面，人大法工委、国税局和财政部都不会发布有关房地产税的消息”。
据悉，房产税改革从2011年1月底正式启动，其标志就是上海、重庆开始房产税改革试点。随后，在国务院发布的《关于深化收入分配制度改革若干意见的通知》、《关于2013年深化经济体制改革重点工作意见的通知》等指导性文件均提出要“扩大个人住房房产税改革试点范围”。
今年全国两会期间，楼继伟再次表示，今年将配合做好房地产税立法工作，加快房地产税立法并适时推进改革。
“房地产税是一个复杂的立法过程。”7月23日，中原地产首席分析师张大伟接受《华夏时报》记者采访时说。事实上，房地产税的立法推进工作非常谨慎，“研究与意见工作主要是国务院研究机构与国税局、财政部的专家参加。”谢逸枫说。
谢逸枫的说法与今年早些时候财政部副部长朱光耀的观点吻合。朱光耀当时表示，目前由全国人大牵头、财政部配合的房地产税立法工作正在研究过程中，还没有立法的具体时间表，但他表示全国人大会有一个科学的安排，“怎么开征房地产税，总的说来由人大牵头，财政部配合”。"""
    gist_obj = Gist()
    gist = gist_obj.get_gist(doc)
    print(gist)

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












