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
from requests.exceptions import Timeout

reload(sys)
sys.setdefaultencoding('utf8')

arg = sys.path[0].split('/')
path_add = arg[:-1]
path_add = '/'.join(path_add)

sys.path.append(path_add+"/weibo/")
sys.path.append(path_add)
try:
    from weibo import weibo_relate_docs_get, user_info_get
except ImportError:
    import weibo_relate_docs_get
    import user_info_get

from abstract import KeywordExtraction

conn = pymongo.MongoReplicaSetClient("h44:27017, h213:27017, h241:27017", replicaSet="myset",
                                                             read_preference=ReadPreference.SECONDARY)
HOST_NER="60.28.29.47"


def total_task():

    docs = fetch_unrunned_docs()

    url_title_lefturl_sourceSite_pairs = fetch_url_title_lefturl_pairs(docs)

    for url, title, lefturl, sourceSiteName in url_title_lefturl_sourceSite_pairs:
        params = {"url":url, "title":title, "lefturl":lefturl, "sourceSiteName": sourceSiteName}
        try:

            print "==================task start, the url is %s, sourceSiteName: %s ============================================" % (url, sourceSiteName)
            do_weibo_task(params)
            do_ner_task(params)
            do_zhihu_task(params)
            do_baike_task(params)
            do_douban_task(params)

            if sourceSiteName != "网易新闻图片":
                is_content_ok = do_content_img_task(params)
                do_relateimg_task(params)
            else:
                is_content_ok = True

            if is_content_ok:
                is_abs_ok = do_abs_task(params)
                if not is_abs_ok:
                    continue

            do_isOnline_task(params)

        except Timeout:
            print "timeout of url==>", url
            continue

def do_isOnline_task(params):

    print "==================isOnline task start================"

    url = params["url"]

    must_meet_field_list = ["weiboOk", "doubanOk", "zhihuOk", "baikeOk", "nerOk", "abstractOk", "contentOk"]

    isOk = is_condition_meet(url, must_meet_field_list)

    if isOk:
        set_googlenews_by_url_with_field_and_value(url, "isOnline", 1)



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

    tagUrl = "http://www.douban.com/tag/%s/?source=topic_search"
    douban_tags = []

    tags = extract_tags(title)

    for tag in tags:
        if isDoubanTag(tag):
            print "douban tag======>", tag
            url_tag = tagUrl%tag
            tag_url_pairs = [tag, url_tag]
            douban_tags.append(tag_url_pairs)

    try:
        set_googlenews_by_url_with_field_and_value(url, "douban", douban_tags)
    except Exception as e:
        print "save douban tag error==>", e
        return

    set_task_ok_by_url_and_field(url, "doubanOk")



def isDoubanTag(tag):

    url = "http://www.douban.com/tag/%s/?source=topic_search" % tag
    try:
        headers={'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36"}
        r = requests.get(url, headers=headers)
        print "status code:", r.status_code

        url_after = r.url.encode("utf-8")
        url_after = urllib.unquote(url_after)

        if url_after == url:
            return True
    except:
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
        element = dom.xpath('//div[@class="mod-list"]/descendant::a[@target="_blank"]')[0]

        element_href = dom.xpath('//div[@class="mod-list"]/descendant::a[@target="_blank"]/@href')[0]

        element_abstract = dom.xpath('//div[@class="mod-list"]/descendant::div[@class="abstract"]')[0]


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

    ner = fetch_ne_by_url(url)

    keyword = ''

    if ner:
        keyword = ner
    else:
        print "when get zhihu, the  ner is None, the url, title==>", url, "|| ", title
        keywords = extract_tags(title, 2)
        keyword = "".join(keywords)

    zhihu = GetZhihu(keyword)

    set_task_ok_by_url_and_field(url, "zhihuOk")
    if zhihu is None:
        return
    set_googlenews_by_url_with_field_and_value(url, "zhihu", zhihu)









def GetZhihu(keyword):

    apiUrl = "http://www.zhihu.com/search?q={0}&type=question".format(keyword)

    r = requests.get(apiUrl)

    dom =etree.HTML(r.text)

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

    content = fetch_content_by_url(url)

    if not content:
        return False

    abstract_here = KeywordExtraction.abstract(content)
    print ">>>>>>>>abstract:", abstract_here

    try:
        set_googlenews_by_url_with_field_and_value(url, "abstract", abstract_here)
    except:
        return False

    set_task_ok_by_url_and_field(url, "abstractOk")

    return True




def fetch_ne_by_url(url):
    doc = conn["news_ver2"]["googleNewsItem"].find_one({"sourceUrl": url})

    ne = ''
    if doc:
        if "ne" in doc.keys():
            temp = doc["ne"]
            ne = get_first_one_of_ne(temp)

    return ne

def get_first_one_of_ne(ne):

    keyword = ''
    if "person" in ne.keys() and len(ne['person']) > 0:
        keyword = ne['person'][0]

    elif "loc" in ne.keys() and len(ne['loc']) > 0:
        keyword = ne['loc'][0]

    elif "org" in ne.keys() and len(ne['org']) > 0:
        keyword = ne['org'][0]

    return keyword

def fetch_content_by_url(url):

    doc = conn["news_ver2"]["googleNewsItem"].find_one({"sourceUrl": url})

    content = ''
    if doc:
        if "content" in doc.keys():
            content = doc["content"]

    return content



def do_content_img_task(params):

    print "do_content_img_task start "
    url = params["url"]
    title = params["title"]
    lefturl = params["lefturl"]

    if lefturl:
        url_use_to_fetch_content_img = lefturl
    else:
        url_use_to_fetch_content_img = url

    status = fetch_and_save_content(url, url_use_to_fetch_content_img)

    if status:
        set_task_ok_by_url_and_field(url, "contentOk")
        return True

    return False




def fetch_and_save_content(url, url_use_to_fetch_content_img):

    apiUrl_text = "http://121.41.75.213:8080/extractors_mvc_war/api/getText?url=" + url_use_to_fetch_content_img
    r_text = requests.get(apiUrl_text)
    text = (r_text.json())["text"]

    img = GetImgByUrl(url)['img']

    if not img:
        print "url:%s" % url, " : img is None"
        return False

    if not text:
        print "url:%s" % url, " : text is None"
        return False

    conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"imgUrls": img, "content": text}})

    return True

def GetImgByUrl(url):

    apiUrl_img = "http://121.41.75.213:8080/extractors_mvc_war/api/getImg?url="+url

    r_img = requests.get(apiUrl_img)

    imgs = (r_img.json())["imgs"]

    result = {}

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


    for i in img_result:
        if not i.endswith('.gif') and (not 'weima' in i) and (not ImgNotMeetCondition(i, 40000)):
            return i

    return ''


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
        if width * height <= size:
            return True
        print width, "+", height, " url=======>", img_url
        return False


def do_ner_task(params):

    print "==================ner task start================"
    url = params["url"]
    title = params["title"]
    title_after_cut = jieba.cut(title)
    title_after_cut = " ".join(title_after_cut)

    ne = getNe(title_after_cut)

    if ne:
        set_googlenews_by_url_with_field_and_value(url, "ne", ne)

    set_task_ok_by_url_and_field(url, "nerOk")

    return True


def do_weibo_task(params):

    print "==================weibo task start================"

    url = params["url"]
    title = params["title"]

    keyword, ner = GetLastKeyWord(title)

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


def set_googlenews_by_url_with_field_and_value(url, field, value):
    conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {field: value}})


def set_task_ok_by_url_and_field(url, field):
    conn["news_ver2"]["Task"].update({"url": url}, {"$set": {field: 1}})


def GetWeibo(title):

    weibos = weibo_relate_docs_get.search_relate_docs(title, 1)

    weibos = json.loads(weibos)

    if isinstance(weibos, list) and len(weibos) <= 0:
        return

    if isinstance(weibos, dict) and "error" in weibos.keys():
        raise ConnectionError


    weibos_of_return = []
    for weibo in weibos:
        weibo_id = weibo["weibo_id"]
        del weibo["weibo_id"]
        # user = user_info_get.get_weibo_user(weibo_id)
        # weibo["user"] = user["screenName"]
        # weibo["profileImageUrl"] = user["profileImageUrl"]
        weibo["user"] = ""
        weibo["profileImageUrl"] = ""
        weibo["sourceSitename"] = "weibo"
        weibo["title"] = weibo["content"]
        del weibo["content"]
        weibos_of_return.append(weibo)

    # weibo = weibos[0]
    # weibo_id = weibo["weibo_id"]
    # user = user_info_get.get_weibo_user(weibo_id)
    # weibo["user"] = user["name"]

    return weibos_of_return


def GetLastKeyWord(title):

    keywords = extract_tags(title, 2)
    keyword = " ".join(keywords)

    ner = Getner(title)
    if ner and not ner in keywords:
        keyword = ner + " " + keyword

    return keyword, ner


def parseNerResult(json_r):

    time_filter = ["今天","明天","后天"]
    times = []
    locs = []
    persons = []
    gpes = []
    orgs = []
    pat = re.compile('<[^<>]+?>')
    for t in json_r["misc"]:

        t = re.sub(pat, '', t)
        if t in time_filter or len(t) <= 2 or not isTime(t):
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

    apiUrl = "http://121.41.75.213:8080/ner_mvc/api/ner?sentence=" + title

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

    un_runned_docs = conn["news_ver2"]["Task"].find({"weiboOk": 0}).sort([("updateTime", -1)])

    return un_runned_docs


def fetch_url_title_lefturl_pairs(docs):

    url_title_lefturl_sourceSite_pairs = []

    for doc in docs:
        url = doc["url"]
        title = doc["title"]
        lefturl = ''
        sourceSiteName = ''
        if "relate" in doc.keys():
            left = doc["relate"]["left"]
            if len(left) > 0:
                lefturl = left[0]["url"]

        if "sourceSiteName" in doc.keys():
            sourceSiteName = doc["sourceSiteName"]


        url_title_lefturl_sourceSite_pairs.append([url, title, lefturl, sourceSiteName])

    return url_title_lefturl_sourceSite_pairs


if __name__ == '__main__':
    while True:
        time.sleep(40)
        total_task()