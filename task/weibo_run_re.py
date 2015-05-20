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
except ImportError:
    import user_info_get
    import weibo_relate_docs_get
    from utils import get_start_end_time, is_number
    print "import error"

from abstract import KeywordExtraction

conn = pymongo.MongoReplicaSetClient("h44:27017, h213:27017, h241:27017", replicaSet="myset",
                                                             read_preference=ReadPreference.SECONDARY)
HOST_NER = "60.28.29.47"

not_need_copy_content_news = ["网易新闻图片", "观察者网"]


g_time_filter = ["今天","明天","后天"]
g_gpes_filter = ["中国"]

def extract_tags_helper(sentence, topK=20, withWeight=False):
    tags = []
    for eng in re.findall(r'[A-Za-z ]+',sentence):
        if len(eng) > 2:
            tags.append(eng)
    tags.extend(extract_tags(sentence, topK, withWeight, allowPOS=('ns', 'n', 'nr')))
    tags = [x for x in tags if not is_number(x)]
    tags = [x for x in tags if not x in g_gpes_filter and not x in g_time_filter]
    return tags


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

            if is_content_ok:
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
    tags = []
    ner = fetch_ne_by_url(url, all=True)

    if ner:
        tags = ner
    else:
        print "when get douan, the  ner is None, the url, title==>", url, "|| ", title

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
        r = requests.get_tag(url, headers=headers)
        print "status code:", r.status_code
        if r.status_code != 200:
            print "error"
            return False
        url_after = r.url.encode("utf-8")
        url_after = urllib.unquote(url_after)

        if url_after == url:
            return True
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



def do_content_img_task(params):

    print "do_content_img_task start "
    url = params["url"]
    title = params["title"]
    lefturl = params["lefturl"]

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




def fetch_and_save_content(url, url_use_to_fetch_content_img):

    apiUrl_text = "http://121.41.75.213:8080/extractors_mvc_war/api/getText?url=" + url
    r_text = requests.get(apiUrl_text)
    text = (r_text.json())["text"]

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
    title_after_cut = jieba.cut(title)
    title_after_cut = [x.strip(':') and x.strip('：') and x.strip('-') for x in title_after_cut]
    title_after_cut = filter(None, title_after_cut)
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

        eventCount = 0
        topStory = ''

        if "ne" in doc.keys() and not is_ne_empty(doc['ne']):
            events = conn["news_ver2"]["googleNewsItem"].find({'$or': [{"ne.gpe": {'$in': doc['ne']['gpe']}},
                                                {"ne.person": {'$in': doc['ne']['person']}}], "createTime": {"$gte": start_time, '$lte': end_time}}).sort([("createTime", pymongo.DESCENDING)])

        else:
            #TODO may cause flipping , as tags contain ner
            tags = extract_tags_helper(title)
            re_tags = [re.compile(x) for x in tags]
            events = conn["news_ver2"]["googleNewsItem"].find({"title": {'$in': re_tags},
                                "createTime": {"$gte": start_time, '$lte': end_time}, "eventId": {'$exists': False}}).sort([("createTime", pymongo.DESCENDING)])

        for story in events:
            #if story.get("eventId", None):  //TODO
            if eventCount is 0:
                set_googlenews_by_url_with_field_and_value(url, "eventId", story["_id"])
                topStory = story["_id"]
            set_googlenews_by_url_with_field_and_value(story["sourceUrl"], "eventId", topStory)
            eventCount += 1
        print 'found topic events count ===>' , eventCount


def do_weibo_task(params):

    print "==================weibo task start================"

    url = params["url"]
    title = params["title"]


    ner = None#fetch_ne_by_url(url)
    if ner:
        keyword = ner
    else:
        print "when get weibo, the  ner is None, the url, title==>", url, "|| ", title
        keywords = extract_tags_helper(title)
        keyword = " ".join(keywords)

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
        weibo_temp["profileImageUrl"] = ''
        weibo_temp["sourceSitename"] = "weibo"
        weibo_temp["img"] = weibo["img_url"]
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

if __name__ == '__main__':

    # if False != width_height_ratio_meet_condition(100, 900, 4):
    #     print "width_height_ratio_meet_condition test fail"
    # else:
    #     print "width_height_ratio_meet_condition test ok"

    # find_first_img_meet_condition(["http://i3.sinaimg.cn/dy/main/other/qrcode_news.jpg"])
    #recovery_old_event()
    '''print " ".join(extract_tags_helper("网易网络受攻击影响巨大损失或超1500万"))
    print " ".join(extract_tags_helper("工信部:多措并举挖掘宽带\"提速降费\"潜力"))
    print " ".join(extract_tags_helper("爆料称Apple Watch迎重磅更新：大量新功能"))
    print " ".join(extract_tags_helper("印度总理莫迪晒与李克强自拍照"))
    print " ".join(extract_tags_helper("【原油收盘】美油微跌0.6美元破60关口，供应过剩阴魂不散"))
    print " ".join(extract_tags_helper("《何以笙箫默》武汉校园之旅黄晓明险被女粉丝'胸咚'"))
    print " ".join(extract_tags_helper("杨幂否认拍不雅视频公公:很多人照她的样子整形"))'''
    # is_exist_mongodb('http://ent.people.com.cn/NMediaFile/2015/0430/MAIN201504301328396563201369173.jpg')
    # isDoubanTag('战机')
    # isDoubanTag('首次')
    # isDoubanTag('展示')
    # do_douban_task({'url':'http://sports.dbw.cn/system/2015/05/10/056499871.shtml','title':"亚冠16强对阵出炉东亚“三国杀”韩国围中日"})

    #parseBaike('安培晋三')

    while True:
        doc_num = total_task()
        if doc_num == "no_doc":
            time.sleep(60)

    # GetWeibo("孙楠 歌手")




