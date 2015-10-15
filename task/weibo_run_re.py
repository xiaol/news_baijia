#coding=utf-8

from jieba.analyse import extract_tags
import jieba
import pymongo
from pymongo.read_preferences import ReadPreference
import json
from requests.exceptions import ConnectionError
import requests_with_sleep as requests
import requests as r
import re
import cStringIO,urllib
import subprocess
import time
import lxml.etree as etree
import sys
import logging
import os
from PIL import Image
import datetime
from requests.exceptions import Timeout, ConnectionError
from text_classifier import get_category_by_hack
import urllib

import gensim
from math import sqrt
import numpy as np
import math

try:
    import zbar
except ImportError:
    print('Can\'t import zbar')

reload(sys)
sys.setdefaultencoding('utf8')

arg = sys.path[0].split('/')
path_add = arg[:-1]
path_add = '/'.join(path_add)

sys.path.append(path_add+"/weibo/")
sys.path.append(path_add+"/controller/")
sys.path.append(path_add+"/analyzer/")
sys.path.append(path_add)
try:
    from weibo import weibo_relate_docs_get, user_info_get
    from controller.utils import get_start_end_time, is_number
    from weibo import Comments
    from analyzer import jieba
except ImportError:
    import user_info_get
    import weibo_relate_docs_get
    from utils import get_start_end_time, is_number
    import Comments
    print "import error"
from abstract import KeywordExtraction
from para_sim.TextRank4ZH.gist import Gist
from AI_funcs.Gist_and_Sim.gist import Gist as g
from extract_time import time_match



conn = pymongo.MongoReplicaSetClient("h44:27017, h213:27017, h241:27017", replicaSet="myset",
                                                             read_preference=ReadPreference.SECONDARY)
HOST_NER = "60.28.29.47"

not_need_copy_content_news = ["网易新闻图片", "观察者网",'地球图辑队','bing热点']


g_time_filter = ["今天","明天","后天"]
g_gpes_filter = ["中国","全国","美国"]
g_keyword_filter = ["小时", "原谅", "标题"]

def extract_tags_helper(sentence, topK=20, withWeight=False):
    tags = []
    for eng in re.findall(r'[A-Za-z ]+',sentence):
        if len(eng) > 2:
            tags.append(eng)
    tagRule = get_tag_from_group(sentence)
    tagRule2 = get_tag_from_group2(sentence)

    tags.extend(extract_tags(sentence, topK, withWeight, allowPOS=('ns', 'n', 'nr', 'nt','nz')))
    tags = [x for x in tags if not is_number(x)]
    tags = [x for x in tags if not x in g_gpes_filter and not x in g_time_filter and not x in g_keyword_filter]
    tags = [x for x in tags if not x in tagRule and not x in tagRule2]
    if len(tagRule2) > 1:
        tags.append(tagRule2)
    if len(tagRule) > 1:
        tags.append(tagRule)
    return tags


def get_tag_from_group(text):
    p_tag = re.compile(r'.*《(?P<tag>.*)》.*')
    tagSearch = p_tag.search(text)
    tag = ''
    if tagSearch:
        tag = tagSearch.group('tag')
    return tag


def get_tag_from_group2(text):
    p_tag = re.compile(r'.*"(?P<tag>.*)".*')
    tagSearch = p_tag.search(text)
    tag = ''
    if tagSearch:
        tag = tagSearch.group('tag')
    return tag


def total_task():

    logging.warning("##################### task start ********************")

    doc_num = 0

    docs = fetch_unrunned_docs_by_date()
    # docs = fetch_unrunned_docs()
    url_title_lefturl_sourceSite_pairs = fetch_url_title_lefturl_pairs(docs)

    start_time, end_time, update_time, update_type, update_frequency = get_start_end_time(halfday=True)
    end_time = end_time + datetime.timedelta(days=-2)
    start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
    end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
    now = datetime.datetime.now()
    now_time = now.strftime('%Y-%m-%d %H:%M:%S')

    for url, title, lefturl, sourceSiteName in url_title_lefturl_sourceSite_pairs:
        # if sourceSiteName == "热点":
        #     print 1
        # else:
        #     continue
        # if url == "http://news.qq.com/a/20150901/009817.htm":
        #     print 1
        # else:
        #     continue
        # url = 'http://news.163.com/api/15/0830/10/B28SBIS200014AED_all.html'
        # title ='周恩来之侄出书:邓颖超曾透露总理去世真正原因'
        # lefturl = ''
        # sourceSiteName ='bing热点'
        doc_num += 1
        params = {"url":url, "title":title, "lefturl":lefturl, "sourceSiteName": sourceSiteName}
        try:

            print "*****************************task start, the url is %s, sourceSiteName: %s " \
                  "*****************************" % (url, sourceSiteName)
            do_ner_task(params)
            do_weibo_task(params)
            # do_event_task(params, end_time, now_time)
            do_zhihu_task(params)
            do_baike_task(params)
            do_douban_task(params)

            if sourceSiteName not in not_need_copy_content_news:
                is_content_ok = do_content_img_task(params)
                if is_content_ok:
                    do_relateimg_task(params)

                else:
                    logging.warn("content or img not ok, continue to copy next doc")
                    continue
            else:
                is_content_ok = True

            if  is_content_ok:
                is_abs_ok = do_abs_task(params)
                if not is_abs_ok:
                    continue

            do_isOnline_task(params)

        except (Timeout, ConnectionError) as e:
            print "timeout of url==>", url, "  exception==>", e
            continue

    logging.warning("##################### task complete ********************")
    if doc_num == 0:
        return "no_doc"
    else:
        return "have_doc"



def do_isOnline_task(params):

    print "==================isOnline task start================"

    url = params["url"]

    must_meet_field_list = ["weiboOk", "doubanOk", "zhihuOk", "baikeOk", "nerOk", "abstractOk", "contentOk"]

    isOk = is_condition_meet(url, must_meet_field_list)

    now = datetime.datetime.now()
    str_now = now.strftime("%Y-%m-%d %H:%M:%S")

    if isOk:
        set_googlenews_by_url_with_field_and_value(url, "isOnline", 1)
        set_googlenews_by_url_with_field_and_value(url, "updateTime", str_now)

        set_task_ok_by_url_and_field(url, "isOnline")
        print "isOnline ok"

    else:
        print "isOnline fail"



def is_condition_meet(url, must_meet_field_list):

    list_size = len(must_meet_field_list)

    meet_condition_num = 0
    doc = conn["news_ver2"]["Task"].find_one({"url": url})
    for key in must_meet_field_list:
        if key in doc.keys() and doc[key] == 1:
            meet_condition_num += 1

    if meet_condition_num == list_size:
        return True

    else:
        return False

def do_relateimg_task(params):

    print "==================do_relateimg_task start==============="
    url = params["url"]
    title = params["title"]

    relate = get_relate_news_by_url(url)

    handle_relate(url, relate)

    print "complete relate url,==>", url

def handle_relate(url, relate):

    keys = ["left", "middle", "bottom", "opinion", "deep_report"]
    for k in keys:
        doImgGetAndSave(k, relate, url)



def doImgGetAndSave(k, relate, url):

    if not relate:
        set_task_ok_by_url_and_field(url, "relateimgOk")
        print "relate is None, set task and leave"
        return

    sub_relate = relate[k]
    for e in sub_relate:
        if not "url" in e.keys():
            continue
        url_here = e["url"]
        img = GetImgByUrl(url_here)['img']

        if not img:
            sub_relate.remove(e)
            continue

        e["img"] = img

        apiUrl_text = "http://121.41.75.213:8080/extractors_mvc_war/api/getText?url=" + url_here
        r_text = requests.get(apiUrl_text)
        text = (r_text.json())["text"]
        e["text"] = text
        try:
            text=text.encode('utf-8')
        except:
            continue
        # text = text.replace(' ', '')

        try:
            gist = g().get_gist(text)
            # gist = fetch_gist_result(text)
        except:
            logging.warning("##################### gist_exception ********************")
            gist = Gist().get_gist_str(text)
        e["gist"] = gist
        compress = get_compression_result(gist)
        e["compress"] = compress

    try:
        set_googlenews_by_url_with_field_and_value(url, "relate."+k, sub_relate)
    except Exception:
        print "save relate." + k, " error, the url====> ", url
        return
    set_task_ok_by_url_and_field(url, "relateimgOk")


def fetch_gist_result(text):
    params_key = {"article": text.encode('utf-8')}
    data = urllib.urlencode(params_key)
    search_url = "http://121.40.34.56/news/baijia/fetchGist?" + data
    r_text = r.post(search_url)
    print repr(r_text)
    text = (r_text.json())
    return text



def get_relate_news_by_url(url):

    doc = conn["news_ver2"]["googleNewsItem"].find_one({"sourceUrl": url})

    relate = []

    if doc:
        if "relate" in doc:
            relate = doc["relate"]

    return relate


def do_douban_task(params):

    print "==================douban task start================"
    url = params["url"]
    title = params["title"]

    # tagUrl = "http://www.douban.com/tag/%s/?source=topic_search"
    tagUrl = "http://www.douban.com/search?cat=1019&q=%s"
    douban_tags = []
    tags = []
    ner = fetch_ne_by_url(url, all=True)

    if ner:
        tags = ner
    else:
        print "when get douan, the  ner is None, the url, title==>", url, "|| ", title

    for tag in tags:
        url_tag = isDoubanTag(tag)
        if url_tag :
            print "douban tag======>", tag
            # url_tag = tagUrl%tag
            tag_url_pairs = [tag, url_tag]
            douban_tags.append(tag_url_pairs)

    try:
        set_googlenews_by_url_with_field_and_value(url, "douban", douban_tags)
    except Exception as e:
        print "save douban tag error==>", e
        return

    set_task_ok_by_url_and_field(url, "doubanOk")


def isDoubanTag(tag):

    # url = "http://www.douban.com/tag/%s/?source=topic_search" % tag
    url = "http://www.douban.com/search?cat=1019&q=%s" % tag
    try:
        headers={'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36"}
        r = requests.get_tag(url, headers=headers)
        print "status code:", r.status_code
        if r.status_code != 200:
            print "error"
            return False
        # url_after = r.url.encode("utf-8")
        # url_after = urllib.unquote(url_after)
        #
        # if url_after == url:
        # r = requests.get(url)
        dom = etree.HTML(r.text)
        element_href = dom.xpath('//div[@class="result"]/div[@class="content"]/div[@class="title"]/descendant::a[@target="_blank"]/@href')[0]
        return element_href
    except Exception as e:
        print "douban tag request error==>", e
        return False
    return False


def do_baike_task(params):

    print "==================baike task start================"
    url = params["url"]
    title = params["title"]

    keyword = fetch_ne_by_url(url)

    if not keyword:
        set_task_ok_by_url_and_field(url, "baikeOk")
        print "keyword is None"
        return

    baike = parseBaike(keyword)

    if baike is None:
        set_task_ok_by_url_and_field(url, "baikeOk")
        return

    try:
        set_googlenews_by_url_with_field_and_value(url, "baike", baike)
    except Exception as e:
        print "save baike error", e
        return
    set_task_ok_by_url_and_field(url, "baikeOk")


def parseBaike(keyword):

    url = "http://baike.baidu.com/search/none?word=%s&pn=0&rn=10&enc=utf8" % keyword

    print "$$$$$$$$$$====>",url

    r = requests.get(url)

    # print ">>>>",type(r)

    r.encoding = 'utf-8'
    text = r.text

    text = text.replace('&', "")

    # print text

    dom =etree.HTML(text)
    # dom = soupparser.fromstring(text)
    try:
        element = dom.xpath('//dl[@class="search-list"]/descendant::a[@target="_blank"]')[0]

        element_href = dom.xpath('//dl[@class="search-list"]/descendant::a[@target="_blank"]/@href')[0]

        element_abstract = dom.xpath('//dl[@class="search-list"]/descendant::p[@class="result-summary"]')[0]


        raw_content = etree.tostring(element, encoding="utf-8")

        raw_content_abstract = etree.tostring(element_abstract, encoding="utf-8")

        pat = re.compile('<[^<>]+?>|&#13;|\\n')

        title = re.sub(pat, '', raw_content)

        url = element_href

        abstract = re.sub(pat, '', raw_content_abstract)

        result = {"title": title, "url": url, "abstract": abstract}

    except Exception:
        logging.warn("parse exception, keyword:"+keyword)
        result = None

    return result


def do_zhihu_task(params):


    url = params["url"]
    title = params["title"]

    print "=============zhihu task start==========="

    ner = None#fetch_ne_by_url(url)

    keyword = ''

    if ner:
        keyword = ner
    else:
        print "when get zhihu, the  ner is None, the url, title==>", url, "|| ", title
        keywords = extract_tags_helper(title)
        keyword = " ".join(keywords)

    zhihu = GetZhihu(keyword)

    set_task_ok_by_url_and_field(url, "zhihuOk")
    if zhihu is None:
        return
    set_googlenews_by_url_with_field_and_value(url, "zhihu", zhihu)


def GetZhihu(keyword):

    apiUrl = "http://www.zhihu.com/search?q={0}&type=question".format(keyword)

    r = requests.get(apiUrl)

    dom = etree.HTML(r.text)

    pat = re.compile('<[^<>]+?>')
    pat_user = re.compile('<[^<>]+?>|[\,，]')

    try:
        elements = dom.xpath('//li[@class="item clearfix"]')

    except Exception as e:

        print "zhihu page Parse error, the url is===>", apiUrl

        return None

    zhihus = []

    for element in elements:
        try:
            element_title = element.xpath('./div[@class="title"]/a')[0]

            raw_content_title = etree.tostring(element_title, encoding='utf-8')

            title = re.sub(pat, '', raw_content_title)

            # s = element.xpath('./div[@class="title"]/a[1]/@href')[0]

            url = "http://www.zhihu.com" + element.xpath('./div[@class="title"]/a[1]/@href')[0]

            user = element.xpath('.//a[@class="author"]/text()')[0]

            zhihu = {"title": title, "url": url, "user": user}

            zhihus.append(zhihu)
        except:
            continue

    return zhihus


def do_abs_task(params):
    url = params["url"]
    title = params["title"]
    sourceSiteName = params["sourceSiteName"]
    if sourceSiteName in not_need_copy_content_news:
        content = fetch_content_by_url(url)
        if not content:
            return False
        try:

            if sourceSiteName in ['观察者网','地球图辑队']:
                content = extract_text(content)
                content = trim_new_line_character(content)
                conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"content": content}})
            text = content
            if text:
                conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"text": text}})
                # print type(text)
            try:
                text=text.encode('utf-8')
            except:
                return False
            # text = text.replace(' ', '')
            # text = "".join(text.split('\n'))
            try:
                # gist = fetch_gist_result(text)
                gist = g().get_gist(text)
                print gist
            except:
                logging.warning("##################### gist_exception ********************")
                gist = Gist().get_gist_str(text)

            conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"gist": gist}})
            compress = get_compression_result(gist)
            conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"compress": compress}})
            # abstract_here = KeywordExtraction.abstract(content)
            # print ">>>>>>>>abstract:", abstract_here
            set_googlenews_by_url_with_field_and_value(url, "abstract", gist)
        except:
            return False

        set_task_ok_by_url_and_field(url, "abstractOk")
    else:
        gist = fetch_gist_by_url(url)
        if not gist:
            return False

        try:
            # abstract_here = KeywordExtraction.abstract(content)
            # print ">>>>>>>>abstract:", abstract_here
            # set_googlenews_by_url_with_field_and_value(url, "abstract", abstract_here)
            set_googlenews_by_url_with_field_and_value(url, "abstract", gist)
        except:
            return False

        set_task_ok_by_url_and_field(url, "abstractOk")

    return True


def extract_text(content):
    result = ''
    for content_elem in content:
        for content_elem_elem in content_elem:
            if 'txt' in content_elem_elem.keys():
                result =result + content_elem_elem['txt']

    return result




def fetch_ne_by_url(url,all=False):
    doc = conn["news_ver2"]["googleNewsItem"].find_one({"sourceUrl": url})
    ne = ''
    if doc:
        if "ne" in doc.keys():
            temp = doc["ne"]
            if all:
                ne = []
                ne = get_all_one_of_ne(temp)
            else:
                ne = ''
                ne = get_first_one_of_ne(temp)
        else:
            print 'Not found ne in ', url
    return ne




def get_first_one_of_ne(ne):

    keyword = ''
    if "person" in ne.keys() and len(ne['person']) > 0:
        keyword = ne['person'][0]

    elif "loc" in ne.keys() and len(ne['loc']) > 0:
        keyword = ne['loc'][0]

    elif "org" in ne.keys() and len(ne['org']) > 0:
        keyword = ne['org'][0]

    elif "gpe" in ne.keys() and len(ne['gpe']) > 0:
        keyword = ne['gpe'][0]

    return keyword


def get_all_one_of_ne(ne):

    keyword = []
    if "person" in ne.keys() and len(ne['person']) > 0:
        keyword.append(ne['person'][0])

    if "loc" in ne.keys() and len(ne['loc']) > 0:
        keyword.append(ne['loc'][0])

    if "org" in ne.keys() and len(ne['org']) > 0:
        keyword.append(ne['org'][0])

    if "gpe" in ne.keys() and len(ne['gpe']) > 0:
        keyword.append(ne['gpe'][0])

    return keyword



def fetch_content_by_url(url):

    doc = conn["news_ver2"]["googleNewsItem"].find_one({"sourceUrl": url})

    content = ''
    if doc:
        if "content" in doc.keys():
            content = doc["content"]

    return content

def fetch_gist_by_url(url):

    doc = conn["news_ver2"]["googleNewsItem"].find_one({"sourceUrl": url})

    gist = ''
    if doc:
        if "gist" in doc.keys():
            gist = doc["gist"]

    return gist



def do_content_img_task(params):

    print "do_content_img_task start "
    url = params["url"]
    title = params["title"]
    lefturl = params["lefturl"]

    apiUrl_text = "http://121.41.75.213:8080/extractors_mvc_war/api/getText?url=" + url
    r_text = requests.get(apiUrl_text)
    text = (r_text.json())["text"]
    if text:
        text = trim_new_line_character(text)
        if is_error_code(text) or not len(text)>10:
            return False
            # continue
    print text
    print type(text)
    try:
        text=text.encode('utf-8')
    except:
        return False
    # text = text.replace(' ', '')

    if text:
        conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"text": text}})
        try:
            gist = g().get_gist(text)
            # gist = fetch_gist_result(text)
        except:
            logging.warning("##################### gist_exception ********************")
            gist = Gist().get_gist_str(text)

        conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"gist": gist}})
        compress = get_compression_result(gist)
        conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"compress": compress}})

    content_status = conn["news_ver2"]["Task"].find_one({"url": url})
    if content_status:
        if content_status["contentOk"] == 1:
            return True

    if lefturl:
        url_use_to_fetch_content_img = lefturl
    else:
        print "left url is None, set it's img is None"
        set_googlenews_by_url_with_field_and_value(url, "imgUrls", "")
        set_task_ok_by_url_and_field(url, "isOnline") #标记为处理过， 接口取新闻会判断图片是否为空
        return False

    status = fetch_and_save_content(url, url_use_to_fetch_content_img)

    if status:
        set_task_ok_by_url_and_field(url, "contentOk")
        return True

    return False

def is_error_code(text):
    pattern = re.compile(ur'script')
    text = text.decode('utf-8')
    result = re.search(pattern, text)
    if result:
        return True
    else:
        return False


def trim_new_line_character(text):
    text_list = text.split('\n')
    result_list = []
    for text_elem in text_list:
        if not text_elem.strip():
            continue
        else:
            result_list.append(text_elem)

    return '\n'.join(result_list)+'\n'



def fetch_and_save_content(url, url_use_to_fetch_content_img):

    apiUrl_text = "http://121.41.75.213:8080/extractors_mvc_war/api/getText?url=" + url
    r_text = requests.get(apiUrl_text)
    text = (r_text.json())["text"]
    if text:
        text = trim_new_line_character(text)
    if url_use_to_fetch_content_img:
        img = GetImgByUrl(url_use_to_fetch_content_img)['img']
    else:
        img = ''

    if not img:
        print "url:%s" % url, " : img is None"
        return False

    if not text:
        print "url:%s" % url, " : text is None"
        return False

    conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"imgUrls": img, "content": text}})

    return True

def GetImgByUrl(url):

    result = {}
    apiUrl_img = "http://121.41.75.213:8080/extractors_mvc_war/api/getImg?url="+url
    r_img = requests.get(apiUrl_img)

    imgs = (r_img.json())["imgs"]


    if isinstance(imgs, list) and len(imgs) > 0:

        img_result = preCopyImg(url, imgs)

        # img_result = copyNormalImg(img_result)

        img_result = find_first_img_meet_condition(img_result)

        result['img'] = img_result.strip()
    else:
        result['img'] = ''

    return result


def preCopyImg(url, img_urls):

    img_result = []
    for result_i in img_urls:
        if result_i.startswith('/'):
            aa = url.find('/', 7)
            result_i = url[:aa] + result_i
            img_result.append(result_i)

        elif result_i.startswith('..'):
            count = 0
            while result_i.startswith('..'):
                count += 1
                result_i = result_i[3:]
            get_list = url.split('/')
            last_list = get_list[2:-1-count]
            result_i = get_list[0] + '//' + '/'.join(last_list) + '/' + result_i
            img_result.append(result_i)

        elif result_i.startswith('.'):
            get_list = url.split('/')
            last_list = get_list[2:-1]
            result_i = get_list[0] + '//' + '/'.join(last_list) + result_i[1:]
            img_result.append(result_i)

        elif re.search(r'^[^http://].*?([\w0-9]*?.jpg)',result_i):
            preurl=re.search(r'(http://.*/)',url)
            if preurl:
                url_result=preurl.group(1)
                url_result=url_result+result_i
                img_result.append(url_result)
        else:
            img_result.append(result_i)

    return img_result


def find_first_img_meet_condition(img_result):

    img_result = [x.encode('utf-8') for x in img_result]
    for i in img_result:
        time.sleep(3)
        if not i.endswith('.gif') and (not 'weima' in i) and (not ImgNotMeetCondition(i, 80000)) and  not is_exist_mongodb(i) and not is_erwei_ma(i):
            return i

    return ''

def is_exist_mongodb(img_url):
    img_url_pattern = img_url.split('/')[-1]
    doc = conn["news_ver2"]["googleNewsItem"].find_one({'imgUrls': re.compile(img_url_pattern)})
    if doc:
        return True
    else:
        return False

def is_erwei_ma(img_url):
    try:
        file = cStringIO.StringIO(urllib.urlopen(img_url).read())
        pil = Image.open(file).convert('L')
    except IOError:
        print "IOError, imgurl===>", img_url
        return True
    width, height = pil.size
    print width, height

    scanner = zbar.ImageScanner()
    scanner.parse_config('enable')




    raw = pil.tostring()
    # wrap image data
    image = zbar.Image(width, height, 'Y800', raw)
    # scan the image for barcodes
    scanner.scan(image)
    # extract results
    for symbol in image:
        # do something useful with results
        print 'decoded', symbol.type, 'symbol', '"%s"' % symbol.data

        if not symbol.type and not symbol.data:
            return False
        else:
            return True


def copyNormalImg(img_result):

    result = []
    for i in img_result:

        result.append(i)
        if i.endswith('.gif') or 'weima' in i or ImgNotMeetCondition(i, 40000):
            result.remove(i)
        else:
            return i

    if len(result) > 0:
        return result[0]
    else:
        return None

def ImgNotMeetCondition(url, size):

        img_url = url
        try:
            img_url = img_url.encode('utf-8')
            file = cStringIO.StringIO(urllib.urlopen(img_url).read())
            im = Image.open(file)
        except IOError:
            print "IOError, imgurl===>", img_url, "url ====>", url
            return True
        width, height = im.size
        print(width, height)
        if width * height <= size or not width_height_ratio_meet_condition(width, height, 4):
            return True
        print width, "+", height, " url=======>", img_url
        return False

def width_height_ratio_meet_condition(width, height, ratio):

    if width == 0 or height == 0:
        return False

    if width/height <= ratio and height/width <= ratio:
        return True

    return False


def do_ner_task(params):

    print "==================ner task start================"
    url = params["url"]
    title = params["title"]
    '''title_after_cut = jieba.cut(title, False)
    title_after_cut = [x.strip(':') and x.strip('：') and x.strip('-') for x in title_after_cut]
    title_after_cut = filter(None, title_after_cut)
    title_after_cut = " ".join(title_after_cut)'''
    title_after_cut = extract_tags_helper(title)
    title_after_cut = " ".join(title_after_cut)

    ne = getNe(title_after_cut)

    if ne:
        set_googlenews_by_url_with_field_and_value(url, "ne", ne)

    set_task_ok_by_url_and_field(url, "nerOk")

    return True


def is_ne_empty(ne):
    if ne.get('gpe', None):
        return False
    if ne.get('loc', None):
        return False
    if ne.get('org', None):
        return False
    if ne.get('person', None):
        return False
    if ne.get('time', None):
        return False
    return True


# need behind ner task
def do_event_task(params, start_time, end_time):
    print "==================event task start================"
    url = params["url"]
    title = params["title"]
    doc = conn["news_ver2"]["googleNewsItem"].find_one({"sourceUrl": url})

    if doc:

        '''
        if "ne" in doc.keys() and not is_ne_empty(doc['ne']):
            events = conn["news_ver2"]["googleNewsItem"].find({'$or': [{"ne.gpe": {'$in': doc['ne']['gpe']}},
                                                {"ne.person": {'$in': doc['ne']['person']}}], "createTime": {"$gte": start_time, '$lte': end_time}}).sort([("createTime", pymongo.DESCENDING)])

        else:'''

        #TODO may cause flipping , as tags contain ner
        tags = extract_tags_helper(title)
        set_googlenews_by_url_with_field_and_value(doc["sourceUrl"], "auto_tags", tags)
        re_tags = [re.compile(x) for x in tags]
        events = conn["news_ver2"]["googleNewsItem"].find({"title": {'$in': re_tags},
                            "createTime": {"$gte": start_time, '$lte': end_time}}).sort([("createTime", pymongo.DESCENDING)])
        domain_dict = {}


        events=filter_unrelate_news(events, doc)
        domain_dict = {-1:events}
        # if "text" not in doc.keys():
        #     return
        # for e in events:
        #     if "classes" not in e.keys():
        #         classes = get_category_by_hack(e['title'])
        #         if classes:
        #             e['classes'] = classes
        #             set_googlenews_by_url_with_field_and_value(e["sourceUrl"], "classes", classes)
        #     isCertain = False
        #     for class_elem in e['classes']:
        #         if class_elem['conf'] > 0.55:
        #             if class_elem['class_num'] in domain_dict:
        #                 domain_dict[class_elem['class_num']].append(e)
        #             else:
        #                 domain_dict[class_elem['class_num']] = [e]
        #             isCertain = True
        #             break
        #     if not isCertain:
        #         if -1 in domain_dict:
        #             domain_dict[-1].append(e)
        #         else:
        #             domain_dict[-1] = [e]

        for k, domain_events in domain_dict.iteritems():
            eventCount = 0
            top_story = ''
            if len(domain_events) < 2:
                continue
            for story in domain_events:
                if "eventId" in story.keys():
                    if "eventId_detail" in story.keys():
                        eventId_detail = story["eventId_detail"]
                    else:
                        eventId_detail = [story["eventId"]]
                    eventId_detail.append(url)
                    if "in_tag_detail" in story.keys():
                        in_tag_detail = story["in_tag_detail"]
                    else:
                        in_tag_detail = story["in_tag"]
                    in_tag_detail.append(",")
                    in_tag_detail.extend(tags)
                    # set_googlenews_by_url_with_field_and_value(story["sourceUrl"], "in_tag", tags)
                    # set_googlenews_by_url_with_field_and_value(story["sourceUrl"], "in_tag_detail", in_tag_detail)
                    # set_googlenews_by_url_with_field_and_value(story["sourceUrl"], "eventId", url)
                    # set_googlenews_by_url_with_field_and_value(story["sourceUrl"], "eventId_detail", eventId_detail)
                    #
                    # set_googlenews_by_url_with_field_and_value(story["sourceUrl"], "similarity", story["similarity"])
                    # set_googlenews_by_url_with_field_and_value(story["sourceUrl"], "unit_vec", story["unit_vec"])
                    # set_googlenews_by_url_with_field_and_value(story["sourceUrl"], "keyword", story["keyword"])
                    set_googlenews_by_url_with_field_and_value_dict(story["sourceUrl"],{"in_tag": tags
                                                                            , "in_tag_detail": in_tag_detail
                                                                            , "eventId": url
                                                                            , "eventId_detail": eventId_detail
                                                                            , "similarity": story["similarity"]
                                                                            , "unit_vec": story["unit_vec"]
                                                                            # , "keyword": story["keyword"]

                                                                              })



                else:

                #if story.get("eventId", None):  //TODO
                # if eventCount is 0:
                #     # set_googlenews_by_url_with_field_and_value(story["sourceUrl"], "eventId", story["_id"])
                #     set_googlenews_by_url_with_field_and_value(story["sourceUrl"], "eventId", story["_id"])
                #     # top_story = story["_id"]
                #     eventCount += 1
                #     continue
                    set_googlenews_by_url_with_field_and_value_dict(story["sourceUrl"],{"in_tag": tags
                                                                            , "in_tag_detail": tags
                                                                            , "eventId": url
                                                                            , "eventId_detail": [url]
                                                                            , "similarity": story["similarity"]
                                                                            , "unit_vec": story["unit_vec"]
                                                                            # , "keyword": story["keyword"]
                                                                              })

                # set_googlenews_by_url_with_field_and_value(story["sourceUrl"], "eventId", top_story)
                eventCount += 1

            duplicate_docs_check(domain_events)

            print 'found topic events count ===>' , eventCount



def filter_unrelate_news(events, compare_news):
    result = []
    if "text" not in compare_news.keys():
        return []
    paragraphIndex = 0
    content_dict = {}
    events_result = []
    for doc in events:
        if "text" in doc.keys():
            content = doc["text"]
        else:
            continue
        content_dict[str(paragraphIndex)] = content
        doc["paragraphIndex"] = str(paragraphIndex)
        events_result.append(doc)
        paragraphIndex += 1

    paragraphIndex_dict = find_Index_similar_with_compare_news(content_dict, {"doc":compare_news["text"]})

    for doc in events_result:
        if doc["paragraphIndex"] in paragraphIndex_dict.keys():
            doc["similarity"] = paragraphIndex_dict[doc["paragraphIndex"]]["similarity"]
            doc["unit_vec"] = paragraphIndex_dict[doc["paragraphIndex"]]["unit_vec"]
            doc["keyword"] = paragraphIndex_dict[doc["paragraphIndex"]]["keyword"]

            result.append(doc)
    return result



def do_weibo_task(params):

    print "==================weibo task start================"

    url = params["url"]
    title = params["title"]


    ner = None#fetch_ne_by_url(url)
    # if ner:
    #     keyword = ner
    # else:
    #     print "when get weibo, the  ner is None, the url, title==>", url, "|| ", title
    #     keywords = extract_tags_helper(title)
    #     keyword = "+".join(keywords)

    keyword = title
    weibo_ready = GetWeibo(keyword)

    if weibo_ready is None and ner:
        weibo_ready = GetWeibo(ner)

    if weibo_ready is None:
        set_task_ok_by_url_and_field(url, "weiboOk")
        print "there is no weibo of this news, the url and title is===>", url," || ", title

    else:
        set_googlenews_by_url_with_field_and_value(url, "weibo", weibo_ready)
        set_task_ok_by_url_and_field(url, "weiboOk")
        print "weiboTaskRun success, the doc url is:" + url

        # Update the comments by weibourl[str] or weibo_ready[{"url":url},]
        # Comments.get_comments_by_weibo_url(url, weiboUrl)
        Comments.get_comments_by_weibo_ready(url, weibo_ready)


def set_googlenews_by_url_with_field_and_value(url, field, value):
    conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {field: value}})


def set_task_ok_by_url_and_field(url, field):
    conn["news_ver2"]["Task"].update({"url": url}, {"$set": {field: 1}})


def GetWeibo(title):

    # weibos = weibo_relate_docs_get.search_relate_docs(title, 1)
    weibos = weibo_relate_docs_get.baidusearch_relate_docs(title,1)
    # weibos = json.loads(weibos)

    if isinstance(weibos, list) and len(weibos) <= 0:
        return

    if isinstance(weibos, dict) and "error" in weibos.keys():
        raise ConnectionError


    weibos_of_return = []

    for weibo in weibos:

        weibo_temp = {}
        # weibo_id = weibo["weibo_id"]
        # del weibo["weibo_id"]
        # # user = user_info_get.get_weibo_user(weibo_id)
        # # weibo["user"] = user["screenName"]
        # # weibo["profileImageUrl"] = user["profileImageUrl"]
        # weibo["user"] = ""
        # weibo["profileImageUrl"] = ""
        # weibo["sourceSitename"] = "weibo"
        # weibo["title"] = weibo["content"]
        # del weibo["content"]
        weibo_temp["user"] = weibo["source_name"]
        weibo_temp["title"] = replace_html(weibo["content"])
        weibo_temp["url"] = weibo["url"]
        weibo_temp["profileImageUrl"] = weibo["profile_image_url"]
        weibo_temp["sourceSitename"] = "weibo"
        weibo_temp["img"] = weibo["img_url"]
        weibo_temp["imgs"] = weibo["img_urls"]

        weibo_temp['like_count'] = weibo["like_count"]
        weibo_temp['comments_count'] = weibo["comments_count"]
        weibo_temp['reposts_count'] = weibo["reposts_count"]
        weibos_of_return.append(weibo_temp)

    # weibo = weibos[0]
    # weibo_id = weibo["weibo_id"]
    # user = user_info_get.get_weibo_user(weibo_id)
    # weibo["user"] = user["name"]

    if len(weibos_of_return) == 0:
        return None
    if len(weibos_of_return) > 8:
        return weibos_of_return[0:8]
    return weibos_of_return


def replace_html(s):
    s = s.replace('&quot;','"')
    s = s.replace('&amp;','&')
    s = s.replace('&lt;','<')
    s = s.replace('&gt;','>')
    s = s.replace('&nbsp;',' ')
    s = s.replace(' - 361way.com','')
    return s

def GetLastKeyWord(title):

    keywords = extract_tags_helper(title, 2)
    keyword = " ".join(keywords)

    ner = Getner(title)
    if ner and not ner in keywords:
        keyword = ner + " " + keyword

    return keyword, ner





def parseNerResult(json_r):
    times = []
    locs = []
    persons = []
    gpes = []
    orgs = []
    pat = re.compile('<[^<>]+?>')
    for t in json_r["misc"]:

        t = re.sub(pat, '', t)
        if t in g_time_filter or len(t) <= 2 or not isTime(t):
            continue
        times.append(t)

    for loc in json_r["loc"]:

        loc = re.sub(pat, '', loc)
        locs.append(loc)

    for person in json_r["person"]:

        person = re.sub(pat, '', person)
        persons.append(person)

    for gpe in json_r["gpe"]:

        gpe = re.sub(pat, '', gpe)
        if gpe in g_gpes_filter or len(gpe) <= 2:
            continue
        gpes.append(gpe)

    for org in json_r["org"]:

        org = re.sub(pat, '', org)
        orgs.append(org)


    ne = {"time": times, "gpe": gpes, "org": orgs, "person": persons, "loc": locs}

    return ne


def isTime(string):

    num = 0
    if '年' in string:
        num += 1

    if '月' in string:
        num += 1

    if '日' in string:
        num += 1

    if num >= 2:
        return True

    return False


def Getner(title):

    apiUrl = "http://%s:8080/ner_mvc/api/ner?sentence=" %(HOST_NER) + title

    r = requests.get(apiUrl)
    try:
        json_r = json.loads(r.text)
    except ValueError:
        return None

    if json_r["error_code"] != 0:
        return None

    keyword = ''
    ne = parseNerResult(json_r)

    if "person" in ne.keys() and len(ne['person']) > 0:
        keyword = ne['person'][0]

    elif "loc" in ne.keys() and len(ne['loc']) > 0:
        keyword = ne['loc'][0]

    elif "org" in ne.keys() and len(ne['org']) > 0:
        keyword = ne['org'][0]

    return keyword


def getNe(content_after_cut):

    print "content_after_cut", content_after_cut
    apiUrl = "http://%s:8080/ner_mvc/api/ner?sentence="%(HOST_NER) + content_after_cut

    r = requests.get(apiUrl)

    try:
        json_r = json.loads(r.text)
    except ValueError:
        return None

    if json_r["error_code"] != 0:
        return None

    ne = parseNerResult(json_r)

    return ne


def fetch_unrunned_docs():

    un_runned_docs = conn["news_ver2"]["Task"].find({"isOnline": 0}).sort([("updateTime", -1)])

    return un_runned_docs


def fetch_unrunned_docs_by_date(lastUpdate=False,isOnline=False,cluster=False,aggreSearchOk=False, update_direction=pymongo.ASCENDING):
    start_time, end_time, update_time, update_type, upate_frequency = get_start_end_time(halfday=True)
    start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
    end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
    if isOnline:
        if cluster:
            docs = conn["news_ver2"]["Task"].find({"isOnline": 1}).sort([("updateTime", pymongo.DESCENDING)]).limit(50)
        else:
            if aggreSearchOk:
                docs = conn["news_ver2"]["Task"].find({"isOnline": 1, "aggreSearchOk": {"$exists": 0}, "updateTime": {"$gte": start_time}}).sort([("updateTime", 1)])
            else:
                docs = conn["news_ver2"]["Task"].find({"isOnline": 1, "updateTime": {"$gte": start_time}}).sort([("updateTime", 1)])
        return docs

    if not lastUpdate:
        docs = conn["news_ver2"]["Task"].find({"isOnline": 0, "updateTime": {"$gte": end_time}}).sort([("updateTime", update_direction)])
        #docs = conn["news_ver2"]["Task"].find({"isOnline": 0, "updateTime": {"$gte": end_time}}).sort([("updateTime", pymongo.DESCENDING)])
    else:
        docs = conn["news_ver2"]["Task"].find({"isOnline": 1, "updateTime": {"$gte": start_time, '$lte': end_time}}).sort([("updateTime", 1)])
    return docs


def fetch_url_title_lefturl_pairs(docs):

    url_title_lefturl_sourceSite_pairs = []

    for doc in docs:
        url = doc["url"]

        relate_doc = get_googlenews_by_url(url)

        if not relate_doc:
            continue

        title = doc["title"]
        lefturl = ''
        sourceSiteName = ''

        if "originsourceSiteName" in relate_doc.keys():
            sourceSiteName = relate_doc["originsourceSiteName"]

        if "relate" in relate_doc.keys():
            relate = relate_doc['relate']
            if relate:
                left = relate_doc["relate"]["left"]
                if left and len(left) > 0:
                    lefturl = left[0]["url"]

        url_title_lefturl_sourceSite_pairs.append([url, title, lefturl, sourceSiteName])

    return url_title_lefturl_sourceSite_pairs


def get_googlenews_by_url(url):

    return conn["news_ver2"]["googleNewsItem"].find_one({"sourceUrl": url})


def recovery_old_event():
    docs = fetch_unrunned_docs_by_date(True)

    url_title_lefturl_sourceSite_pairs = fetch_url_title_lefturl_pairs(docs)

    for url, title, lefturl, sourceSiteName in url_title_lefturl_sourceSite_pairs:
        params = {"url":url, "title":title, "lefturl":lefturl, "sourceSiteName": sourceSiteName}
        start_time, end_time, update_time, update_type, update_frequency = get_start_end_time(halfday=True)
        start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
        end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
        now = datetime.datetime.now()
        now_time = now.strftime('%Y-%m-%d %H:%M:%S')
        print "*****************************task start, the url is %s, sourceSiteName: %s " \
                  "*****************************" % (url, sourceSiteName)
        #do_ner_task(params)
        do_event_task(params, start_time, end_time)



def find_Index_similar_with_compare_news(training_data, data_to_classify):
    # Load in corpus, remove newlines, make strings lower-case
    # if len(training_data) == 1 or not training_data:
    #     message = "The number of classes has to be greater than one; got 1 or 0."
    #     print message
    #     return
    docs = {}
    docs.update(training_data)
    docs.update(data_to_classify)
    names = docs.keys()
    keyword = list(extract_tags_helper(data_to_classify['doc']))
    preprocessed_docs = {}
    for name in names:
        preprocessed_docs[name] = list(jieba.cut(docs[name]))
    # Build the dictionary and filter out rare terms
    # Perform Chinese words segmentation.
    # dct = gensim.corpora.Dictionary(preprocessed_docs.values())
    dct = gensim.corpora.Dictionary([keyword])
    unfiltered = dct.token2id.keys()
    keyword = dct.token2id
    # no_below_num = 0.005*len(training_data)
    # dct.filter_extremes(no_below=no_below_num)
    filtered = dct.token2id.keys()
    # filtered_out = set(unfiltered) - set(filtered)


    # Build Bag of Words Vectors out of preprocessed corpus
    bow_docs = {}
    dense = {}
    for name in names:
        sparse = dct.doc2bow(preprocessed_docs[name])
        bow_docs[name] = sparse
        dense[name] = vec2dense(sparse, num_terms=len(dct))

    # # Build tfidf
    # tfidf = gensim.models.TfidfModel(bow_docs.values())
    # bow_docs_tfidf = {}
    # for name in names:
    #     bow_docs_tfidf[name] = tfidf[bow_docs[name]]


    # Dimensionality reduction using LSI. Go from 6D to 2D.
    # print "\n---LSI Model---"
    #
    # lsi_docs = {}
    # num_topics = 300
    # lsi_model = gensim.models.LsiModel(bow_docs_tfidf.values(),id2word=dct,
    #                                    num_topics=num_topics)
    # lsi_model = gensim.models.LsiModel(bow_docs_tfidf.values(),id2word=dct,
    #                                    num_topics=num_topics)


    # for name in names:
    #     vec = bow_docs[name]
    #     vec_tfidf = bow_docs_tfidf[name]
    #     sparse = lsi_model[vec_tfidf]
    #     # dense = vec2dense(sparse, num_topics)
    #     lsi_docs[name] = sparse

    # Normalize LSI vectors by setting each vector to unit length
    # print "\n---Unit Vectorization---"
    #
    unit_vec = {}
    #
    for name in names:

        vec = dense[name]
        norm = sqrt(sum(num ** 2 for num in vec))
        if norm<0.000001:
            norm = 1
        with np.errstate(invalid='ignore'):
            unit_vec[name] = [(num/norm) for num in vec]
        # if norm<0.000001:
        #     unit_vec[name] = [0.0] * len(vec)

    #     unit_vecs[name] = unit_vec
    # Take cosine distances between docs and show best matches
    # print "\n---Document Similarities---"

    # index = gensim.similarities.MatrixSimilarity(lsi_docs.values())
    # index = gensim.similarities.MatrixSimilarity(bow_docs_tfidf.values())
    # index = gensim.similarities.MatrixSimilarity(bow_docs.values())
    # print type(index)



    for i, name in enumerate(names):
        if name=="doc":
            paragraphIndex_dict = {}
            # paragraphIndex_list = []
            print "article_title,%s"%docs[name]
            # vec = lsi_docs[name]
            # vec = bow_docs_tfidf[name]
            vec = unit_vec[name]
            sims, same_word = calculate_sim(vec, names, unit_vec)

            # sims = index[vec]

            sims = sorted(sims.iteritems(), key=lambda d:d[1], reverse = True)
            # sims_names = sims.keys()
            keyword_num = len(keyword)
            keyword_num_muti = (keyword_num*0.2)
            # index=0
            for sims_elem in sims:
                if sims_elem[0]=="doc":
                    continue
                elif sims_elem[1]>=0.7 or (same_word[sims_elem[0]]>=keyword_num*0.2 and keyword_num>=10):
                    paragraphIndex_dict[sims_elem[0]] = { "similarity": sims_elem[1]
                                                         , "unit_vec" : unit_vec[sims_elem[0]]
                                                         , "keyword": keyword}


                    # paragraphIndex_list.append(sims_elem[0])
                    print "sims,%s"%sims_elem[0]
                    print "title,%s,sims,%10.3f"%(docs[sims_elem[0]], sims_elem[1])
                    print "same_word,%10.3f"%same_word[sims_elem[0]]
                    print "keyword_num,%10.3f"%keyword_num
                else:
                    continue
                    # print "sims,%s"%sims_elem[0]
                    # print "title,%s,sims,%10.3f"%(docs[sims_elem[0]], sims_elem[1])
                # index+=1
            break
        else:
            continue

    return paragraphIndex_dict

def vec2dense(vec, num_terms):
    '''Convert from sparse gensim format to dense list of numbers'''
    return list(gensim.matutils.corpus2dense([vec], num_terms=num_terms).T[0])

def calculate_sim(vec, names, unit_vec):
    sims={}
    sims_word={}
    for name in names:
        sims_value = sum([vec[i]*unit_vec[name][i] for i in range(len(vec))])
        same_word_num = sum([(1 if vec[i]>0 else 0)*(1 if unit_vec[name][i]>0 else 0) for i in range(len(vec))])
        sims_word[name] = same_word_num
        if same_word_num>=2:
            sims[name] = sims_value
        else:
            sims[name] = 0.0

    return sims,sims_word


def duplicate_docs_check(domain_events):
    events = []
    for event in domain_events:
        # if event["_id"] == 'http://nk.news.sohu.com/20150808/n418401792.shtml':
        #     print "1"
        if "sentence"  not in event.keys():
            text = event["text"]
            paragraph_list = text.split('\n')
            sentence_dict = {}
            sentence_cut_dict = {}
            paragraph_dict = {}
            i = 0
            for paragraph_elem in paragraph_list:
                if len(paragraph_elem)<=4:
                    continue
                sentence_dict[str(i)], sentence_cut_dict[str(i)] = extractSentenceBlock(paragraph_elem)
                paragraph_dict[str(i)] = paragraph_elem
                # result_dict[str(i)]
                i = i+1
            event["sentence"] = sentence_dict
            event["sentence_cut"] = sentence_cut_dict
            event["paragraph"] = paragraph_dict
            conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": event["_id"]}, {"$set": {"sentence": sentence_dict
                                                                                        , "sentence_cut": sentence_cut_dict
                                                                                        , "paragraph": paragraph_dict}})

        events.append(event)


    for event in events:

        main_event = event
        url = main_event["_id"]


        duplicate_result = {}
        result = {}
        for event_elem in events:
            if url == event_elem["_id"]:
                continue
            duplicate_result, result = compare_doc_is_duplicate(main_event, event_elem, duplicate_result, result)
        if len(duplicate_result) >0:
            conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"duplicate_check": duplicate_result}})

        common_opinion, self_opinion = extract_opinion(main_event,duplicate_result)
        event["self_opinion"] = self_opinion
        event["common_opinion"] = common_opinion

        duplicate_result_by_paragraph = compute_match_ratio_sentence_to_paragraph(result)
        min_match_ratio, one_paragraph_by_article, total_paragraph_by_article = extract_opinon_by_match_ratio(main_event, duplicate_result_by_paragraph)
        if min_match_ratio<0.39:
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


    for event in events:
        main_event = event
        url = main_event["_id"]
        result ={}
        result["self_opinion"] = []
        result["common_opinion"] = []
        for event_elem in events:
            if url == event_elem["_id"]:
                continue
            else:
                if len(event_elem["self_opinion"])>=20:
                    result["self_opinion"].append({"self_opinion": event_elem["self_opinion"], "url": event_elem["_id"], "title": event_elem["title"]})
                if len(event_elem["common_opinion"])>20:
                    result["common_opinion"].append({"common_opinion": event_elem["common_opinion"], "url": event_elem["_id"], "title": event_elem["title"]})

        conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"relate_opinion": result}})




def extract_opinion(main_event,result):
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
                    common_opinion=common_opinion + sentence_value +'。'
                    common_opinion_flag = True
                else:
                    self_opinion = self_opinion + sentence_value + '。'
                    self_opinion_flag = True

        else:
            for sentence_key in sorted(paragraph_value.keys()):
                sentence_value = paragraph_value[sentence_key]
                self_opinion = self_opinion + sentence_value+'。'
                self_opinion_flag = True
        if  self_opinion_flag:
            self_opinion = self_opinion + '\n'
        if  common_opinion_flag:
            common_opinion = common_opinion + '\n'

    return  common_opinion, self_opinion

    # for paragraph_key, paragraph_value in sentence.items():
    #     if paragraph_key in result.keys():
    #         for sentence_key, sentence_value in paragraph_value.items():
    #             if sentence_key in result[paragraph_key].keys():
    #                 common_opinion=common_opinion + sentence_value +'。'
    #             else:
    #                 self_opinion = self_opinion + sentence_value + '。'
    #     else:
    #         for sentence_key, sentence_value in paragraph_value.items():
    #             self_opinion=self_opinion+sentence_value+'。'
    # return  common_opinion, self_opinion

def extract_opinon_by_match_ratio(main_event, duplicate_result_by_paragraph):
    total_paragraph_by_article = {}
    one_paragraph_by_article = ''
    paragraph = main_event["paragraph"]
    min_match_ratio = 1
    min_paragraph_key = '0'
    title = main_event["title"]
    tags = extract_tags_helper(title)

    for paragraph_key, paragraph_value in paragraph.items():
        total_paragraph_by_article[paragraph_key] = {}
        total_paragraph_by_article[paragraph_key]["content"] = paragraph[paragraph_key]
        if paragraph_key in duplicate_result_by_paragraph.keys():
            total_paragraph_by_article[paragraph_key]["match_ratio"] = duplicate_result_by_paragraph[paragraph_key]
        else:
            total_paragraph_by_article[paragraph_key]["match_ratio"] = 1
        if  total_paragraph_by_article[paragraph_key]["match_ratio"] < min_match_ratio and is_normal_info(paragraph[paragraph_key]) and is_tags_in_paragraph(tags, paragraph[paragraph_key]):
            min_match_ratio = total_paragraph_by_article[paragraph_key]["match_ratio"]
            min_paragraph_key = paragraph_key
            print "min_paragraph_key_change"

    one_paragraph_by_article = paragraph[min_paragraph_key]


    return min_match_ratio,one_paragraph_by_article, total_paragraph_by_article



def is_normal_info(paragraph):
    paragraph = paragraph.decode('utf-8')
    pattern=re.compile(ur'http[:：]|[[【]|[]】]|扫描二维码|来源[:：]|编辑[:：]|作者[:：]|发布[:：]|正文已结束|字号[:：]|未经授权禁止转载')
    result = re.search(pattern, paragraph)
    if result:
        return False
    else:
        return True

def is_tags_in_paragraph(tags,paragraph):
    for tag in tags:
        if tag in paragraph:
            return True

    return False


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
    url = event_elem["_id"]


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
                    match_ratio = 1
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



    return duplicate_result, result






def extractSentenceBlock(doc):
    SENTENCE_SEP=re.compile(ur'[。\n!！]')
    result = {}
    result_cut = {}
    doc_array=re.split(SENTENCE_SEP, doc.encode('utf8').decode("utf8"))
    i = 0
    for elem in doc_array:
        if len(elem)<=5:
            continue
        result[str(i)] = elem.strip()
        keyword = set()
        keyword = {word for word in jieba.cut_with_stop(elem.strip())}
        keyword_list = list(keyword)
        result_cut[str(i)] = keyword_list
        # result.append(elem.strip())
        i = i + 1
    return result, result_cut


# text is the string to be pre-processed, regex is the regular expression(s).
def text_preprocess(raw_sentence):
    regex = ur"[,|，].*称[,|，]|“|”| |‘|’|《|》|%|\[|]|-|·"
    text = raw_sentence
    pre_processed_txt = re.sub(regex, normalize_orders, text)
    return pre_processed_txt


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
        #Get last text segment of a sentence as last comma encountered


def get_last_sen_seg(sen=''):
    # last_sen_seg = sen.split('，')[-1]
    print type(sen)
    print type(sen.decode("utf8"))
    last_sen_seg = re.split(ur",|，|，", sen.decode("utf8"))[-1]    #",|，|，" sen.encode('utf8').decode("utf8")
    return last_sen_seg
def get_compression_result(raw_sentence):
    raw_sentence = unicode(raw_sentence)
    refined_text = text_preprocess(raw_sentence)
    get_last_sen = get_last_sen_seg(refined_text)
    sentence_ready_to_compress = get_last_sen
    if len(refined_text) <= 12:
        return refined_text

    try:
        compr_result = requests.get("http://60.28.29.37:8080/SentenceCompressor?sentence=" + sentence_ready_to_compress)
        compr_result = (compr_result.json())
        return compr_result["result"]
    except:
        return get_last_sen
    return get_last_sen


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
    search_url ="http://192.168.0.37:8083/search?"+data
    # search_url ="http://60.28.29.37:8083/search?"+data
    try:
        r_text = r.get(search_url)
        text = (r_text.json())
        search_list = text["searchItems"]
    # try:

    # r_text = r.get(searchUrl_text)
    # except:
    #     print "search_url_exception"
    #     return
    except:
        print "search_url_exception"
        return
    search_doc_num = 0
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
        if len(img)==0:
            try:
                img = GetImgByUrl(search_url)['img']

            except:
                print "img_exception"
                continue
        # if not img:
        #     print "url:%s" % search_url, " : img is None"
        #     continue
        if not text:
            print "url:%s" % search_url, " : text is None"
            continue

        # print type(str(search_title))

        result_elem["_id"] = search_url
        if "img" in params.keys():
            result_elem["originsourceSiteName"] = "bing热点"
        else:
            result_elem["originsourceSiteName"] = "热点"
        # result_elem["updateTime"] = getDefaultTimeStr()
        updateTime = time_match(search_url)
        if updateTime[0:4]<>'2015':
            print "updateTime year no equal 2015"
            print "updateTime,%s"%updateTime
            print "sourceUrl,%s"%search_url
            continue
        result_elem["updateTime"] = updateTime
        print "updateTime,%s"%updateTime
        result_elem["sourceUrl"] = search_url
        result_elem["description"] = ""
        result_elem["title"] = replace_html(str(search_title))
        result_elem["relate"] = {}
        result_elem["sourceSiteName"] = "百家热点"
        result_elem["createTime"] = getDefaultTimeStr()
        result_elem["channel"] = "融合搜索"
        result_elem["root_class"] = "40度"
        if len(url)>0:
            result_elem["relate_url"] = url
        result_elem["keyword"] = str(topic)
        result_elem["imgUrls"] = img
        result_elem["content"] = text
        result_elem["text"]= text
        result_elem["category"] = "热点"
        title = result_elem['title']
        titleItem={'title': search_title}

        imgUrlsItem={'imgUrls': img}

        if "img" in params.keys():
            if conn["news_ver2"]["googleNewsItem"].find_one(imgUrlsItem):
                logging.warn("Item %s imgUrls alread exists in  database " %(result_elem['_id']))
                break

        if conn["news_ver2"]["googleNewsItem"].find_one(titleItem):
            logging.warn("Item %s alread exists in  database " %(result_elem['_id']))
            continue


        if conn["news_ver2"]["Task"].find_one({'url': search_url}):
            logging.warn("Item %s alread exists in  database " %(result_elem['_id']))
            continue

        print "google_news_save_start"
        conn["news_ver2"]["googleNewsItem"].save(dict(result_elem))
        print "google_news_save_end"
        search_doc_num = search_doc_num + 1




        Task = {}
        Task['url'] = search_url
        Task['title'] = search_title
        Task['updateTime'] = getDefaultTimeStr()
        Task['sourceSiteName'] = '百家'
        Task['weiboOk']=0
        Task['zhihuOk']=0
        Task['abstractOk']=0
        Task['nerOk']=0
        Task['baikeOk']=0
        Task['baiduSearchOk']=0
        Task['doubanOk']=0
        Task['relateImgOk']=0
        Task['isOnline']=0
        if "img" in params.keys() or len(img)>0:
            Task['contentOk'] = 1
            conn["news_ver2"]["Task"].save(dict(Task))
            break
        else:
            Task['contentOk'] = 0
            conn["news_ver2"]["Task"].save(dict(Task))
        if search_doc_num >= 6:
            break


def getDefaultTimeStr():
    format='%Y-%m-%d %H:%M:%S'
    timeDelta=datetime.timedelta(milliseconds=3600*1000)
    defaultTime=(datetime.datetime.now()-timeDelta)
    defaultTimeStr=defaultTime.strftime(format)
    return defaultTimeStr

def trim_bracket(title):
    print "title,%s"%title
    bracket_pat=re.compile(r'\(.*?\)')
    title=re.sub(bracket_pat, '', title)
    bracket_pat_1=re.compile(r'（.*?）')
    title=re.sub(bracket_pat_1, '', title)
    bracket_pat_2=re.compile(r'【.*?】')
    title=re.sub(bracket_pat_2, '', title)
    bracket_pat_3=re.compile(r'[.*?]')
    title=re.sub(bracket_pat_3, '', title)
    return title


def set_googlenews_by_url_with_field_and_value_dict(url, condition_dict):

    conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set":
                                                                        {"in_tag": condition_dict["in_tag"],
                                                                         "in_tag_detail": condition_dict["in_tag_detail"],
                                                                         "eventId": condition_dict["eventId"],
                                                                         "eventId_detail": condition_dict["eventId_detail"],
                                                                         "similarity": condition_dict["similarity"],
                                                                         "unit_vec": condition_dict["unit_vec"]
                                                                         # "keyword": condition_dict["keyword"]
                                                                         }
                                                               })


def test_extract_tags():
    print " ".join(extract_tags_helper("网易网络受攻击影响巨大损失或超1500万"))
    print " ".join(extract_tags_helper("工信部:多措并举挖掘宽带\"提速降费\"潜力"))
    print " ".join(extract_tags_helper("爆料称Apple Watch迎重磅更新：大量新功能"))
    print " ".join(extract_tags_helper("携程遭超长宕机：内部数据管理恐存严重漏洞"))
    print " ".join(extract_tags_helper("携程系统大规模崩溃或源自内部管理失控"))
    print " ".join(extract_tags_helper("印度总理莫迪晒与李克强自拍照"))
    print " ".join(extract_tags_helper("【原油收盘】美油微跌0.6美元破60关口，供应过剩阴魂不散"))
    print " ".join(extract_tags_helper("《何以笙箫默》武汉校园之旅黄晓明险被女粉丝'胸咚'"))
    print " ".join(extract_tags_helper("《何以笙箫默》《何以笙箫默2》武汉校园之旅黄晓明险被女粉丝'胸咚'"))
    print " ".join(extract_tags_helper("杨幂否认拍不雅视频公公:很多人照她的样子整形"))
    print " ".join(extract_tags_helper("刘强东与奶茶妹妹的婚纱照冲淡了翻新手机的丑闻?"))
    print " ".join(extract_tags_helper("港媒:复旦校庆宣传片被指抄东大校友称不可原谅"))
    print " ".join(extract_tags_helper("复旦宣传片事件暴露大学危机应对机制缺失"))
    print " ".join(extract_tags_helper("10人候选全国道德模范"))
    print " ".join(extract_tags_helper("原标题：北京朝阳一铲车撞上绿化带司机当场死亡"))
    print " ".join(extract_tags_helper("俄外交部：俄期望能按期就伊朗核计划达成协议"))
    print " ".join(extract_tags_helper("媒体盘点：李克强出访拉美带来的签证便利"))
    print " ".join(extract_tags_helper("《哆啦A梦》四天揣走2.37亿影迷为'蓝胖子'舍钞票"))
    print " ".join(extract_tags_helper("河南将整治人员密集场所消防安全重查彩钢板建筑"))
    print " ".join(extract_tags_helper("国产厂商转战799元价位手机或将迎来降价潮"))
    print " ".join(extract_tags_helper("美媒曝FBI正在调查布拉特被捕人员将提供线索"))
    print " ".join(extract_tags_helper("重庆应急避难场所达2500万平米拥有400余支应急队伍"))
    print " ".join(extract_tags_helper("广州市越秀区一养老院违规用彩钢板"))
    print " ".join(extract_tags_helper("南阳开展消防安全大检查拆除违规彩钢板建筑22处"))
    print " ".join(extract_tags_helper("重庆应急避难所可容1200万人高空救援设备不足"))
    print " ".join(extract_tags_helper("阿里在中国最美公路旁边建了一个数据中心"))



if __name__ == '__main__':

    # if False != width_height_ratio_meet_condition(100, 900, 4):
    #     print "width_height_ratio_meet_condition test fail"
    # else:
    #     print "width_height_ratio_meet_condition test ok"

    # find_first_img_meet_condition(["http://i3.sinaimg.cn/dy/main/other/qrcode_news.jpg"])
    #recovery_old_event()

    # is_exist_mongodb('http://ent.people.com.cn/NMediaFile/2015/0430/MAIN201504301328396563201369173.jpg')
    # isDoubanTag('战机')
    # isDoubanTag('首次')
    # isDoubanTag('刘翔')
    # do_douban_task({'url':'http://sports.dbw.cn/system/2015/05/10/056499871.shtml','title':"亚冠16强对阵出炉东亚“三国杀”韩国围中日"})

    #parseBaike('安培晋三')
    #test_extract_tags()
    # start_time, end_time, update_time, update_type, update_frequency = get_start_end_time(halfday=True)
    # start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
    # end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
    # now = datetime.datetime.now()
    # now_time = now.strftime('%Y-%m-%d %H:%M:%S')
    # do_event_task({'url':"http://www.techweb.com.cn/internet/2015-08-03/2184133.shtml", 'title':"王思聪cj被拦路人狂笑"}, start_time, end_time)
    # fetch_and_save_content('http://news.southcn.com/international/content/2015-06/14/content_126321942.htm','http://news.southcn.com/international/content/2015-06/14/content_126321942.htm')

    # start_time, end_time, update_time, update_type, update_frequency = get_start_end_time(halfday=True)
    # end_time = end_time + datetime.timedelta(days=-2)
    # start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
    # end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
    # now = datetime.datetime.now()
    # now_time = now.strftime('%Y-%m-%d %H:%M:%S')
    # do_event_task({'url':"http://www.jfdaily.com/tiyu/bw/201508/t20150803_1723010.html", 'title':"哈萨克斯坦总统祝贺北京申奥成功"}, end_time, now_time)

    # text = "<script type=\"text/javascript\"> var m=Math.random(); document.write('<script type=\"text/javascript\" src=\"http://cast.ra.icast.cn/p/?id=2084&rnd='+m+'\"><\\/script>'); </script> <script> var timestamp = Date.parse(new Date()); var src = \"http://statistic.dvsend.china.com/cc/00S4K?adcrm?v=\"+timestamp; var s = document.createElement(\"SCRIPT\"); document.getElementsByTagName(\"HEAD\")[0].appendChild(s); s.src = src; </script>\n<script type=\"text/javascript\"> /*内页通发流媒体300*250 创建于 2015-04-02*/ var cpro_id = \"u2024173\"; </script> <script src=\"http://cpro.baidustatic.com/cpro/ui/f.js\" type=\"text/javascript\"></script> <script> var timestamp = Date.parse(new Date()); var src = \"http://statistic.dvsend.china.com/cc/00UYZ?adcrm?v=\"+timestamp; var s = document.createElement(\"SCRIPT\"); document.getElementsByTagName(\"HEAD\")[0].appendChild(s); s.src = src; </script>\n<!--<script type=\"text/javascript\">//<![CDATA[ ac_as_id = 2384; ac_click_track_url = \"\";ac_format = 0;ac_mode = 1; ac_width = 280;ac_height = 210; //]]></script> <script type=\"text/javascript\" src=\"http://static.acs86.com/g.js\"></script> <script> var timestamp = Date.parse(new Date()); var src = \"http://statistic.dvsend.china.com/cc/00W54?adcrm?v=\"+timestamp; var s = document.createElement(\"SCRIPT\"); document.getElementsByTagName(\"HEAD\")[0].appendChild(s); s.src = src; </script>-->\n"

    # text ='''<script type="text/javascript"> var m=Math.random(); document.write('<script type="text/javascript" src="http://cast.ra.icast.cn/p/?id=2084&rnd='+m+'"><\/script>'); </script> <script> var timestamp = Date.parse(new Date()); var src = "http://statistic.dvsend.china.com/cc/00S4K?adcrm?v="+timestamp; var s = document.createElement("SCRIPT"); document.getElementsByTagName("HEAD")[0].appendChild(s); s.src = src; </script><script type="text/javascript"> /*内页通发流媒体300*250 创建于 2015-04-02*/ var cpro_id = "u2024173"; </script> <script src="http://cpro.baidustatic.com/cpro/ui/f.js" type="text/javascript"></script> <script> var timestamp = Date.parse(new Date()); var src = "http://statistic.dvsend.china.com/cc/00UYZ?adcrm?v="+timestamp; var s = document.createElement("SCRIPT"); document.getElementsByTagName("HEAD")[0].appendChild(s); s.src = src; </script><script type="text/javascript"> mx_as_id =3006801; mx_server_base_url ="mega.mlt01.com/"; </script> <script type="text/javascript" src="http://static.mlt01.com/b.js"></script> <script> var timestamp = Date.parse(new Date()); var src = "http://statistic.dvsend.china.com/cc/00W2W?adcrm?v="+timestamp; var s = document.createElement("SCRIPT"); document.getElementsByTagName("HEAD")[0].appendChild(s); s.src = src; </script>'''

    # keyword = list(extract_tags_helper(text))
    # is_normal_info("2015-08-12 08:47:32  | 来源：")
    # is_error_code('scriptdddd')
    # do_search_task({"url":'http://www.guancha.cn/society/2015_08_19_331204.shtml', "title":'天津爆炸最新消息：瑞海操控人看守所透露公司“政商关系网”'})
    # print trim_bracket("夏克立否认夏天退出爸爸3 暂由夫人黄嘉千替代(图)")
    # gist = fetch_gist_result(r"8月23日上午9时许，位于上海展览中心的上海书展人头攒动，一位身着米白色休闲西装的老人，在讲台台阶旁的轮椅上安静坐着。 老人白白瘦瘦，看着却特别精神。当主持人向台下观众作完介绍，观众才发现，在一旁静坐良久的老人正是这场签售会的主角。他是周恩来的侄子、86岁的周尔鎏先生。 周尔鎏带来的是他的新书，由中央文献出版社出版的《我的七爸周恩来》。 周尔鎏的祖父与周恩来的父亲是嫡堂兄弟，分别属于家族里的二房和七房。因长房无后，周尔鎏的祖父就过继给长房而成为周家的大家长，周尔鎏即成为周家的长房长孙。两家不仅同时从绍兴举家迁往淮安定居，并且同居一宅，不分彼此。 周尔鎏1929年出生在上海，“我出生不久生母就离世了，那时我家在上海北四川路永安里44号（现已定为周恩来早期革命遗址），七爸和七妈在我家隐蔽时，我还不到1岁，他们对我百般呵护。从我牙牙学语时，就遵嘱称他们‘七爸’、‘七妈’。” 他口中的七爸正是周恩来，七妈则是邓颖超。 新书首次披露独家史料 1939年至1942年间，周尔鎏的父亲和继母等家人分别去了重庆和苏北，只留他一人在上海读书，后来被周恩来戏称为“孤岛孤儿”。1946年，周恩来通过时任《文汇报》经理张振邦先生几经辗转找到了周尔鎏，“以后我就由七爸七妈直接抚养”。 周恩来夫妇对周尔鎏不仅在生活上给予支持和帮助，也对他之后的工作和思想产生了极大影响。 据周尔鎏介绍，周恩来是中国理学开山鼻祖之一周敦颐的第33世孙，作为周氏始祖的后人，更作为家庭成员中的杰出代表，周恩来早年就因周敦颐而深感自豪并以之为人生楷模。 “七爸作为周敦颐家族的后人，一生信奉其先祖所倡导的‘以诚为本’。”周尔鎏在书中写道，“他任职世界人口最多的大国总理26年之久，始终做到廉洁自持，一尘不染，这是当时全中国人民乃至全世界人民都有目共睹或耳熟能详的历史事实。” 周尔鎏年轻时曾经入伍当兵，后进入南开大学学习，毕业后曾任中联部副局长、对外文委（文化部）司长、北京大学副校长、中国驻英使馆文化参赞、中国社会发展研究中心主任等职。 “由于历史巧遇和工作安排，常常是继总理政治出访某些国家后，我便随后陪同文化代表团出访该国。在国内，我也常陪外宾去总理视察过的地方和单位参观。为此，七爸曾戏称我对他是‘亦步亦趋，步我后尘’。” 周尔鎏说，有关周恩来的许多资料迄今未曾面世，自己深感有责任在有生之年将这些宝贵史料披露出来。“书中内容或许有助于增进国内外对周恩来总理的全面了解，有助于周恩来研究工作的推进。” 在周氏后人中，读者较早看到的是周恩来侄女周秉德的回忆录，周尔鎏认为，自己和周秉德因“经历和年龄差别，当年的事她并不知晓”。 这部20余万字的新书分为《周氏家世》《爱宝与七爸七妈》《建国风云》《文革岁月》《永远的怀念》《史实的订补与澄清》《秉承遗训》七个部分。新书首次公布了诸多独家史料，包括周恩来曾先留学英国后留学法国，“伍豪事件”前后周恩来躲藏在周尔鎏的出生地上海，周恩来生前最后的枕边书、内心的家族愿望，以及从建国到“文革”，周恩来在家人面前流露的思想看法等。 “周元棠是七爸的高祖，他对七爸的影响是迄今为止罕为人知的。”周尔鎏在书中写道。 周元棠生于1791年，卒于1851年，“生前著述甚多，但因战乱，身后仅有一卷《海巢书屋诗稿》留存。这卷诗稿所录诗作均是周元棠22岁之前所写。” 周尔鎏在书中披露，正是这卷收录135首诗作的诗稿，被周恩来珍藏在床头枕下阅读多年，伴随他历经“文革”的十年浩劫，直到他离开人世。 周尔鎏认为，周恩来幼年生长在淮安，此后相继在辽宁、天津求学，后来更是辗转南北，但他对祖居地??绍兴的乡恋深情始终未变，对当地的风物景致、文化习俗甚为了解，这除了周恩来的博闻强识并曾专程到过绍兴外，和他研读高祖周元棠的诗作获取独特的感受不无关系。 “元棠公生前虽遭遇家道衰落，但他一生甘守清贫，始终秉持高洁操守。”周尔鎏认为，周元棠《自述》诗作中“当作奇男子”的铮铮铁骨之言，迄今仍然令周氏后人有读其佳句如见其人的感受。 周恩来在1917年9月从天津南开东渡日本，在出发前曾写下诗篇《大江歌罢掉头东》：大江歌罢掉头东，邃密群科济世穷。面壁十年图破壁，难酬蹈海亦英雄。 周尔鎏感慨，青年时代周恩来为拯救中华而愿献出一切的豪迈气概，与元棠公“当作奇男子”的铮铮铁骨是何等的相似。 再如《海巢书屋诗稿》中的《留侯》，“提到自古以来真正的可以称作豪杰的历史人物并不多见，往往不是过于刚直就是过于压抑自己，真正能够文武全才刚柔并济的英雄人物‘总以识高见才力’。” 周尔鎏发现，周元棠在无意中还成了一位预言家，“七爸非凡而又曲折艰辛的一生，于百余年后全面验证了元棠公的预示，也同时验证了中华民族传统文化强大的生命力。” “从一个没落的封建大家庭中走出来的周恩来，最终成为世人公认的智勇兼备、文武双全、刚柔并济的伟大政治家，与家族传承不无关系。因此，七爸一生珍藏这一诗集也就不足为奇了，他经常反复研读这些诗篇，从中得到激励或抚慰，也是可以想见的。”周尔鎏写道。 出身大家庭的周恩来曾打算退休后写一部名为《房》的长篇小说。周恩来告诉周尔鎏，这一小说的内容就是根据大家庭的许多“房”的不同历史演变，作为中国社会的缩影加以描述。然而这一愿望最终未能实现。 “文革”初期跟不上 周尔鎏认为，“文革”初期，周恩来也感觉“跟不上”。 他在书中写道，1965年，毛泽东提出“整党内走资本主义道路的当权派”，又向地方一些领导人说：“中央出了修正主义你们怎么办？”可以说这是危险的提示，实际上，毛泽东已经发出了准备发动“文化大革命”的重要信号。 另一方面，周尔鎏认为，当时的周恩来“只是感到毛泽东同其他中央领导的分歧可能愈加厉害，并未料到这场异乎寻常的政治大动乱即将来临”。 1965年11月，上海《文汇报》突然发表了姚文元的文章《评新编历史剧〈海瑞罢官〉》，对剧作者、时任北京市副市长吴晗进行公开点名批判。 “七爸当时对此事一无所知，他同意彭真的意见：吴晗问题是学术问题而不是政治问题，学术问题要坚持‘百花齐放、百家争鸣’的方针。”周尔鎏写道。 1965年5月25日，在康生、曹轶欧夫妇的策划下，北京大学哲学系聂元梓等七人贴出“大字报”??《宋硕、陆平、彭?云在文化大革命中究竟干些什么？》，攻击北京大学党委和北京市搞修正主义，遭到许多师生和员工的批驳。 周尔鎏回忆，由于北京大学有几十个国家的留学生，七爸指示：北大搞运动一定要慎重，注意内外有别。大字报贴出以后，七爸连夜派中共中央华北局、国务院外办和高教部的负责人到该校，批评聂元梓等人违反中央规定的原则，搞乱了中央的部署，并重申要严格遵守内外有别的中央指示。 几日后，毛泽东指示康生、陈伯达，将该大字报由新华社全文广播，并在全国各地报刊发表。 “当晚，陈毅询问七爸：‘这么大的举动，为什么事先不通知？’七爸回答道：‘我本人也只是临近广播前才接到康生电话，告我该大字报内容由中央台向全国播出。 1974年，邓颖超曾和周尔鎏有一次特别的谈话。 “1974年春天，七爸不仅是重病缠身，同时他在政治上还处于一个危难的时刻，七妈避开周围耳目，单独嘱咐我配合他们作最坏的准备。” 周尔鎏感到，这次谈话在某种意义上讲，是七爸七妈对他的最后嘱咐。 这一次谈话，周尔鎏在书中形容为“特别的谈话”。 他在书中回忆，“1974年的这次谈话，七妈避开秘书和身边工作人员秘密地打电话约我个别见面。她用了很长的时间让我详尽地汇报‘文革’以来我的遭遇和表现，看来她对我的情况早就有所了解。” 周尔鎏向邓颖超谈到康生和江青后，邓颖超说道，“至于你提到康生，他称外事口的工作不仅是‘三和一少’（对帝国主义和，对修正主义和，对各国反动派和，对支持民族解放运动少），甚至无限上纲为‘三降一灭’（投降帝国主义、投降现代修正主义、投降反动派和消灭民族解放运动），你说他将矛头除明显指向王稼祥同志外还指向七爸这是对的。‘四人帮’也是这样，我们没法跟别人讲，这次就要跟你讲彻底。江青她就是反你七爸的，看来是狼子野心，有点不达目的不罢休的意思。” “总理已染重病在身，居然还受到这种恶毒的污蔑和攻击，你作为侄儿并且一度是外事口的干部，对你七爸非常了解，对这样极不公正合理的遭遇当时是会感到义愤的。其实不仅如此，这不幸的遭遇也可能会降临到你和你的家庭，这也是七爸让我再次特地召见你的原因之一，希望你预作最坏的准备……北京的形势如何，七爸的病情如何发展都很难说。”周尔鎏在书中回忆邓颖超的谈话。 多年后，邓颖超向周尔鎏讲述了周恩来去世的真正原因。")
    # print gist
    # replace_html("四川&quot;老板&quot;配手机监控乞丐 乞者报警获解救】9月5日，在四川达州张家湾行乞的一名残疾人用手机报警表示“我是被迫行乞”。据报警的行乞残疾人称，")
    # replace_html("广州女白领&quot;卖晚安&quot;赚3千元 短信1元1条")
    while True:
        doc_num = total_task()
        if doc_num == "no_doc":
            time.sleep(60)

    # GetWeibo("孙楠 歌手")





