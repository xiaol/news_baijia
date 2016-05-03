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
reload(sys)
sys.setdefaultencoding('utf8')
DBStore = dbConn.GetDateStore()
conn = DBStore._connect_news

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
    pattern=re.compile(ur'http[:：]|[[【]|[]】]|扫描二维码|来源[:：]|编辑[:：]|作者[:：]|发布[:：]|正文已结束|字号[:：]|未经授权禁止转载')
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


if __name__ == '__main__':
    # print do_article_task({"topic":"抢红包大打出手"})
    print bingSearch()
    # domain_events = [u"今日，法晚记者从河南警方获悉，北京和颐酒店女子遇袭案发生后，河南公安厅全力配合北京警方抓捕逃犯，由李法正副厅长坐镇指挥，整个抓捕过程保密性很强，行动十分迅速。\n今日，法晚记者从河南警方获悉，北京和颐酒店女子遇袭案发生后，五名嫌犯逃窜到了原籍河南省许昌市襄城县汾陈乡。北京警方调查得知后，随即向河南省公安厅发出了协助抓捕的请求。河南省公安厅的主要领导对这起案件非常重视，派出了负责打击刑事犯罪和网络安全保卫工作的李法正副厅长坐镇指挥。这次抓捕行动由许昌市公安局刑侦支队统一调配，在掌握了犯罪嫌疑人李某的逃窜轨迹后，襄城县刑警队迅速出动，将李某抓获归案。许昌市、襄城县公安机关很多重要岗位的警官直到破案才知道原来自己的同事也参与了此次行动。此前，北京警方回应网友对破案速度的质疑时称：此次抓捕行动需要跨省、跨警种的合作，两地警方的协调、沟通工作就花费了一部分时间。"
    #                  ,u"法晚深度即时（稿件统筹 朱顺忠 实习生 尚妍）今日，法晚记者从河南警方获悉，北京和颐酒店女子遇袭案发生后，河南公安厅全力配合北京警方抓捕逃犯，由李法正副厅长坐镇指挥，整个抓捕过程保密性很强，行动十分迅速。\n今日，法晚（微信公号ID：fzwb_52165216）记者从河南警方获悉，北京和颐酒店女子遇袭案发生后，五名嫌犯逃窜到了原籍河南省许昌市襄城县汾陈乡。北京警方调查得知后，随即向河南省公安厅发出了协助抓捕的请求。河南省公安厅的主要领导对这起案件非常重视，派出了负责打击刑事犯罪和网络安全保卫工作的李法正副厅长坐镇指挥。这次抓捕行动由许昌市公安局刑侦支队统一调配，在掌握了犯罪嫌疑人李某的逃窜轨迹后，襄城县刑警队迅速出动，将李某抓获归案。许昌市、襄城县公安机关很多重要岗位的警官直到破案才知道原来自己的同事也参与了此次行动。此前，北京警方回应网友对破案速度的质疑时称：此次抓捕行动需要跨省、跨警种的合作，两地警方的协调、沟通工作就花费了一部分时间。"]
    #
    # result = data_tranfer(domain_events)
    # print duplicate_docs_check(result)
    # print (extract_opinion(article))
