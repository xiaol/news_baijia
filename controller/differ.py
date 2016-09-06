# coding=utf-8
__author__ = 'yangjiwen'
import re
import jieba
import sys
from analyzer import jieba
import requests as r
import requests
import lxml.etree as etree
import lxml.html
import json
import urllib
import sys
import urllib2
from config import dbConn
from ltp import segmentor, postagger
# from __future__ import print_function

from sklearn import feature_extraction
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
from numpy import linalg as la

from AI_funcs.textrank4zh import TextRank4Keyword, TextRank4Sentence
tr4w = TextRank4Keyword()
tr4s = TextRank4Sentence()
reload(sys)
sys.setdefaultencoding('utf8')
DBStore = dbConn.GetDateStore()
conn = DBStore._connect_news
import random
import jieba.analyse
import MySQLdb
# import ConfigParser
from task.weibo_run_re import extract_tags_helper

# cf = ConfigParser.ConfigParser()
# cf.read("config.ini")

# host = cf.get("db", "host")
# port = int(cf.get("db", "port"))
# user = cf.get("db", "user")
# passwd = cf.get("db", "passwd")
# db_name = cf.get("db", "db")
# charset = cf.get("db", "charset")
# use_unicode = cf.get("db", "use_unicode")
# db = MySQLdb.connect(host='121.41.75.213', port=3306, user='yangjw', passwd='Huohua123', db='ZHIHUHOT_FULL_DATA', charset='utf8', use_unicode='True')
# cursor = db.cursor()

def duplicate_docs_check(domain_events):
    events = []
    for event in domain_events:
        if "sentence"  not in event.keys():
            text = event["text"]
            paragraph_list = text.split('\n')
            sentence_dict = {}
            sentence_cut_dict = {}
            paragraph_dict = {}
            i = 0
            for paragraph_elem in paragraph_list:
                if len(paragraph_elem) <= 4:
                    continue
                sentence_dict[str(i)], sentence_cut_dict[str(i)] = extractSentenceBlock(paragraph_elem)
                paragraph_dict[str(i)] = paragraph_elem
                i = i + 1
            event["sentence"] = sentence_dict
            event["sentence_cut"] = sentence_cut_dict
            event["paragraph"] = paragraph_dict
        events.append(event)
    duplicate_result = {}

    for event in events:
        main_event = event
        url = main_event["_id"]
        result = {}
        for event_elem in events:
            if url == event_elem["_id"]:
                continue
            duplicate_result, result = compare_doc_is_duplicate(main_event, event_elem, duplicate_result, result)
    # return duplicate_result

        common_opinion, self_opinion = extract_opinion(main_event,duplicate_result)
        event["self_opinion"] = self_opinion
        # event["common_opinion"] = common_opinion
        duplicate_result_by_paragraph = compute_match_ratio_sentence_to_paragraph(result)
        min_match_ratio, one_paragraph_by_article, total_paragraph_by_article = extract_opinon_by_match_ratio(main_event, duplicate_result_by_paragraph)
        if min_match_ratio < 0.39 and min_match_ratio > 0.1:
            event["self_opinion"] = one_paragraph_by_article
        else:
            event["self_opinion"] = ''
        # f = open("/Users/yangjiwen/Documents/yangjw/duplicate_case.txt","a")
        # if "eventId" in main_event.keys():
        #     f.write("event_id:"+str(main_event["eventId"]).encode('utf-8')+'\n\n'
        #             "新闻url:"+str(main_event["_id"]).encode('utf-8')+'\n\n'
        #             "独家观点:"+str(main_event["self_opinion"]).encode('utf-8')+'\n\n'
        #             # "共同观点:"+str(common_opinion).encode('utf-8')+'\n\n'
        #             "----------------------------------------------------"
        #             )
        #     f.close()

    differ_result = []
    for event in events:
        result = {}
        main_event = event
        url = main_event["_id"]
        # result = main_event
        result["_id"] = url
        result["self_opinion"] = ""
        if len((event["self_opinion"].strip())) >= 20:
            result["self_opinion"] = event["self_opinion"]

        # result["self_opinion"] = []
        # # result["common_opinion"] = []
        # for event_elem in events:
        #     if url == event_elem["_id"]:
        #         continue
        #     else:
        #         if len(event_elem["self_opinion"]) >= 20:
        #             result["self_opinion"].append({ "self_opinion": event_elem["self_opinion"], "_id": event_elem["_id"]})
        # #         if len(event_elem["common_opinion"]) > 20:
        #             result["common_opinion"].append({"common_opinion": event_elem["common_opinion"], "url": event_elem["_id"]})
        differ_result.append(result)
    return differ_result
        # conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"relate_opinion": result}})


def extract_opinion(main_event, result):
    sentence = main_event["sentence"]
    common_opinion=''
    self_opinion = ''
    for paragraph_key in sorted(sentence.keys()):
        self_opinion_flag = False
        common_opinion_flag = False
        paragraph_value = sentence[paragraph_key]
        if paragraph_key in result.keys():
            for sentence_key in sorted(paragraph_value.keys()):
                sentence_value = paragraph_value[sentence_key]
                if sentence_key in result[paragraph_key].keys():
                    # print type(sentence_value)
                    common_opinion=common_opinion + sentence_value + u'。'
                    common_opinion_flag = True
                else:
                    self_opinion = self_opinion + sentence_value + u'。'
                    self_opinion_flag = True
        else:
            for sentence_key in sorted(paragraph_value.keys()):
                sentence_value = paragraph_value[sentence_key]
                self_opinion = self_opinion + sentence_value + u'。'
                self_opinion_flag = True
        if self_opinion_flag:
            self_opinion = self_opinion + '\n'
        if common_opinion_flag:
            common_opinion = common_opinion + '\n'

    return common_opinion, self_opinion

def extract_opinon_by_match_ratio(main_event, duplicate_result_by_paragraph):
    total_paragraph_by_article = {}
    one_paragraph_by_article = ''
    paragraph = main_event["paragraph"]
    min_match_ratio = 1
    min_paragraph_key = '0'
    for paragraph_key, paragraph_value in paragraph.items():
        total_paragraph_by_article[paragraph_key] = {}
        total_paragraph_by_article[paragraph_key]["content"] = paragraph[paragraph_key]
        if paragraph_key in duplicate_result_by_paragraph.keys():
            total_paragraph_by_article[paragraph_key]["match_ratio"] = duplicate_result_by_paragraph[paragraph_key]
        else:
            total_paragraph_by_article[paragraph_key]["match_ratio"] = 1
        if  total_paragraph_by_article[paragraph_key]["match_ratio"] < min_match_ratio and is_normal_info(paragraph[paragraph_key]):
            min_match_ratio = total_paragraph_by_article[paragraph_key]["match_ratio"]
            min_paragraph_key = paragraph_key
            # print "min_paragraph_key_change"

    one_paragraph_by_article = paragraph[min_paragraph_key]


    return min_match_ratio,one_paragraph_by_article, total_paragraph_by_article

def compute_match_ratio_sentence_to_paragraph(result):
    duplicate_result_by_paragraph = {}

    for paragraph_key, paragraph_value in result.items():
        avg_match_ratio_by_paragraph = 1
        sum_match_ratio_by_paragraph = 0
        sentence_num = len(paragraph_value)
        for sentence_key, sentence_value in paragraph_value.items():
            top_match_ratio_by_sentence = 0
            for sentence_value_elem in sentence_value:
                if  sentence_value_elem["match_ratio"] > top_match_ratio_by_sentence:
                    top_match_ratio_by_sentence = sentence_value_elem["match_ratio"]
            sum_match_ratio_by_paragraph = sum_match_ratio_by_paragraph + top_match_ratio_by_sentence
        if sentence_num > 0:
            avg_match_ratio_by_paragraph = sum_match_ratio_by_paragraph*1.0/sentence_num

        duplicate_result_by_paragraph[paragraph_key] = avg_match_ratio_by_paragraph
    return duplicate_result_by_paragraph


def compare_doc_is_duplicate(main_event, event_elem, duplicate_result, result):
    sentence_cut = main_event["sentence_cut"]
    paragraph = event_elem["paragraph"]
    url = main_event["_id"]
    for paragraph_key, paragraph_value in sentence_cut.items():
        for sentence_key, sentence_value in paragraph_value.items():
            top_match_ratio = 0.0
            top_match_paragraph_id = "-1"
            keyword_num = len(sentence_value)
            # if keyword_num <=5:
            #     continue
            for compare_paragraph_key, compare_paragraph_value in paragraph.items():
                match_num = 0
                for sentence_keyword in sentence_value:
                    compare_result = compare_paragraph_value.find(sentence_keyword)
                    if compare_result >= 0:
                        match_num = match_num + 1
                if keyword_num < 2:
                    match_ratio = 0
                else:
                    match_ratio = match_num / (keyword_num * 1.0)
                if match_ratio > top_match_ratio:
                    top_match_ratio = match_ratio
                    top_match_paragraph_id = compare_paragraph_key
            if top_match_ratio > 0.8:
                # f = open("/Users/yangjiwen/Documents/yangjw/duplicate_case.txt","a")
                # f.write("mainurl:"+str(main_event["_id"]).encode('utf-8')
                #             +"main_paragraph_id:"+str(paragraph_key).encode('utf-8')
                #             +"main_sentence_id:"+str(sentence_key).encode('utf-8')
                #             +"sentence_content:"+str(main_event["sentence"][paragraph_key][sentence_key]).encode('utf-8')
                #             +"sentence_cut_content:"+str(','.join(sentence_value)).encode('utf-8')
                #             +"relateurl:"+str(url).encode('utf-8')
                #             +"realte_paragraph_id:"+str(top_match_paragraph_id).encode('utf-8')
                #             +"match_ratio:"+str(top_match_ratio).encode('utf-8')
                #             +"relate_paragraph_content"+str(paragraph[top_match_paragraph_id]).encode('utf-8')
                #             )


                # f.write("*"+str(main_event["_id"]).encode('utf-8')
                #             +"*"+str(paragraph_key).encode('utf-8')
                #             +"*"+str(sentence_key).encode('utf-8')
                #             +"*"+str(main_event["sentence"][paragraph_key][sentence_key]).encode('utf-8')
                #             +"*"+str(','.join(sentence_value)).encode('utf-8')
                #             +"*"+str(url).encode('utf-8')
                #             +"*"+str(top_match_paragraph_id).encode('utf-8')
                #             +"*"+str(top_match_ratio).encode('utf-8')
                #             +"*"+str(paragraph[top_match_paragraph_id]).encode('utf-8')
                #             )
                #
                #
                # f.write('\n')
                # f.close()
                # if paragraph_key not in duplicate_result.keys():
                #     duplicate_result[paragraph_key] = {}
                # if sentence_key not in duplicate_result[paragraph_key].keys():
                #     duplicate_result[paragraph_key][sentence_key] = {}
                #     if "text" not in duplicate_result[paragraph_key][sentence_key].keys():
                #         duplicate_result[paragraph_key][sentence_key]["text"] = main_event["sentence"][paragraph_key][sentence_key]
                #     if "relate" not in duplicate_result[paragraph_key][sentence_key].keys():
                #         duplicate_result[paragraph_key][sentence_key]["relate"] = [{"_id": event_elem["_id"], "paragraph_id": top_match_paragraph_id, "match_ratio": top_match_ratio, "text": event_elem["paragraph"][top_match_paragraph_id]}]
                #     else:
                #         duplicate_result[paragraph_key][sentence_key]["relate"].append({"_id": event_elem["_id"], "paragraph_id": top_match_paragraph_id, "match_ratio": top_match_ratio, "text": event_elem["paragraph"][top_match_paragraph_id]})


                if paragraph_key not in duplicate_result.keys():
                    duplicate_result[paragraph_key] = {}
                if sentence_key not in duplicate_result[paragraph_key].keys():
                    duplicate_result[paragraph_key][sentence_key] = []
                    duplicate_result[paragraph_key][sentence_key] = [{"url": url, "paragraph_id": top_match_paragraph_id, "match_ratio": top_match_ratio}]

                else:
                    duplicate_result[paragraph_key][sentence_key].append({"url": url, "paragraph_id": top_match_paragraph_id, "match_ratio": top_match_ratio})

            if paragraph_key not in result.keys():
                result[paragraph_key] = {}
            if sentence_key not in result[paragraph_key].keys():
                result[paragraph_key][sentence_key] = []
                result[paragraph_key][sentence_key] = [{"url": url, "paragraph_id": top_match_paragraph_id, "match_ratio": top_match_ratio}]

            else:
                result[paragraph_key][sentence_key].append({"url": url, "paragraph_id": top_match_paragraph_id, "match_ratio": top_match_ratio})

            # if paragraph_key not in result.keys():
            #     result[paragraph_key] = {}
            # if sentence_key not in result[paragraph_key].keys():
            #     result[paragraph_key][sentence_key] = {}
            #     result[paragraph_key][sentence_key]["text"] = ""
            #     if "relate" not in result[paragraph_key][sentence_key].keys():
            #         result[paragraph_key][sentence_key]["relate"] = [{"url": url, "paragraph_id": top_match_paragraph_id, "match_ratio": top_match_ratio}]
            #     else:
            #         result[paragraph_key][sentence_key]["relate"].append({"url": url, "paragraph_id": top_match_paragraph_id, "match_ratio": top_match_ratio})
    return duplicate_result, result


def extractSentenceBlock(doc):
    SENTENCE_SEP = re.compile(ur'[。\n!！]')
    result = {}
    result_cut = {}
    doc_array=re.split(SENTENCE_SEP, doc.encode('utf8').decode("utf8"))
    i = 0
    for elem in doc_array:
        if len(elem) <= 5:
            continue
        result[str(i)] = elem.strip()
        keyword = set()
        keyword = {word for word in jieba.cut_with_stop(elem.strip())}
        keyword_list = list(keyword)
        result_cut[str(i)] = keyword_list
        # result.append(elem.strip())
        i = i + 1
    return result, result_cut

def is_normal_info(paragraph):
    paragraph = paragraph
    print ""
    print type(paragraph)
    pattern=re.compile(ur'http[:：]|[[【]|[]】]|二维码|来源[:：]|编辑[:：]|作者[:：]|发布[:：]|正文已结束|字号[:：]|未经授权禁止转载')
    result = re.search(pattern, paragraph)
    if result:
        return False
    else:
        return True

def data_tranfer(domain_events):
    i =0
    result = []
    for elem in domain_events:
        dict = {"_id": i, "text": elem}
        result.append(dict)
        i = i + 1
    return result

def compare_doc_is_duplicate_copy(main_event, event_elem, duplicate_result, result):
    sentence_cut = main_event["sentence_cut"]
    paragraph = event_elem["paragraph"]
    url = main_event["_id"]
    for paragraph_key, paragraph_value in sentence_cut.items():
        for sentence_key, sentence_value in paragraph_value.items():
            top_match_ratio = 0.0
            top_match_paragraph_id = "-1"
            keyword_num = len(sentence_value)
            # if keyword_num <=5:
            #     continue
            for compare_paragraph_key , compare_paragraph_value in paragraph.items():
                match_num = 0
                for sentence_keyword in sentence_value:
                    compare_result = compare_paragraph_value.find(sentence_keyword)
                    if compare_result >= 0:
                        match_num = match_num + 1
                if keyword_num < 2:
                    match_ratio = 0
                else:
                    match_ratio = match_num / (keyword_num * 1.0)
                if match_ratio > top_match_ratio:
                    top_match_ratio = match_ratio
                    top_match_paragraph_id = compare_paragraph_key
            if top_match_ratio > 0.8:
                if url not in duplicate_result.keys():
                    duplicate_result[url] = {}
                if paragraph_key not in duplicate_result[url].keys():
                    duplicate_result[url][paragraph_key] = {}
                if sentence_key not in duplicate_result[url][paragraph_key].keys():
                    duplicate_result[url][paragraph_key][sentence_key] = []
                    duplicate_result[url][paragraph_key][sentence_key] = [{"url": url, "paragraph_id": top_match_paragraph_id, "match_ratio": top_match_ratio}]

                else:
                    duplicate_result[url][paragraph_key][sentence_key].append({"url": url, "paragraph_id": top_match_paragraph_id, "match_ratio": top_match_ratio})

            if paragraph_key not in result.keys():
                result[paragraph_key] = {}
            if sentence_key not in result[paragraph_key].keys():
                result[paragraph_key][sentence_key] = []
                result[paragraph_key][sentence_key] = [{"url": url, "paragraph_id": top_match_paragraph_id, "match_ratio": top_match_ratio}]

            else:
                result[paragraph_key][sentence_key].append({"url": url, "paragraph_id": top_match_paragraph_id, "match_ratio": top_match_ratio})
    return duplicate_result, result


def bingSearch():
    apiUrl ='http://cn.bing.com/hpm?'
    response = requests.get(apiUrl)
    if response.status_code == 200:
        print "content,%s"%response.text
        content = etree.HTML(response.text)
        pages_arr = content.xpath('//div[@id="crs_scroll"]/ul/li')
        for pages in pages_arr:
            img = pages.xpath('./a/span/img/@src')[0]
            img_after = conver_small_to_larger(img)
            topic_pattern = re.compile(r'<div class="hp_text">(.*?)</div>')
            # pages_str = ET.tostring(pages, encoding='utf8', method='xml')
            pages_str = etree.tostring(pages, encoding='utf-8')
            topic_search_result = re.search(topic_pattern, pages_str)
            if topic_search_result:
                topic = topic_search_result.group(1)
            else:
                continue
            print type(topic)
            topic = topic.decode("utf8")
            topic = "出境购超5千元征税".decode("utf8")
            no_error_pattern = re.compile(u'[\u4e00-\u9fa5_0-9]+')
            if re.search(no_error_pattern, topic):
                params = {"topic": topic, "img": img_after}
                print "topic,%s"%topic
                print "search_start"
                text_list = do_search_task(params)
                # for text_elem in text_list:
                    # input_list.append(text_elem["text"])
                tranfer_list = data_tranfer(text_list)
                result = duplicate_docs_check(tranfer_list)
                return result
    #             text_list = '$'.join(text_list)
    #             params_key = {"article": text_list}
    #             data = urllib.urlencode(params_key)
    #             # search_url ="http://192.168.0.37:8083/search?"+data
    #             search_url ="http://121.40.34.56/news/baijia/differOpinion"
    #             # try:
    #             req = urllib2.Request(url = search_url, data = data)
    #             res_data = urllib2.urlopen(req)
    #             res = res_data.read()
    #             print res
    #             # print type(res)
    #             text = json.loads(res)
    #             for paragraph, paragraph_value in text.items():
    #                 for sentence, sentence_value in paragraph_value.items():
    #                     print "paragraph,%s" % paragraph
    #                     print "sentence,%s" % sentence
    #                     for key, value in sentence_value.items():
    #                         print repr(key)
    #                         if key == u'text':
    #                             print "text:%s"%value.encode('utf-8')
    #                         if key == u'relate':
    #                             for elem in value:
    #                                 print "relate_opinion,%s"%elem["text"].encode('utf-8')
    #             print text
    #             # text = (res.json())
    #             # print text
    #             # except:
    #             # print "search_url_exception"
    #
    #         else:
    #             continue
    # else:
    #     return ""


def do_article_task(params):
    if "topic" in params.keys():
        topic = params["topic"]
    docs = conn["news_ver2"]["article"].find_one({"_id": topic})
    if docs:
        return docs["article"]
    params_key = {"key": topic}
    data = urllib.urlencode(params_key)
    # search_url ="http://192.168.0.37:8083/search?"+data
    search_url ="http://60.28.29.37:8083/search?"+data
    # try:
    r_text = r.get(search_url)
    text = (r_text.json())
    search_list = text["searchItems"]
    # except:
    #     print "search_url_exception"
    #     return
    text_list = []
    for search_elem in search_list:
        result_elem = {}
        search_url = search_elem["url"]
        search_title = search_elem["title"]
        search_title = trim_bracket(search_title)
        if not (search_url.endswith('html') or search_url.endswith('shtml') or search_url.endswith('htm')):
            continue
        if search_url.split('/')[-1].find('index')>=0:
            continue
        try:
            apiUrl_text = "http://121.41.75.213:8080/extractors_mvc_war/api/getText?url=" + search_url
            r_text = requests.get(apiUrl_text)
            text = (r_text.json())["text"]
        except:
            print "r_text_exception"
            continue
        if text:
            text = trim_new_line_character(text)
        if not text:
            print "url:%s" % search_url, " : text is None"
            continue
        result_elem["sourceUrl"] = search_url
        result_elem["title"] = replace_html(str(search_title))
        result_elem["text"]= text
        text_list.append(result_elem)
    elem = {}
    elem["_id"] = topic
    elem["article"] = text_list
    item_dict = dict(elem)
    conn['news_ver2']['article'].save(item_dict)

    return text_list


def do_search_task(params):
    if "url" in params.keys():
        url = params["url"]
    else:
        url = ""

    if "topic" in params.keys():
        topic = params["topic"]
    else:
        title = params["title"]
        # regex = ur"[：]"
        print type()
        title = title.encode('utf8').decode("utf8")
        regex = ur"[,|，].*称[,|，]|“|”| |‘|’|《|》|%|\[|]|-|·|:|："
        title = re.sub(regex, "", title)
        topic = title[:len(title)/3*2]

    if "img" in params.keys():
        img = params["img"]
    else:
        img = ""

    params_key = {"key": topic}
    data = urllib.urlencode(params_key)
    # search_url ="http://192.168.0.37:8083/search?"+data
    search_url ="http://60.28.29.37:8083/search?"+data
    # try:
    r_text = r.get(search_url)
    text = (r_text.json())
    search_list = text["searchItems"]
    # except:
    #     print "search_url_exception"
    #     return
    search_doc_num = 0
    text_list = []
    for search_elem in search_list:
        result_elem = {}
        search_url = search_elem["url"]
        search_title = search_elem["title"]
        search_title = trim_bracket(search_title)
        if not (search_url.endswith('html') or search_url.endswith('shtml') or search_url.endswith('htm')):
            continue
        if search_url.split('/')[-1].find('index')>=0:
            continue
        try:
            apiUrl_text = "http://121.41.75.213:8080/extractors_mvc_war/api/getText?url=" + search_url
            r_text = requests.get(apiUrl_text)
            text = (r_text.json())["text"]
        except:
            print "r_text_exception"
            continue
        if text:
            text = trim_new_line_character(text)
        if not text:
            print "url:%s" % search_url, " : text is None"
            continue
        result_elem["_id"] = search_url
        # updateTime = time_match(search_url)
        # if updateTime[0:4]<>'2016':
        #     print "updateTime year no equal 2015"
        #     print "updateTime,%s"%updateTime
        #     print "sourceUrl,%s"%search_url
        #     continue
        # result_elem["updateTime"] = updateTime
        # print "updateTime,%s"%updateTime
        result_elem["sourceUrl"] = search_url
        result_elem["title"] = replace_html(str(search_title))
        result_elem["keyword"] = str(topic)
        result_elem["text"]= text
        text_list.append(text)
    return text_list





def replace_html(s):
    s = s.replace('&quot;','"')
    s = s.replace('&amp;','&')
    s = s.replace('&lt;','<')
    s = s.replace('&gt;','>')
    s = s.replace('&nbsp;',' ')
    s = s.replace(' - 361way.com','')
    return s

def conver_small_to_larger(img):
    if re.sub("&","&amp;", img).startswith("http://s.cn.bing.net"):
        return re.sub("&","&amp;", img)
    else:
        return "http://s.cn.bing.net" + re.sub("&","&amp;", img)

def trim_bracket(title):
    # print "title,%s"%title
    bracket_pat=re.compile(r'\(.*?\)')
    title=re.sub(bracket_pat, '', title)
    bracket_pat_1=re.compile(r'（.*?）')
    title=re.sub(bracket_pat_1, '', title)
    bracket_pat_2=re.compile(r'【.*?】')
    title=re.sub(bracket_pat_2, '', title)
    bracket_pat_3=re.compile(r'[.*?]')
    title=re.sub(bracket_pat_3, '', title)
    return title

def trim_new_line_character(text):
    text_list = text.split('\n')
    result_list = []
    for text_elem in text_list:
        if not text_elem.strip():
            continue
        else:
            result_list.append(text_elem)

    return '\n'.join(result_list)+'\n'

def split_words(text,article):
    text = text.decode('utf-8')
    result = []
    for eng in re.findall(r'[A-Za-z ]+' ,text):
        if len(eng) > 2:
            result.append(eng)
            text = text.replace(eng, "")
    # 最大匹配
    maximum = 6
    index = len(text)
    while index > 0:
      word = None
      for length in range(maximum, 0, -1):
        if index - length < 0:
          continue
        piece = text[(index - length):index]
        if piece_in_article(piece, article):
          word = piece
          result.append(word)
          index = index - length
          break
      if word is None:
        index -= 1
    return result

def piece_in_article(piece, article):
    if article.count(piece)>1:
        return True
    else:
        return False

def extract_tag(content):
    tags = []
    result = ""
    print content
    print '\n'
    for strong_text in re.findall(r'<strong>(.*?)</strong>', content):
        print strong_text
        result = result + re.sub(r'<.*?>', "", strong_text)
    if len(result)>=10:
        tr4w.analyze(text=result, lower=True, window=2)
        # print '/'.join(tr4w.get_keyphrases(keywords_num=30, min_occur_num= 1))
        # print 'end'
        # for item in tr4w.get_keywords(50, word_min_len=2):
        for item in tr4w.get_keyphrases(keywords_num=30, min_occur_num= 1):
            tags.append(item)
            # print item.word
            # print item.weight
    # tr4s.analyze(text=re.sub(r'<.*?>', "", content), lower=True, source = 'all_filters')
    # abs = u''
    # for item in tr4s.get_key_sentences(num=3):
    #     abs = abs+ item.sentence + u'。'
    # tags.append(abs)
    return tags

def extract_abs(content):
    tr4s.analyze(text=re.sub(r'<.*?>', "", content), lower=True, source = 'all_filters')
    abs = []
    for item in tr4s.get_key_sentences(num=3):
        abs.append(item.sentence)
    return abs


def do_relate_task(params):
    if "title" in params.keys():
        title = params["title"]
    docs = conn["news_ver2"]["relate"].find_one({"_id": title})
    if docs and len(docs["relate_opinion"])>0:
        return docs["relate_opinion"]
    params_key = {"url": params["url"]}
    data = urllib.urlencode(params_key)
    search_url ="http://120.27.162.110:9001/extract_news"
    # try:
    req = urllib2.Request(url = search_url, data = data)
    res_data = urllib2.urlopen(req)
    res = res_data.read()
    # print res
    # print type(res)
    content =""
    text = json.loads(res)
    if text["ret_code"] <>1:
        try:
            print "ret_code_erorr"
            apiUrl_text = "http://121.41.75.213:8080/extractors_mvc_war/api/getText?url=" + params["url"]
            r_text = requests.get(apiUrl_text)
            content = (r_text.json())["text"]
            # print content
        except:
            return {'response': 202, 'msg': 'text is null'}
    if text["ret_code"] == 1:
        for elem in text["result"]["content"]:
            if "text" in elem.keys():
                content = content + elem["text"]
        # print content
    try:
        result = split_words(title, content)
    except:
        return {'response': 202, 'msg': 'text is null'}
    words = []
    for word in result[::-1]:
        print word,' ',
        # words.append(word)


    if len([i.encode('utf-8') for i in result[::-1] if len(i)>=2])>=1:
        key = " ".join([i.encode('utf-8') for i in result[::-1] if len(i)>=2])
    else:
        key = title[:len(title)/3 * 2]

    sentence = key.encode("utf-8")
    words = segmentor.segment(sentence)
    print "\n".join(words)
    num =len(words)
    # print "num,%s" %num
    postags = postagger.postag(words)
    print "\n".join(postags)
    key_new=[]
    for i in range(num):
        # print "%s  %s  " % (netags[i], words[i]),
      if postags[i] not in ('m', 'q', 'wp','u'):
          key_new.append(words[i].decode('utf-8'))
    print " ".join(key_new[:3])

    params_key = {"key": " ".join(key_new[:3])}

    if "tags" in params.keys():
        if params["tags"] is not None:
            params_key = {"key": params["tags"]}
    data = urllib.urlencode(params_key)
    search_url ="http://120.55.88.11:8088/search?"+data
    # try:
    r_text = r.get(search_url)
    text = (r_text.json())
    search_list = text["searchItems"]
    # except:
    #     print "search_url_exception"
    #     return
    # text_list = []
    # url_set = set()
    for search_elem in search_list:
        # search_url = search_elem["url"]
        print search_elem["title"]
    relate_opinion = {}
    relate_opinion["searchItems"] = search_list[:4]

    if "tags" in params.keys():
        tag_temp = set(extract_tag(content) + [i for i in key_new if len(i)>=2])
        tag_temp.discard(params["tags"])
        relate_opinion["tags"] = list(tag_temp)
    else:
        relate_opinion["tags"] = list(set(extract_tag(content) + [i for i in key_new if len(i)>=2]))

    relate_opinion["abs"] = extract_abs(content)
    elem = {}
    elem["_id"] = title
    elem["relate_opinion"] = relate_opinion
    item_dict = dict(elem)
    # conn['news_ver2']['relate'].save(item_dict)
    # print relate_opinion
    return relate_opinion

globvar = 3124756  #3000000
def random_fetch_question():
    global globvar
    rand = random.random()
    print globvar
    # doc = conn["news_ver2"]["questionItem"].find_one({'random': {"$gte": rand}})
    doc = conn["news_ver2"]["questionItem"].find_one({'nid': globvar})
    globvar = globvar + 1
    if not doc:
        return random_fetch_question()
    if "_id" in doc.keys():
        doc.pop('_id')
    return doc

#by liulei for QA

#@brief: get similariy of sentense2 with sentense1
#@param:   keyWords1----list of sentense1
#          keyWords2----list of sentense2
def getSenSimilarity(keyWords1, keyWords2):
    num = 0
    for item in keyWords1:
        if item in keyWords2:
            num += 1
    return num


qkws = []
def getQuestionKws():
    cursor = conn['news_ver2']['qaDataSet'].find()
    for doc in cursor:
        if "keywords" not in doc.keys():
            continue
        if '_id' not in doc.keys():
            continue
        kws = doc.pop('keywords')
        id = doc.pop('_id')
        qkws.append((id, kws))

#jieba分词
words_cut = []
_ids = []
nn = 0
def getCutWords():
    global words_cut, _ids, nn
    offset = 0
    while True:
        cursor = conn['news_ver2']['qaDataSet'].find().skip(offset).limit(100)
        if offset >= cursor.count():
            break
        for doc in cursor:
            if 'keywords' in doc.keys() and '_id' in doc.keys():
                kws = doc.pop('keywords')
                _id = doc.pop('_id')
                wd = ' '.join(kws)
                words_cut.append(wd)
                _ids.append(_id)
        offset += 100
        print offset

        #for doc in cursor:
        #    if "question" in doc.keys() and '_id' in doc.keys():
        #        question = doc.pop('question')
        #        _id = doc.pop('_id')
        #        #cut
        #        words = jieba.cut(question)
        #        #add space between words
        #        wd = ' '.join(words)
        #        words_cut.append(wd)
        #        _ids.append(_id)
        #offset += 100

#get tf-idf
words_bag = []
weight_matrix = []
def getWeights():
    global words_bag
    global weight_matrix
    vectorizer=CountVectorizer()#该类会将文本中的词语转换为词频矩阵，矩阵元素a[i][j] 表示j词在i类文本下的词频
    transformer=TfidfTransformer()#该类会统计每个词语的tf-idf权值
    tfidf=transformer.fit_transform(vectorizer.fit_transform(words_cut))#第一个fit_transform是计算tf-idf，第二个fit_transform是将文本转为词频矩阵
    words_bag=vectorizer.get_feature_names()#获取词袋模型中的所有词语
    print len(words_cut)
    weight_matrix=tfidf.toarray()#将tf-idf矩阵抽取出来，元素a[i][j]表示j词在i类文本中的tf-idf权重
    print 'finish get weights'

#collect data when service start
def collData():
    print 'begin colldata'
    getCutWords()
    print '-----get cut words =-----finished'
    #getWeights()
    print '====collData finished====='

def cosSimilar(inA, inB):
    inA = np.mat(inA)
    inB = np.mat(inB)
    num = float(inA*inB.T)
    denom = la.norm(inA)*la.norm(inB)
    return 0.5+0.5*(num/denom)

#compare target question
def getMostSimilary(askedQues):
    askedQues_cut = jieba.cut(askedQues)
    cut = ' '.join(askedQues_cut)
    words_cut.append(cut)
    #cut_list = [cut,]
    vectorizer=CountVectorizer()#该类会将文本中的词语转换为词频矩阵，矩阵元素a[i][j] 表示j词在i类文本下的词频
    transformer=TfidfTransformer()#该类会统计每个词语的tf-idf权值
    tfidf=transformer.fit_transform(vectorizer.fit_transform(words_cut))#第一个fit_transform是计算tf-idf，第二个fit_transform是将文本转为词频矩阵

    s1 = tfidf * tfidf.T
    SimMatris = s1.toarray()
    max_index = -1
    max_score = 0
    target_sims = SimMatris[len(words_cut ) - 1]
    for i in range (len(words_cut) -2):
        if target_sims[i] > max_score:
            max_score = target_sims[i]
            max_index = i

    words_cut.remove(cut)
    if max_index == -1:
        return 'No matching answer. Please try another question.'
    print max_index, len(_ids)
    _id = _ids[max_index]
    doc = conn["news_ver2"]["qaDataSet"].find_one({'_id': _id})
    if doc and "_id" in doc.keys():
        doc.pop('_id')
        return doc
    else:
        return 'No matching answer. Please try another question.'



    #words_aksed = vectorizer.get_feature_names()#获取词袋模型中的所有词语
    #weight_asked = tfidf.toarray()#将tf-idf矩阵抽取出来，元素a[i][j]表示j词在i类文本中的tf-idf权重

    #get target matrix of asked question
    target_matrix = [0.0 for i in range(len(words_bag))]
    for wd in words_aksed:
        if wd in words_bag:
            print wd
            _index_bag = words_bag.index(wd)
            _index_local = words_aksed.index(wd)
            print _index_bag, _index_local, weight_asked[0][_index_local]
            target_matrix[_index_bag] = weight_asked[0][_index_local]

    maxScore = 0
    index = 0
    weight_num =  len(weight_matrix)
    if weight_num and (len(target_matrix) == len(weight_matrix[0])):
        for i in range(weight_num):
            score = cosSimilar(target_matrix, weight_matrix[i])
            if score > maxScore:
                maxScore = score
                index = i

    if maxScore == 0:
        return 'No matching answer. Please try another question.'

    _id = _ids[index]
    doc = conn["news_ver2"]["qaDataSet"].find_one({'_id': _id})
    if doc and "_id" in doc.keys():
        doc.pop('_id')
        return doc
    else:
        return 'No matching answer. Please try another question.'

#@brief: get top n questions from db
#@parms: askedQues --- asked question
#        n --- get top n
def getSimQuestions(askedQues, n):
    dic = []
    asked_kws = jieba.analyse.extract_tags(askedQues, 5)
    for i in asked_kws:
        print i.encode('utf-8')
    for id, kws in qkws:
        sim_score = getSenSimilarity(asked_kws, kws)
        #print (bytes(id) + ':' + bytes(sim_score))
        if len(dic) < n:
            dic.append((id, sim_score))
            dic = sorted(dic, key=lambda d: d[1])
        else:
            for item in dic:
                id2, sim_score2 = item
                if sim_score > sim_score2 :
                    dic.remove(item)
                    dic.append((id, sim_score))
                    dic = sorted(dic, key=lambda d: d[1])
                break
    if dic and dic[0][1] > 0:
        _id = dic[0][0]
        doc = conn["news_ver2"]["qaDataSet"].find_one({'_id': _id})
        del doc['_id']
        return doc
    else:
        return 'No matching answer. Please try another question.'

def get_bigrams(string):
    '''
    Takes a string and returns a list of bigrams
    '''
    s = string.lower()
    return [s[i:i+2] for i in xrange(len(s) - 1)]

def string_similarity(str1, str2):
    '''
    Perform bigram comparison between two strings
    and return a percentage match in decimal form
    '''
    pairs1 = get_bigrams(str1)
    pairs2 = get_bigrams(str2)
    union  = len(pairs1) + len(pairs2)
    hit_count = 0
    for x in pairs1:
        for y in pairs2:
            if x == y:
                # print x
                hit_count += 1
                break
    return max((1.0 * hit_count)/len(pairs1), (1.0 * hit_count)/len(pairs2))    #(2.0 * hit_count) / union


def getZHihuQuestions(askedQues, n):
    db = MySQLdb.connect(host='121.41.75.213', port=3306, user='yangjw', passwd='Huohua123', db='ZHIHUHOT_FULL_DATA', charset='utf8', use_unicode='True')
    cursor = db.cursor()
    dic = []
    sked_kws = jieba.analyse.extract_tags(askedQues, 5)   #extract_tags_helper(askedQues.encode("utf-8"))
    if len(sked_kws)>=1:
        str_sked_kws = ' '.join(sked_kws)
    else:
        str_sked_kws = askedQues
    # for i in asked_kws:
    #     print i.encode('utf-8')
    # sql = "SELECT NAME,LINK_ID FROM QUESTION WHERE NAME  like" +'"' + "%" + sked_kws[0] + "%" +'"'   #and LINK_ID = 19680895
    # sql = "SELECT NAME,LINK_ID FROM QUESTION WHERE NAME  like %s"  #and LINK_ID = 19680895
    # sql = "SELECT NAME,LINK_ID FROM QUESTION_GX WHERE NAME  REGEXP " +"'" + str_sked_kws +"'" +" limit 10000"
    sql = "SELECT NAME,LINK_ID FROM QUESTION_GX WHERE MATCH(NAME)  AGAINST(" + "'" + str_sked_kws +"'" + " IN NATURAL LANGUAGE MODE) limit 10"

    # cursor.execute(sql, (sked_kws[0],))
    cursor.execute(sql)
    results = cursor.fetchall()
    cursor.close()
    searchResult = []
    for row in results:
        doc = {}
        question = ""
        answer = ""
        question = str(row[0])
        answer = str(row[1])
        similarity = string_similarity(askedQues.decode('utf-8'), question.decode('utf-8'))
        doc["question"] = question
        doc["answer"] = "https://www.zhihu.com/question/" + answer
        doc["similarity"] = similarity
        searchResult.append(doc)
        # break
    if len(searchResult) > 0:
        doc={}
        # dic = sorted(searchResult, key=lambda d: d["similarity"], reverse =True)
        # doc["question"] = dic[0]["question"]
        # doc["answer"] = dic[0]["answer"]
        doc["question"] = searchResult[0]["question"]
        doc["answer"] = searchResult[0]["answer"]
        doc["keywords"] = sked_kws
        return doc
    else:
        return 'No matching answer. Please try another question.'


if __name__ == '__main__':
    # print do_article_task({"topic":"抢红包大打出手"})
    # print bingSearch()
    getZHihuQuestions("史上最难题之一，搬砖的如何让马云请他吃顿饭？",1)
    # extract_tag("中新网北京12月1日电(记者 张曦) 30日晚，高圆圆和赵又廷在京举行答谢宴，诸多明星现身捧场，其中包括张杰(微博)、谢娜(微博)夫妇、何炅(微博)、蔡康永(微博)、徐克、张凯丽、黄轩(微博)等。30日中午，有媒体曝光高圆圆和赵又廷现身台北桃园机场的照片，照片中两人小动作不断，尽显恩爱。事实上，夫妻俩此行是回女方老家北京举办答谢宴。")
    do_relate_task({"url":"http://mp.weixin.qq.com/s?__biz=MjM5MTk2OTIwOA==&mid=401562035&idx=1&sn=c3bebee6cb09072cd048bea3108b03c7&scene=23&srcid=0321UwN45f6LVCgXQvbzo1NI#rd","title":"20宗宁：网红经济的悖论，现在做已经晚了"})
    # do_relate_task({"url":"http://www.taiwan.cn/xwzx/shytp/201606/t20160630_11495228_12.htm","title":"14宗宁：网红经济的悖论，现在做已经晚了"})
    # domain_events = [u"今日，法晚记者从河南警方获悉，北京和颐酒店女子遇袭案发生后，河南公安厅全力配合北京警方抓捕逃犯，由李法正副厅长坐镇指挥，整个抓捕过程保密性很强，行动十分迅速。\n今日，法晚记者从河南警方获悉，北京和颐酒店女子遇袭案发生后，五名嫌犯逃窜到了原籍河南省许昌市襄城县汾陈乡。北京警方调查得知后，随即向河南省公安厅发出了协助抓捕的请求。河南省公安厅的主要领导对这起案件非常重视，派出了负责打击刑事犯罪和网络安全保卫工作的李法正副厅长坐镇指挥。这次抓捕行动由许昌市公安局刑侦支队统一调配，在掌握了犯罪嫌疑人李某的逃窜轨迹后，襄城县刑警队迅速出动，将李某抓获归案。许昌市、襄城县公安机关很多重要岗位的警官直到破案才知道原来自己的同事也参与了此次行动。此前，北京警方回应网友对破案速度的质疑时称：此次抓捕行动需要跨省、跨警种的合作，两地警方的协调、沟通工作就花费了一部分时间。"
    #                  ,u"法晚深度即时（稿件统筹 朱顺忠 实习生 尚妍）今日，法晚记者从河南警方获悉，北京和颐酒店女子遇袭案发生后，河南公安厅全力配合北京警方抓捕逃犯，由李法正副厅长坐镇指挥，整个抓捕过程保密性很强，行动十分迅速。\n今日，法晚（微信公号ID：fzwb_52165216）记者从河南警方获悉，北京和颐酒店女子遇袭案发生后，五名嫌犯逃窜到了原籍河南省许昌市襄城县汾陈乡。北京警方调查得知后，随即向河南省公安厅发出了协助抓捕的请求。河南省公安厅的主要领导对这起案件非常重视，派出了负责打击刑事犯罪和网络安全保卫工作的李法正副厅长坐镇指挥。这次抓捕行动由许昌市公安局刑侦支队统一调配，在掌握了犯罪嫌疑人李某的逃窜轨迹后，襄城县刑警队迅速出动，将李某抓获归案。许昌市、襄城县公安机关很多重要岗位的警官直到破案才知道原来自己的同事也参与了此次行动。此前，北京警方回应网友对破案速度的质疑时称：此次抓捕行动需要跨省、跨警种的合作，两地警方的协调、沟通工作就花费了一部分时间。"]
    #
    # result = data_tranfer(domain_events)
    # print duplicate_docs_check(result)
    # # print (extract_opinion(article))
