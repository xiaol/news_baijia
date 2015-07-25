#coding=utf-8

from jieba.analyse import extract_tags
import jieba
import pymongo
from pymongo.read_preferences import ReadPreference
import json
from requests.exceptions import ConnectionError
import requests_with_sleep as requests
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
from analyzer import jieba

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
sys.path.append(path_add)
try:
    from weibo import weibo_relate_docs_get, user_info_get
    from controller.utils import get_start_end_time, is_number
    from weibo import Comments
except ImportError:
    import user_info_get
    import weibo_relate_docs_get
    from utils import get_start_end_time, is_number
    import Comments
    print "import error"

from abstract import KeywordExtraction
from para_sim.TextRank4ZH.gist import Gist



conn = pymongo.MongoReplicaSetClient("h44:27017, h213:27017, h241:27017", replicaSet="myset",
                                                             read_preference=ReadPreference.SECONDARY)
HOST_NER = "60.28.29.47"

not_need_copy_content_news = ["网易新闻图片", "观察者网"]


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

    for url, title, lefturl, sourceSiteName in url_title_lefturl_sourceSite_pairs:

        doc_num += 1
        params = {"url":url, "title":title, "lefturl":lefturl, "sourceSiteName": sourceSiteName}
        start_time, end_time, update_time, update_type, update_frequency = get_start_end_time(halfday=True)
        end_time = end_time + datetime.timedelta(days=-2)
        start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
        end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
        now = datetime.datetime.now()
        now_time = now.strftime('%Y-%m-%d %H:%M:%S')
        try:

            print "*****************************task start, the url is %s, sourceSiteName: %s " \
                  "*****************************" % (url, sourceSiteName)
            do_ner_task(params)
            do_weibo_task(params)
            do_event_task(params, end_time, now_time)
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
        gist = Gist().get_gist_str(text)
        e["gist"] = gist

    try:
        set_googlenews_by_url_with_field_and_value(url, "relate."+k, sub_relate)
    except Exception:
        print "save relate." + k, " error, the url====> ", url
        return
    set_task_ok_by_url_and_field(url, "relateimgOk")

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
            abstract_here = KeywordExtraction.abstract(content)
            print ">>>>>>>>abstract:", abstract_here
            set_googlenews_by_url_with_field_and_value(url, "abstract", abstract_here)
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
    if text:
        conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"text": text}})
        gist = Gist().get_gist_str(text)
        conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"gist": gist}})

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

        result['img'] = img_result
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
        # domain_dict = {'1', events}
        if "text" not in doc.keys():
            return
        for e in events:
            if "classes" not in e.keys():
                classes = get_category_by_hack(e['title'])
                if classes:
                    e['classes'] = classes
                    set_googlenews_by_url_with_field_and_value(e["sourceUrl"], "classes", classes)
            isCertain = False
            for class_elem in e['classes']:
                if class_elem['conf'] > 0.55:
                    if class_elem['class_num'] in domain_dict:
                        domain_dict[class_elem['class_num']].append(e)
                    else:
                        domain_dict[class_elem['class_num']] = [e]
                    isCertain = True
                    break
            if not isCertain:
                if -1 in domain_dict:
                    domain_dict[-1].append(e)
                else:
                    domain_dict[-1] = [e]

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
                                                                            , "keyword": story["keyword"]

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
                                                                            , "keyword": story["keyword"]
                                                                              })

                # set_googlenews_by_url_with_field_and_value(story["sourceUrl"], "eventId", top_story)
                eventCount += 1

            duplicate_docs_check(domain_events)

            print 'found topic events count ===>' , eventCount

def filter_unrelate_news(events, compare_news):
    result = []
    if "text" not in compare_news.keys():
        return events
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
        weibo_temp["title"] = weibo["content"]
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


def fetch_unrunned_docs_by_date(lastUpdate=False, update_direction=pymongo.ASCENDING):
    start_time, end_time, update_time, update_type, upate_frequency = get_start_end_time(halfday=True)
    start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
    end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')


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

        if "sourceSiteName" in doc.keys():
            sourceSiteName = doc["sourceSiteName"]

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
            sims = calculate_sim(vec, names, unit_vec)

            # sims = index[vec]

            sims = sorted(sims.iteritems(), key=lambda d:d[1], reverse = True)
            # sims_names = sims.keys()

            # index=0
            for sims_elem in sims:
                if sims_elem[0]=="doc":
                    continue
                elif sims_elem[1]>=0.6:
                    paragraphIndex_dict[sims_elem[0]] = { "similarity": sims_elem[1]
                                                         , "unit_vec" : unit_vec[sims_elem[0]]
                                                         , "keyword": keyword}

                    # paragraphIndex_list.append(sims_elem[0])
                    print "sims,%s"%sims_elem[0]
                    print "title,%s,sims,%10.3f"%(docs[sims_elem[0]], sims_elem[1])
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
    for name in names:
        sims_value = sum([vec[i]*unit_vec[name][i] for i in range(len(vec))])
        same_word_num = sum([(1 if vec[i]>0 else 0)*(1 if unit_vec[name][i]>0 else 0) for i in range(len(vec))])
        if same_word_num>=2:
            sims[name] = sims_value
        else:
            sims[name] = 0.0

    return sims


def duplicate_docs_check(domain_events):
    events = []
    for event in domain_events:

        if "sentence" not in event.keys():
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
        result = {}
        for event_elem in events:
            if url == event_elem["_id"]:
                continue
            result = compare_doc_is_duplicate(main_event, event_elem, result)
        if len(result) >0:
            conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"duplicate_check": result}})


def compare_doc_is_duplicate(main_event, event_elem,result):
    sentence_cut = main_event["sentence_cut"]
    paragraph = event_elem["paragraph"]
    url = event_elem["_id"]


    for paragraph_key, paragraph_value in sentence_cut.items():
        for sentence_key, sentence_value in paragraph_value.items():
            top_match_ratio = 0.0
            top_match_paragraph_id = "-1"
            keyword_num = len(sentence_value)
            if keyword_num <=5:
                continue
            for compare_paragraph_key , compare_paragraph_value in paragraph.items():
                match_num = 0
                for sentence_keyword in sentence_value:
                    compare_result = compare_paragraph_value.find(sentence_keyword)
                    if compare_result >= 0:
                        match_num = match_num + 1
                match_ratio = match_num / (keyword_num * 1.0)
                if match_ratio > top_match_ratio:
                    top_match_ratio = match_ratio
                    top_match_paragraph_id = compare_paragraph_key
            if top_match_ratio > 0.8:
                if paragraph_key not in result.keys():
                    result[paragraph_key] = {}
                if sentence_key not in result[paragraph_key].keys():
                    result[paragraph_key][sentence_key] = []
                    result[paragraph_key][sentence_key] = [{"url": url, "paragraph_id": top_match_paragraph_id, "match_ratio": top_match_ratio}]
                else:
                    result[paragraph_key][sentence_key].append([{"url": url, "paragraph_id": top_match_paragraph_id, "match_ratio": top_match_ratio}])
    return result






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


def set_googlenews_by_url_with_field_and_value_dict(url, condition_dict):

    conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set":
                                                                        {"in_tag": condition_dict["in_tag"],
                                                                         "in_tag_detail": condition_dict["in_tag_detail"],
                                                                         "eventId": condition_dict["eventId"],
                                                                         "eventId_detail": condition_dict["eventId_detail"],
                                                                         "similarity": condition_dict["similarity"],
                                                                         "unit_vec": condition_dict["unit_vec"],
                                                                         "keyword": condition_dict["keyword"]
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
    '''start_time, end_time, update_time, update_type, update_frequency = get_start_end_time(halfday=True)
    start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
    end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
    now = datetime.datetime.now()
    now_time = now.strftime('%Y-%m-%d %H:%M:%S')
    do_event_task({'url':"http://tech.caijing.com.cn/20150608/3900634.shtml", 'title':"阿里在中国最美公路旁边建了一个数据中心"}, start_time, end_time)'''
    # fetch_and_save_content('http://news.southcn.com/international/content/2015-06/14/content_126321942.htm','http://news.southcn.com/international/content/2015-06/14/content_126321942.htm')
    while True:
        doc_num = total_task()
        if doc_num == "no_doc":
            time.sleep(60)

    # GetWeibo("孙楠 歌手")






