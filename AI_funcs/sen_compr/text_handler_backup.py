
# -*- coding:utf8 -*-
from __future__ import print_function
__author__ = 'Gavin'

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from controller.config import dbConn
import requests
import re


class SentenceCompressor:
    def __init__(self, raw_sentence="", api_url="http://60.28.29.37:8080/SentenceCompressor?sentence="):
        self.api_url = api_url
        self.raw_sentence = raw_sentence

    # If you want to match a certain part of a string using a regex,
    # just add a new regex-string condition pair into this method body.
    @staticmethod
    def normalize_orders(matchobj):
        if matchobj.group() == "%":
            return "百分号"
        elif matchobj.group() == '\[':
            return '('
        elif matchobj.group() == ']':
            return ')'
        elif matchobj.group() == "-":
            # return "_"
            return "_"
        elif matchobj.group() == '·':
            return '_'
        # elif matchobj.group() == " ":
        #     return ","
        elif matchobj.group() == r"[,|，].*称[,|，]|“|”| |‘|’|《|》":
            return ""

    #Collect all the regular expressions to be used.  | stands for bitwise OR.
    def regex_collect(self):
        rg = r"[,|，].*称[,|，]|“|”| |‘|’|《|》|%|\[|]|-|·"
        return rg

    # text is the string to be pre-processed, regex is the regular expression(s).
    def text_preprocess(self):
        regex = self.regex_collect()
        text = self.raw_sentence
        pre_processed_txt = re.sub(regex, SentenceCompressor.normalize_orders(), text)
        return pre_processed_txt

    #Get last text segment of a sentence as last comma encountered
    def get_last_sen_seg(self, sen=''):
        # last_sen_seg = sen.split('，')[-1]
        last_sen_seg = re.split(",|，", sen)[-1]
        return last_sen_seg

    def get_compression_result(self):
        refined_text = self.text_preprocess()
        sentence_ready_to_compress = get_last_sen_seg(refined_text)
        if len(refined_text) <= 12:
            return refined_text
        compr_result = requests.get(self.api_url + sentence_ready_to_compress)
        return compr_result



def get_html_content(s=''):
    s = re.sub("<.*?>", "", s)
    if len(s) <= 12:
        return s
    url_link= 'http://localhost:8080/sentcompr/'
    sentence_seg = text_preprocess(s)
    result = requests.get(url_link+sentence_seg)
    result = result.text
    #Remove all HTML tags.
    result = re.sub("<.*?>", "", result)
    print(result)
    return result


# If you want to match a certain part of a string using a regex,
# just add a new regex-string condition pair into this method body.
def normalize_orders(matchobj):
    if matchobj.group() == "%":
        return "百分号"
    elif matchobj.group() == '\[':
        return '('
    elif matchobj.group() == ']':
        return ')'
    elif matchobj.group() == "-":
        # return "_"
        return "_"
    elif matchobj.group() == '·':
        return '_'
    # elif matchobj.group() == " ":
    #     return ","
    elif matchobj.group() == r"[,|，].*称[,|，]|“|”| |‘|’|《|》":
        return ""

#Collect all the regular expressions to be used.  | stands for bitwise OR.
def regex_collect():
    rg = r"[,|，].*称[,|，]|“|”| |‘|’|《|》|%|\[|]|-|·"
    return rg

# text is the string to be pre-processed, regex is the regular expression(s).
def text_preprocess(text, regex=regex_collect()):
    pre_processed_txt = re.sub(regex, normalize_orders, text)
    return pre_processed_txt


def find_gists_of_google_news():
    dbstore = dbConn.GetDateStore()
    conn = dbstore._connect_news
    result_doc = conn["news_ver2"]["googleNewsItem"].find({"isOnline":1}).skip(200).limit(100)

    gists = []
    urls = []
    ggs = []
    titles = []
    articles = []
    for result_doc_elem in result_doc:

        gist_raw = result_doc_elem["abstract"]
        title = result_doc_elem["title"]
        article = result_doc_elem["content"]
        article = article.encode('utf-8')
        gist = gist_raw.encode('utf-8')
        gg = text_preprocess(gist)
        gists.append(gist)
        ggs.append(gg)
        titles.append(title)
        url =result_doc_elem["sourceUrl"]
        urls.append(url)
        articles.append(article)
    return zip(titles, gists, ggs, urls, articles)


def get_longest_sen_seg(sen=''):
    sen_seg_list = sen.split('，')
    sen_seg_len_list = [len(s) for s in sen_seg_list]
    max_len_sen_seg = max(sen_seg_len_list)
    for sen_seg in sen_seg_list:
        if len(sen_seg) == max_len_sen_seg:
            # sen_seg = re.sub("[《|》]", "", sen_seg)
            return sen_seg

#Get last text segment of a sentence as last comma encountered
def get_last_sen_seg(sen=''):
    # last_sen_seg = sen.split('，')[-1]
    last_sen_seg = re.split(",|，", sen)[-1]
    return last_sen_seg


def get_quote_text(txt_str=''):
    # pattern = re.compile(ur'[说|道|云|称|讲|曰]+[,|:|\'|"| |：|“|，|:"|:\'|：“]+(.*?)["|\'|”][.|。|!|！|”。|".]+')
    # qtxt = pattern.findall(txt_str)
    #
    #
    # for txt in qtxt:
    #     print(txt)

    sentences = re.split(r'\.|。', txt_str)
    signs = ['：“', ':"', ":'", '表示，', '表示,', '表态,', '表态，', '，“', '认为，',
             '认为,', '表明,', '表明，', '表明:', '表明：', '说，', '说,']
    quotes = []

    for sen in sentences:
        for sign in signs:
            if sign in sen:
                quotes.append(sen)
                print(sen)
                print('oooooooooooooooooooooooooooooooooooooooooooooooooo')
    return quotes


if __name__ == '__main__':
    a_sample_sentence_to_compress = '凌德权认为,通过中越双方对阮富仲访华的一系列精心安排可以看出,两国领导人都十分珍视中越传统友谊,并有强烈的共同意愿,推动两国全面战略合作伙伴关系长期稳定健康发展'
    sencom = SentenceCompressor(raw_sentence=a_sample_sentence_to_compress)
    sencom = sencom.get_compression_result()

    print(type(sencom))




    xx = find_gists_of_google_news()
    for title, gst, gg, u , aticle in xx:
        print(aticle)
        print("\n")
        print("\n")
        # get_quote_text(aticle)
        print("                ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
        gloss = get_longest_sen_seg(gst)
        glass = get_last_sen_seg(gst)
        print("\n")
        print("\n")
        print('                Original article source link:  '+ u)
        print('                title:                    ' + title)
        print("                ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print("                        【Compression info for original sentence】")
        print('                Original sentence:        ' + gst)
        html_content = get_html_content(gg)
        print("                ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print("                        【Compression info for longest sentence segment】")
        print("                Longest sentence segment: " + gloss)
        html_content = get_html_content(gloss)
        print("                ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print("                        【Compression info for last sentence segment】")
        print("                Last sentence segment:    " + glass)
        html_content = get_html_content(glass)
        print("                ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")