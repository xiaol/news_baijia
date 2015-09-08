#coding=utf-8
from jieba.analyse import extract_tags
import jieba
import pymongo
from pymongo.read_preferences import ReadPreference
import json
from requests.exceptions import ConnectionError
import requests_with_sleep as requests
import re
import subprocess
import time
import lxml.etree as etree
import lxml.html
import sys
import logging
import os
from PIL import Image
import datetime
from requests.exceptions import Timeout
from weibo_run_re import set_googlenews_by_url_with_field_and_value, do_search_task


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
    import weibo_relate_docs_get
    import user_info_get
    from utils import get_start_end_time, is_number

from abstract import KeywordExtraction
# from AI_funcs.Doc_Clustering.doc_clustering import doc_cluster, doc_similarity
import jieba
import gensim
from math import sqrt
import numpy as np
import math
from config import dbConn

from weibo_run_re import fetch_unrunned_docs_by_date, fetch_url_title_lefturl_pairs, do_event_task
from controller.home_get import homeContentFetch

g_time_filter = ["今天","明天","后天"]
g_gpes_filter = ["中国"]

def extract_tags_helper(sentence, topK=20, withWeight=False):
    tags = extract_tags(sentence, topK, withWeight, allowPOS=('ns', 'n', 'nr'))
    tags = [x for x in tags if not is_number(x)]
    tags = [x for x in tags if not x in g_gpes_filter and not x in g_time_filter]
    return tags

conn = pymongo.MongoReplicaSetClient("h44:27017, h213:27017, h241:27017", replicaSet="myset",
                                                             read_preference=ReadPreference.SECONDARY)
mapOfSourceName = {"weibo":"微博"}

HOST_NER="60.28.29.47"

# Task : 微博获取任务，定时获取数据，存到mongo
def weiboTaskRun():

    # un_runned_docs = conn["news_ver2"]["Task"].find().sort([("updateTime", -1)])
    un_runned_docs = conn["news_ver2"]["Task"].find({"weiboOk": 0}).sort([("updateTime", -1)])

    success_num = 0

    url_title_pairs = []
    for doc in un_runned_docs:
        # url = doc["url"]
        url = doc["url"]
        title = doc["title"]
        url_title_pairs.append([url, title])

    for url, title in url_title_pairs:


        keyword, ner = GetLastKeyWord(title)

        try:
            weibo_ready = GetWeibo(keyword)
        except ConnectionError,Timeout:
            continue

        if weibo_ready is None and ner:

            try:
                weibo_ready = GetWeibo(ner)
            except ConnectionError, Timeout:
                continue

        if weibo_ready is None:

            conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"weiboOk": 1}})
            print "there is no weibo of this news, the url and title is===>", url," || ", title

        if weibo_ready is not None:

            try:
                conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"weibo": weibo_ready}})
            except Exception as e:
                print "weiboTaskRun save weibo fail, the doc url is:", url
                continue

            conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"weiboOk": 1}})

            success_num += 1
            print "weiboTaskRun success, the doc url is:" + url, "sucess num:", success_num

def GetLastKeyWord(title):

    keywords = extract_tags(title, 2)
    keyword = " ".join(keywords)

    ner = Getner(title)
    if ner and not ner in keywords:
        keyword = ner + " " + keyword

    return keyword, ner


def GetWeibo(title):

    # if one:
    weibos = weibo_relate_docs_get.search_relate_docs(title, 1)
    # else:
    #     weibos = weibo_relate_docs_get.search_relate_docs(title, 7)

    weibos = json.loads(weibos)

    # for weibo in weibos:
    #     weibo_id = weibo["weibo_id"]
    #     userinfo = user_info_get(weibo_id)

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


# Task : 命名实体识别， 定时分析mongo中新 新闻的命名实体识别
def nerTaskRun():

    un_runned_docs = conn["news_ver2"]["Task"].find({"nerOk":0}).sort([("updateTime", -1)])   #OK 大写
    # un_runned_docs = conn["news_ver2"]["Task"].find().sort([("updateTime", -1)])
    index = 0

    url_title_pairs = []
    for doc in un_runned_docs:
        url = doc["url"]
        title = doc["title"]
        url_title_pairs.append([url, title])


    for url, title in url_title_pairs:

        title_after_cut = jieba.cut(title)

        title_after_cut = " ".join(title_after_cut)

        try:
            ne = getNe(title_after_cut)
        except Timeout:
            continue

        #ner 有问题，跳过
        if not ne:
            conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"nerOk": 1}})
            continue

        try:
            conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"ne": ne}})
        except:
            print "ne set fail, the doc url is===> ", url
            continue

        conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"nerOk": 1}})
        index += 1
        print "ne set success, the doc url is:", url, "num===> ", index

def fetch_and_save_content_by_url(url):

    print "get content for url====>", url
    apiUrl_text = "http://121.41.75.213:8080/extractors_mvc_war/api/getText?url="

    apiUrl_text += url

    r_text = requests.get(apiUrl_text)
    text = (r_text.json())["text"]
    img = GetImgByUrl(url)['img']

    if not img:
        print "when do ner task, img or text is None"

        img = CopyImgAfterFail(url)   #取左侧图片

        if not img:
            return False

    if not text:
        return False

    try:
        conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"imgUrls": img, "content": text}})
    except Exception as e:
        print ">>>>>>>>save content error", e, "the url is :", url
        return None

    return True

def CopyImgAfterFail(url):

    doc = conn["news_ver2"]["googleNewsItem"].find_one({"sourceUrl": url})

    left = doc["relate"]["left"]

    if "img" in left:
        return left["img"]
    else:
        return None




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

    # if len(times)==0 and len(gpes) == 0 and len(orgs) == 0 and len(persons)==0 and len(locs)==0:
    #     return None

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


#摘要抽取任务，对每条新闻进行摘要抽取候，存入mongo
def abstractTaskRun():

    un_runned_docs = conn["news_ver2"]["Task"].find({"abstractOk": 0}).sort([("updateTime", -1)])
    # un_runned_docs = conn["news_ver2"]["Task"].find()
    success_num = 0
    urls = []
    for doc in un_runned_docs:
        url = doc["url"]
        urls.append(url)

    for url in urls:
        try:
            content = GetContent(url)
        except Timeout:
            continue

        if not content:
            today = datetime.date.today()
            yesterday = today - datetime.timedelta(days=1)
            yesterday = yesterday.strftime("%Y-%m-%d %H:%M:%S")
            conn["news_ver2"]["Task"].update({"url": url, "updateTime":{"$lt": yesterday}}, {"$set": {"contentOk": -1}})
            continue

        abstract_here = KeywordExtraction.abstract(content)
        print ">>>>>>>>abstract:", abstract_here

        try:
            conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"abstract": abstract_here}})
        except Exception as e:
            print "abstract update fail, the doc url is :", url
            continue

        conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"abstractOk": 1}})

        success_num += 1
        print "abstract update success, the doc url is: ", url, "success num:", success_num


def GetContent(url):

    apiUrl_text = "http://121.41.75.213:8080/extractors_mvc_war/api/getText?url="+url

    try:
        r_text = requests.get(apiUrl_text)
        text = (r_text.json())["text"]
    except Exception:
        print "get content exception"
        return None

    return text


# 正文，和图片获取 task
def cont_pic_titleTaskRun():

    un_runned_docs = conn["news_ver2"]["Task"].find({"contentOk": 0}).sort([("updateTime", -1)])
    # un_runned_docs = conn["news_ver2"]["Task"].find().sort([("updateTime", -1)])

    urls = []
    for doc in un_runned_docs:
        url = doc["url"]

        left_url = get_left_url(doc)
        if left_url:
            url = left_url

        urls.append(url)

    for url in urls:

        try:
            status = fetch_and_save_content_by_url(url)
        except Timeout:
            print "timeout of url ==>", url
            continue

        if status:

            conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"contentOk": 1}})

        else:
            today = datetime.date.today()
            yesterday = today - datetime.timedelta(days=1)
            yesterday = yesterday.strftime("%Y-%m-%d %H:%M:%S")
            conn["news_ver2"]["Task"].update({"url": url, "updateTime":{"$lt": yesterday}}, {"$set": {"contentOk": -1}})

            print "cont_pic_titleTaskRun fail, the doc url is:", url
            print "this doc will be copied in next round if it is not too late"
            continue

        print "cont_pic_titleTaskRun success, the doc url is:", url

def get_left_url(doc):

    left_url = None
    if "relate" in doc.keys():
            left = doc["relate"]["left"]
            if len(left)>0:
                left_url = left[0]["url"]

    return left_url




# 对应新闻，相关知乎的话题，task
def zhihuTaskRun():

    un_runned_docs = conn["news_ver2"]["Task"].find({"zhihuOk": 0}).sort([("updateTime", -1)])
    # un_runned_docs = conn["news_ver2"]["Task"].find().sort([("updateTime", -1)])

    url_title_pairs = []

    for doc in un_runned_docs:

        title = doc["title"]
        url = doc["url"]
        url_title_pairs.append([url, title])

    index = 0
    no_zhihu = 0
    for url, title in url_title_pairs:

        index += 1
        try:
            ner = Getner(title)
        except Timeout:
            print "timeout of this url==>", url
            continue

        if ner:
            keywords = ner
        else:
            print "when get zhihu, the  ner is None, the url, title==>", url, "|| ", title
            keywords = extract_tags(title, 2)
            keywords = "".join(keywords)

        try:
            zhihu = GetZhihu(keywords)
        except Timeout:
            print "get zhihu timeout, the url is ==>", url
            continue
        if zhihu is None:
            #直呼没有， 也标记为处理过
            no_zhihu += 1
            conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"zhihuOk": 1}})

            print "no zhihu question, the url is ==>", url, "num:", no_zhihu
            continue
        try:
            conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"zhihu": zhihu}})

        except:
            print "update zhihu error, the url is==>", url
            continue

        conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"zhihuOk": 1}})

        print "zhihuTaskRun complete url:", url, "num:", index


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


# 所有任务完成后，设置新闻上线， isOnline为1
def isOnlineTaskRun():
    un_runned_docs = conn["news_ver2"]["Task"].find({"isOnline": 0}).sort([("updateTime", -1)])
    # un_runned_docs = conn["news_ver2"]["Task"].find({"url":"http://www.jfdaily.com/wenyu/new/201503/t20150323_1348552.html"}).sort([("updateTime", -1)])

    for doc in un_runned_docs:

        url = doc["url"]

        # url = "http://www.jfdaily.com/wenyu/new/201503/t20150323_1348552.html"

        weiboOk = 0
        zhihuOk = 0
        contentOk = 0


        abstractOk = 0
        nerOk = 0

        doubanOk = 0
        baikeOk = 0
        weiboOk = 0
        zhihuOk = 0
        baiduSearchOk = 0


        if "contentOk" in doc.keys():
            contentOk = doc["contentOk"]

        if "weiboOk" in doc.keys():
            weiboOk = doc["weiboOk"]

        # if "zhihuOk" in doc.keys():
        #     zhihuOk = doc["zhihuOk"]

        if "abstractOk" in doc.keys():
            abstractOk = doc["abstractOk"]

        if "nerOk" in doc.keys():
            nerOk = doc["nerOk"]

        if "baiduSearchOk" in doc.keys():
            baiduSearchOk = doc["baiduSearchOk"]

        if "zhihuOk" in doc.keys():
            zhihuOk = doc["zhihuOk"]

        # if "weiboOk" in doc.keys():
        #     weiboOk = doc["weiboOk"]

        if "doubanOk" in doc.keys():
            doubanOk = doc["doubanOk"]

        if "baikeOk" in doc.keys():
            baikeOk = doc["baikeOk"]

        if contentOk==1 and abstractOk==1 and nerOk==1 and doubanOk == 1 and baikeOk == 1 and weiboOk == 1 \
                and zhihuOk == 1 and baiduSearchOk == 1:
            try:
                conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"isOnline": 1}})

            except:
                print "isOnlineTaskRun fail, the doc url is:", url
                continue

            conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"isOnline": 1}})

            print "isOnlineTaskRun success, the doc url is:", url

import urllib, cStringIO
def ImgMeetCondition(url):

    print "==>"
    doc = conn['news_ver2']['googleNewsItem'].find_one({"sourceUrl": url})
    if not "imgUrls" in doc.keys() or not doc['imgUrls']:
        return False

    img_url = doc['imgUrls']
    try:
        img_url = img_url.encode("utf-8")
        file = cStringIO.StringIO(urllib.urlopen(img_url).read())
        im = Image.open(file)
    except IOError:
        print "IOError, imgurl===>", img_url, "url ====>", url
        return False

    width, height = im.size

    if width * height >= 40000:
        return True

    print width, "+", height, " url=======>", img_url

    return False

# task 百科
def baikeTaskRun():

    un_runned_docs = conn["news_ver2"]["Task"].find({"baikeOk": 0}).sort([("updateTime", -1)])

    # un_runned_docs = conn["news_ver2"]["Task"].find()
    index = 0

    url_title_pairs = []
    for doc in un_runned_docs:

        url = doc["url"]
        title = doc["title"]
        url_title_pairs.append([url, title])

    for url, title in url_title_pairs:
        try:
            keword = Getner(title)

        except Timeout:
            continue
        if keword is None:

            logging.warn("Getner is None, the url==>" + url)
            conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"baikeOk": 1}})
            continue

        re = parseBaike(keword)

        if re is None:

            logging.warn("baike is None, the url==>" + url)
            conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"baikeOk": 1}})
            continue

        try:
            conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"baike": re}})

        except Exception:

            continue

        conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"baikeOk": 1}})
        index += 1
        logging.warn("baikeTaskRun, the url is:" + url + "num==>" + str(index))


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


#task 豆瓣，标签提取任务
def doubanTaskRun():

    un_runned_docs = conn["news_ver2"]["Task"].find({"$or": [{"doubanOk": 0}, {"doubanOk": {"$exists": 0}}]}).sort([("updateTime", -1)])

    # un_runned_docs = conn["news_ver2"]["Task"].find()

    tagUrl = "http://www.douban.com/tag/%s/?source=topic_search"


    title_url_pairs = []
    for doc in un_runned_docs:

        title = doc["title"]
        # title = "厦门飞北京一客机冒烟发出紧急代码后备降合肥"
        url = doc["url"]

        title_url_pairs.append([title, url])


    for title, url in title_url_pairs:

        douban_tags = []
        # title = "财政部：去年超8成土地出让收入用于拆迁征地"
        # url = "http://www.hinews.cn/news/system/2015/03/24/017426253.shtml"
        tags = extract_tags(title)

        is_db_error = False

        for tag in tags:
            if isDoubanTag(tag):
                print "douban tag======>", tag
                url_tag = tagUrl%tag
                tag_url_pairs = [tag, url_tag]
                douban_tags.append(tag_url_pairs)

        try:
            conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"douban": douban_tags}})
        except:
            is_db_error = True
            print "douban set error, url==>", url
            continue

        if not is_db_error:
            conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"doubanOk": 1}})

        print "douban get and set bingo, url==>", url

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

        # dom = etree.HTML(r.text)
        # element = dom.xpath('//title')[0]
        #
        # pat = "没上线"
        # content_str = etree.tostring(element, encoding="utf-8")
        # if re.match(pat, content_str):
        #     return False

    except:
        return False
    return False

def baiduNewsTaskRun():
    start_time, end_time, update_time, update_type, upate_frequency = get_start_end_time(halfday=True)
    start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
    end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')

    un_runned_docs = conn["news_ver2"]["Task"].find({"updateTime": {"$gte": end_time}, "isOnline": 1,
                        "$or":[{"baiduSearchOk": 0}, {"baiduSearchOk": {"$exists": 0}}]}).sort([("updateTime", -1)])

    url_title_pairs = []
    for doc in un_runned_docs:

        url = doc["url"]
        title = doc["title"]
        if not url or not title:
            print "when doing baiduNewsTask, there is no url or title, url==>", url, "title===>", title
            continue

        ls = [url, title]

        url_title_pairs.append(ls)


    for url_title_pair in url_title_pairs:

        url_here = url_title_pair[0]
        title_here = url_title_pair[1]

        '''
        topic = Getner(title_here)
        if not topic:
            topic = extract_tags_helper(title_here)
            topic = 's'.join(topic)'''
        topic = title_here[:len(title_here)/3*2]

        # cmd = 'scrapy crawl news.baidu.com -a url=' + url_here + ' -a topic=\"'+ topic + '\"'



        cmd = 'sh /root/workspace/news_baijia/task/script.sh ' + url_here + ' ' + topic
        # cmd = 'sh script.sh ' + url_here + ' ' + topic
        print cmd

        child = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).wait()
        print "complete url===>", url_here,

        conn["news_ver2"]["Task"].update({"url": url_here}, {"$set": {"baiduSearchOk": 1}})


# task 从googleNewsItem 表中取没上线新闻到 Task表
def newsToTaskRun():

    offline_docs = conn["news_ver2"]["googleNewsItem"].find({"$or": [{"isOnline": 0}, {"isOnline": {"$exists": 0}}]}).sort([("updateTime", -1)])

    index = 0

    url_title_pairs = []
    for doc in offline_docs:

        url = doc["sourceUrl"]
        title = doc["title"]
        url_title_pairs.append([url, title])

    for url, title in url_title_pairs:

        conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"url": url, "title": title, "weiboOk": 0, "zhihuOk": 0,
                                                                 "abstractOk": 0, "contentOk": 0, "nerOk": 0, "isOnline": 0, "baikeOk": 0, "baiduSearchOk": 0}}, upsert=True)
        print "title", title, "num:", index
    print "newsToTaskRun complete"

#task , img get
def GetImagTaskRun():


    print "start GetImagTaskRun"
    un_runned_docs = conn["news_ver2"]["Task"].find({"$or": [{"relateImgOk": 0}, {"relateImgOk": {"$exists": 0}}]}).sort([("updateTime", -1)])

    print "fetch mongo ok"
    # un_runned_docs = conn["news_ver2"]["Task"].find().sort([("updateTime", -1)])

    urls = []
    for doc in un_runned_docs:
        url = doc["url"]
        urls.append(url)

    for url in urls:
        doc_google = conn["news_ver2"]["googleNewsItem"].find_one({"sourceUrl": url})

        if "relate" in doc_google.keys():
            relate = doc_google["relate"]

        keys = ["left", "middle", "bottom", "opinion", "deep_report"]

        for k in keys:
            doImgGetAndSave(k, relate, url)

        print "complete relate url,==>", url

def doImgGetAndSave(k, relate, url):

    print "doImgGetAndSave start"
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
        conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"relate."+k: sub_relate}})
    except Exception:
        print "save relate." + k, " error, the url====> ", url
        return

    conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"relateImgOk": 1}})
    print "doImgGetAndSave ok , url :", url


def GetImgByUrl(url):

    apiUrl_img = "http://121.41.75.213:8080/extractors_mvc_war/api/getImg?url="+url

    r_img = requests.get(apiUrl_img)

    imgs = (r_img.json())["imgs"]

    result = {}

    if isinstance(imgs, list) and len(imgs) > 0:

        img_result = preCopyImg(url, imgs)

        img_result = copyNormalImg(img_result)

        if img_result is None:
            result['img'] = ''
        else:
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

def copyNormalImg(img_result):

    result = []
    for i in img_result:

        result.append(i)
        if i.endswith('.gif') or 'weima' in i or ImgMeetCondition_ver2(i):
            result.remove(i)

    if len(result) > 0:
        return result[0]
    else:
        return None


def GetBigImg(img_result):

    if not len(img_result)>0:
        raise IndexError

    big_img = ''
    big_size = 0
    for img in img_result:
        img_size = ImgMeetCondition_ver2(img, True)
        if img_size > big_size:
            big_size = img_size
            big_img = img

    return big_img




def ImgMeetCondition_ver2(url, getSize=False):


        img_url = url

        # img_url = "http://news.ittime.com.cn/uploadimage/images/窝窝团大.jpg"
        if getSize:

            try:
                file = cStringIO.StringIO(urllib.urlopen(img_url).read())
                im = Image.open(file)
            except IOError:
                print "IOError, imgurl===>", img_url, "url ====>", url
                return 0
            width, height = im.size
            return width*height

        try:
            img_url = img_url.encode('utf-8')
            file = cStringIO.StringIO(urllib.urlopen(img_url).read())
            im = Image.open(file)
        except IOError:
            print "IOError, imgurl===>", img_url, "url ====>", url
            return True
        width, height = im.size
        print(width, height)
        if width * height <= 40000:
            return True
        print width, "+", height, " url=======>", img_url
        return False

def googleNewsTaskRun():
    start_time, end_time, update_time, update_type, upate_frequency = get_start_end_time(halfday=True)
    start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
    end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')

    un_runned_docs = conn["news_ver2"]["Task"].find({"updateTime": {"$gte": end_time}, "isOnline": 1,
                        "$or":[{"googleSearchOk": 0}, {"googleSearchOk": {"$exists": 0}}]}).sort([("updateTime", -1)])

    url_title_pairs = []
    for doc in un_runned_docs:

        url = doc["url"]
        title = doc["title"]
        if not url or not title:
            print "when doing googleNewsTask, there is no url or title, url==>", url, "title===>", title
            continue

        ls = [url, title]

        url_title_pairs.append(ls)


    for url_title_pair in url_title_pairs:

        url_here = url_title_pair[0]
        title_here = url_title_pair[1]

        # topic = Getner(title_here)
        # if not topic:
        #     topic = extract_tags_helper(title_here)
        #     topic = 's'.join(topic)

        topic = title_here
        # cmd = 'scrapy crawl google.com.hk -a url=' + url_here + ' -a topic=\"'+ topic + '\"'
        cmd = '/root/workspace/news_baijia/task/script.sh ' + url_here + ' ' + topic
        # cmd = 'sh script.sh ' + url_here + ' ' + topic
        print cmd



        child = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).wait()
        print "complete url===>", url_here,

        conn["news_ver2"]["Task"].update({"url": url_here}, {"$set": {"googleSearchOk": 1}})
        time.sleep(30)


def clusterTaskRun():

    start_time, end_time, update_time, update_type, upate_frequency = get_start_end_time(halfday=True)
    start_time = start_time + datetime.timedelta(days=-1)
    start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
    end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
    docs = conn["news_ver2"]["googleNewsItem"].find({"createTime": {"$gte": start_time
                                                                    }}).sort([("createTime", -1)])
    param_list = []
    title_dict = {}
    content_dict = {}
    paragraphIndex = 0
    for doc in docs:
        param_elem = {}
        url = doc["sourceUrl"]
        if "text" in doc.keys():
            content = doc["text"]
        else:
            continue
        if "title" in doc.keys():
            title = doc["title"]
        title_dict[str(paragraphIndex)] = title
        content_dict[str(paragraphIndex)] = content
        paragraphIndex += 1
        # param_elem["url"] = url
        # param_elem["content"] = content
        # param_list.append(param_elem)
    # content_dict['1']="【摘要】         7月4日晚，张靓颖在演唱会上公开了与少城时代CEO冯轲长达12年的恋情。恋情公开后，各种有关张靓颖与冯柯的八卦疯狂扩散。但让人意外的是，张靓颖公开恋情，在微博上却让金星的红沙发火了起来，这是怎么一回事？\n    华龙网7月5日22时讯（首席记者 黄军）7月4日晚，张靓颖在演唱会上公开了与少城时代CEO冯轲长达12年的恋情。恋情公开后，各种有关张靓颖与冯柯的八卦疯狂扩散。但让人意外的是，张靓颖公开恋情，在微博上却让金星的红沙发火了起来，这是怎么一回事？\n    当天的演唱会上，张靓颖唱完《终于等到你》后，突然公开了与自己的经纪人，也就是少城时代CEO冯轲的恋情。在粉丝的尖叫下，冯轲走上舞台，与张靓颖热烈拥吻，让不少粉丝润湿眼眶。\n张靓颖做客《金星时间》。 视频截图\n    但是，今晚的微博热搜榜上，没有看见张靓颖公开恋情的话题，却有一个莫名其妙的话题——金星的红沙发。\n    要想知道这是怎么一回事，得回到6月10日播出的《金星时间》中看看。当时，张靓颖是座上宾，节目现场有两张红沙发，都挨着金星，张靓颖选择了离金星近的沙发坐下。采访中，金星问张靓颖是单身还是恋爱状态，张靓颖没有直接回答，但金星表示已经猜出。\n    金星对张靓颖说，坐在靠近她的位置上，很快就要嫁出去了。坐在另一个红沙发上，很快就要生孩子了。\n    这是有典故的。金星说，周迅来的时候还没谈恋爱，来坐了红沙发之后，回去就谈恋爱结婚了。张靓颖坐了那个红沙发后，也在7月4日公开恋情，网友笑称：“结婚生娃也不远了。”\n    也正因如此，张靓颖公开恋情后，“金星的红沙发”话题被迅速刷上了微博热搜榜，阅读量超过1000万。\n"
    paragraphIndex_list = find_Index_similar_with_compare_news(content_dict,
                 {"doc":"【摘要】         7月4日晚，张靓颖在演唱会上公开了与少城时代CEO冯轲长达12年的恋情。恋情公开后，各种有关张靓颖与冯柯的八卦疯狂扩散。但让人意外的是，张靓颖公开恋情，在微博上却让金星的红沙发火了起来，这是怎么一回事？\n    华龙网7月5日22时讯（首席记者 黄军）7月4日晚，张靓颖在演唱会上公开了与少城时代CEO冯轲长达12年的恋情。恋情公开后，各种有关张靓颖与冯柯的八卦疯狂扩散。但让人意外的是，张靓颖公开恋情，在微博上却让金星的红沙发火了起来，这是怎么一回事？\n    当天的演唱会上，张靓颖唱完《终于等到你》后，突然公开了与自己的经纪人，也就是少城时代CEO冯轲的恋情。在粉丝的尖叫下，冯轲走上舞台，与张靓颖热烈拥吻，让不少粉丝润湿眼眶。\n张靓颖做客《金星时间》。 视频截图\n    但是，今晚的微博热搜榜上，没有看见张靓颖公开恋情的话题，却有一个莫名其妙的话题——金星的红沙发。\n    要想知道这是怎么一回事，得回到6月10日播出的《金星时间》中看看。当时，张靓颖是座上宾，节目现场有两张红沙发，都挨着金星，张靓颖选择了离金星近的沙发坐下。采访中，金星问张靓颖是单身还是恋爱状态，张靓颖没有直接回答，但金星表示已经猜出。\n    金星对张靓颖说，坐在靠近她的位置上，很快就要嫁出去了。坐在另一个红沙发上，很快就要生孩子了。\n    这是有典故的。金星说，周迅来的时候还没谈恋爱，来坐了红沙发之后，回去就谈恋爱结婚了。张靓颖坐了那个红沙发后，也在7月4日公开恋情，网友笑称：“结婚生娃也不远了。”\n    也正因如此，张靓颖公开恋情后，“金星的红沙发”话题被迅速刷上了微博热搜榜，阅读量超过1000万。\n"}
                 )
    # param_cluster_list = doc_cluster(param_list)
    # domain_dict = {}
    # for param_cluster_elem in param_cluster_list:
    #     if param_cluster_elem['cluster'] in domain_dict:
    #         domain_dict[param_cluster_elem['cluster']].append(param_cluster_elem)
    #     else:
    #         domain_dict[param_cluster_elem['cluster']] = [param_cluster_elem]

    # for k, domain_events in domain_dict.iteritems():
    #     domain_events = doc_similarity(domain_events)
    #     eventCount = 0
    #     top_story = ''
    #     if len(domain_events) < 2:
    #         continue
    #     for story in domain_events:
    #         #if story.get("eventId", None):  //TODO
    #         if eventCount is 0:
    #             set_googlenews_by_url_with_field_and_value_ex(story["url"], "eventId", story["url"], "similarity", story["similarity"])
    #             top_story = story["url"]
    #             eventCount += 1
    #             continue
    #
    #         set_googlenews_by_url_with_field_and_value_ex(story["url"], "eventId", top_story, "similarity", story["similarity"])
    #         eventCount += 1
    #     print 'found topic events count ===>' , eventCount
    #
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


def doc_classify(training_data, data_to_classify):
    # Load in corpus, remove newlines, make strings lower-case
    # if len(training_data) == 1 or not training_data:
    #     message = "The number of classes has to be greater than one; got 1 or 0."
    #     print message
    #     return
    docs = {}
    docs.update(training_data)
    docs.update(data_to_classify)
    names = docs.keys()

    preprocessed_docs = {}
    for name in names:
        if name=='doc':
        # preprocessed_docs[name] = list(jieba.cut(docs[name]))
            preprocessed_docs[name] = list(extract_tags_helper(docs[name]))
        else:
            preprocessed_docs[name] = list(jieba.cut(docs[name]))
    # Build the dictionary and filter out rare terms
    # Perform Chinese words segmentation.
    # dct = gensim.corpora.Dictionary(preprocessed_docs.values())
    dct = gensim.corpora.Dictionary([preprocessed_docs['doc']])
    unfiltered = dct.token2id.keys()
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

    # Build tfidf
    tfidf = gensim.models.TfidfModel(bow_docs.values())
    bow_docs_tfidf = {}
    for name in names:
        bow_docs_tfidf[name] = tfidf[bow_docs[name]]


    # Dimensionality reduction using LSI. Go from 6D to 2D.
    print "\n---LSI Model---"

    lsi_docs = {}
    num_topics = 300
    lsi_model = gensim.models.LsiModel(bow_docs_tfidf.values(),id2word=dct,
                                       num_topics=num_topics)
    # lsi_model = gensim.models.LsiModel(bow_docs_tfidf.values(),id2word=dct,
    #                                    num_topics=num_topics)


    for name in names:
        vec = bow_docs[name]
        vec_tfidf = bow_docs_tfidf[name]
        sparse = lsi_model[vec_tfidf]
        # dense = vec2dense(sparse, num_topics)
        lsi_docs[name] = sparse

    # Normalize LSI vectors by setting each vector to unit length
    # print "\n---Unit Vectorization---"
    #
    unit_vec = {}
    #
    for name in names:

        vec = bow_docs[name]
        norm = sqrt(sum(num[1] ** 2 for num in vec))
        if norm<0.000001:
            norm = 1
        with np.errstate(invalid='ignore'):
            unit_vec[name] = [(num[0], num[1]/norm) for num in vec]
        # if norm<0.000001:
        #     unit_vec[name] = [0.0] * len(vec)

    #     unit_vecs[name] = unit_vec
    # Take cosine distances between docs and show best matches
    print "\n---Document Similarities---"

    # index = gensim.similarities.MatrixSimilarity(lsi_docs.values())
    # index = gensim.similarities.MatrixSimilarity(bow_docs_tfidf.values())
    index = gensim.similarities.MatrixSimilarity(bow_docs.values())
    print type(index)


    for i, name in enumerate(names):
        if name=="doc":
            print "article_title,%s"%docs[name]
            # vec = lsi_docs[name]
            vec = bow_docs_tfidf[name]
            vec = unit_vec[name]
            sims = index[vec]

            sims = sorted(enumerate(sims), key=lambda item: -item[1])


            # index=0
            for sims_elem in sims:
                print "sims,%d"%sims_elem[0]
                print "title,%s,sims,%10.3f"%(docs[str(names[sims_elem[0]])], sims_elem[1])
                # index+=1
            break
        else:
            continue
            # Similarities are a list of tuples of the form (doc #, score)
            # In order to extract the doc # we take first value in the tuple
            # Doc # is stored in tuple as numpy format, must cast to int

            # if int(sims[0][0]) != i:
            #     match = int(sims[0][0])
            # else:
            #     match = int(sims[1][0])

            # match = names[match]
        #
        # print "\n---Classification---"
        #
        # train = [unit_vecs[key] for key in training_data.keys()]
        #
        # labels = [(num + 1) for num in range(len(training_data.keys()))]
        # label_to_name = dict(zip(labels, training_data.keys()))
        # classifier = SVC()
    # classifier.fit(train, labels)
    # result = {}
    # for name in names:
    #
    #     vec = unit_vecs[name]
    #     label = classifier.predict([vec])[0]
    #     cls = label_to_name[label]
    #     if name in data_to_classify.keys():
    #         result[name] = cls
    # return result



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

    # Build tfidf
    tfidf = gensim.models.TfidfModel(bow_docs.values())
    bow_docs_tfidf = {}
    for name in names:
        bow_docs_tfidf[name] = tfidf[bow_docs[name]]


    # Dimensionality reduction using LSI. Go from 6D to 2D.
    print "\n---LSI Model---"

    lsi_docs = {}
    num_topics = 300
    lsi_model = gensim.models.LsiModel(bow_docs_tfidf.values(),id2word=dct,
                                       num_topics=num_topics)
    # lsi_model = gensim.models.LsiModel(bow_docs_tfidf.values(),id2word=dct,
    #                                    num_topics=num_topics)


    for name in names:
        vec = bow_docs[name]
        vec_tfidf = bow_docs_tfidf[name]
        sparse = lsi_model[vec_tfidf]
        # dense = vec2dense(sparse, num_topics)
        lsi_docs[name] = sparse

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
    print "\n---Document Similarities---"

    # index = gensim.similarities.MatrixSimilarity(lsi_docs.values())
    # index = gensim.similarities.MatrixSimilarity(bow_docs_tfidf.values())
    index = gensim.similarities.MatrixSimilarity(bow_docs.values())
    # print type(index)



    for i, name in enumerate(names):
        if name=="doc":
            paragraphIndex_list = []
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
                    paragraphIndex_list.append(sims_elem[0])
                else:
                    continue
                    # print "sims,%s"%sims_elem[0]
                    # print "title,%s,sims,%10.3f"%(docs[sims_elem[0]], sims_elem[1])
                # index+=1
            break
        else:
            continue

    return  paragraphIndex_list

def calculate_sim(vec, names, unit_vec):
    sims={}
    for name in names:
        sims_value = sum([vec[i]*unit_vec[name][i] for i in range(len(vec))])
        sims[name] = sims_value
    return sims

def vec2dense(vec, num_terms):
    '''Convert from sparse gensim format to dense list of numbers'''
    return list(gensim.matutils.corpus2dense([vec], num_terms=num_terms).T[0])


def set_googlenews_by_url_with_field_and_value_ex(url, field1, value1, field2, value2):
    conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {field1: value1, field2: value2}})





def getBaiduHotWord():
    DBStore = dbConn.GetDateStore()
    conn = DBStore._connect_news

    map={'0': '全部', '1': '国际', '2':'国内', '3':'体育', '4':'娱乐', '5':'社会', '6':'财经', '8':'科技', '10':'汽车', '14':'军事' }
    result = []
    for i  in [0, 1, 2, 3, 4, 5, 6, 8, 10, 14]:
        apiUrl = "http://news.baidu.com/n?m=rddata&v=hot_word&type=%d&date="%i
        r = requests.get(apiUrl)
        if r.status_code == 200:
            print "content,%s"%r.content
            dict_obj = json.loads(r.content)
            data = dict_obj['data']
            for data_elem in data:
                result_elem = {}
                result_elem["baiduHotWord"] = data_elem["query_word"].split(" ")
                result_elem["title"] = data_elem["title"]
                result_elem["type"] = map[str(i)]
                result_elem["createTime"] = getDefaultTimeStr()
                result_elem["chemicalBond"] = "baiduHotWord"
                result.append(result_elem)


    for result_elem in result:
        is_exists_in_elementary = conn['news_ver2']['elementary'].find_one({'title': result_elem['title']})
        if is_exists_in_elementary:
            continue
        else:
            conn['news_ver2']['elementary'].insert(result_elem)



def getDefaultTimeStr():
    format='%Y-%m-%d %H:%M:%S'
    defaultTime=(datetime.datetime.now())
    defaultTimeStr=defaultTime.strftime(format)
    return defaultTimeStr


def bingSearch():
    apiUrl ='http://cn.bing.com/hpm?'
    response = requests.get(apiUrl)
    if response.status_code == 200:
        print "content,%s"%response.text
        content = etree.HTML(response.text)
        # content = lxml.html.fromstring(response.content)
        pages_arr = content.xpath('//div[@id="crs_scroll"]/ul/li')
        # re.compile(r'<div id="crs_scroll" role="complementary"><ul id="crs_pane"><li.*?</li>')
        # pages_arr = re.findall

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

                # try:
            topic = topic.encode('utf8').decode("utf8")
            no_error_pattern = re.compile(u'[\u4e00-\u9fa5_0-9]+')
            if re.search(no_error_pattern, topic):
                params = {"topic": topic, "img": img_after}
                print "topic,%s"%topic
                print "search_start"
                do_search_task(params)
                print "search_end"
            else:
                continue
            # except:
            #     continue

    else:
        return ""

def conver_small_to_larger(img):
    if re.sub("&","&amp;", img).startswith("http://s.cn.bing.net"):
        return re.sub("&","&amp;", img)
    else:
        return "http://s.cn.bing.net" + re.sub("&","&amp;", img)


def aggreSearch():

    docs_online_search_ok = fetch_unrunned_docs_by_date(isOnline = True, aggreSearchOk = True)
    url_title_lefturl_sourceSite_pairs_online_search_ok = fetch_url_title_lefturl_pairs(docs_online_search_ok)

    logging.warning("##################### online_search_task start ********************")
    for url, title, lefturl, sourceSiteName in url_title_lefturl_sourceSite_pairs_online_search_ok:

        params = {"url":url, "title":title, "lefturl":lefturl, "sourceSiteName": sourceSiteName}
        do_search_task(params)
        conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"aggreSearchOk": 1}})

    logging.warning("##################### online_search_task complete ********************")

def onlineEvent():
    start_time, end_time, update_time, update_type, update_frequency = get_start_end_time(halfday=True)
    end_time = end_time + datetime.timedelta(days=-2)
    end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
    now = datetime.datetime.now()
    now_time = now.strftime('%Y-%m-%d %H:%M:%S')

    docs_online = fetch_unrunned_docs_by_date(isOnline = True)
    url_title_lefturl_sourceSite_pairs_online = fetch_url_title_lefturl_pairs(docs_online)

    logging.warning("##################### online_event_task start ********************")
    for url, title, lefturl, sourceSiteName in url_title_lefturl_sourceSite_pairs_online:
        params = {"url":url, "title":title, "lefturl":lefturl, "sourceSiteName": sourceSiteName}
        try:
            do_event_task(params, end_time, now_time)
        except:
            continue

    logging.warning("##################### online_event_task complete ********************")


def unOnlineEvent():
    logging.warning("##################### unOnline_event_task start ********************")
    docs = fetch_unrunned_docs_by_date()
    url_title_lefturl_sourceSite_pairs = fetch_url_title_lefturl_pairs(docs)
    start_time, end_time, update_time, update_type, update_frequency = get_start_end_time(halfday=True)
    end_time = end_time + datetime.timedelta(days=-2)
    start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
    end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
    now = datetime.datetime.now()
    now_time = now.strftime('%Y-%m-%d %H:%M:%S')

    for url, title, lefturl, sourceSiteName in url_title_lefturl_sourceSite_pairs:
        params = {"url":url, "title":title, "lefturl":lefturl, "sourceSiteName": sourceSiteName}
        print "*****************************task start, the url is %s, sourceSiteName: %s " \
                  "*****************************" % (url, sourceSiteName)
        do_event_task(params, end_time, now_time)

    logging.warning("##################### unOnline_event_task complete ********************")

if __name__ == '__main__':

    # ImgMeetCondition_ver2("111")

    for arg in sys.argv[1:]:
        print arg
        if arg == 'weibo':
            print "weibo start"
            index=0
            while True:
                time.sleep(30)
                index += 1
                weiboTaskRun()
                logging.warn("===============this round of weibo complete====================")

        elif arg == 'ner':
            print "NER start"
            while True:
                time.sleep(20)
                nerTaskRun()
                logging.warn("===============this round of NER complete====================")

        elif arg == 'abs':
            while True:
                time.sleep(40)
                abstractTaskRun()
                logging.warn("===============this round of abs complete====================")

        elif arg == 'zhihu':
            while True:
                time.sleep(40)
                zhihuTaskRun()
                logging.warn("===============this round of zhihu complete====================")

        elif arg == 'baike':
            while True:
                time.sleep(30)
                baikeTaskRun()
                logging.warn("===============this round of baike complete====================")

        elif arg == 'douban':
            index =0
            while True:
                time.sleep(30)
                index += 1
                doubanTaskRun()
                logging.warn("===============this round of douban complete====================")

        elif arg == 'baiduNews':
            while True:
                time.sleep(50)
                baiduNewsTaskRun()
                logging.warn("===============this round of baiduNews complete====================")

        elif arg == 'googleNews':
            while True:
                googleNewsTaskRun()
                logging.warn("===============this round of googleNews complete====================")
                time.sleep(7200)

        elif arg == 'relateimg':
            while True:
                time.sleep(40)
                GetImagTaskRun()
                logging.warn("===============this round of relateimg complete====================")
        elif arg == "isOnline":
            while True:
                time.sleep(40)
                isOnlineTaskRun()
                logging.warn("===============this round of isonline complete====================")
        elif arg == "content":
            while True:
                time.sleep(30)
                cont_pic_titleTaskRun()
                logging.warn("===============this round of content complete====================")

        elif arg == "cluster":
            while True:
                # time.sleep(30)
                # clusterTaskRun()
                logging.warn("===============this round of content complete====================")
                # time.sleep(3600*24)
        elif arg == "getBaiduHotWord":
            while True:
                # time.sleep(30)
                getBaiduHotWord()
                logging.warn("===============this round of content complete====================")
                time.sleep(3600*2)

        elif arg == "bingSearch":
            while True:
                # time.sleep(30)
                bingSearch()
                logging.warn("===============this round of content complete====================")
                time.sleep(3600*0.5)

        elif arg == "aggreSearch":
            while True:
                # time.sleep(30)
                aggreSearch()
                logging.warn("===============this round of content complete====================")
                time.sleep(3600*0.5)

        elif arg == "onlineEvent":
            while True:
                t00 = datetime.datetime.now()
                t00 = t00.strftime("%Y-%m-%d %H:%M:%S")
                logging.warn("===============this round of content start====================%s"%(t00))
                # time.sleep(30)
                onlineEvent()
                t01 = datetime.datetime.now()
                t01 = t01.strftime("%Y-%m-%d %H:%M:%S")
                logging.warn("===============this round of content complete====================%s"%(t01))
                # time.sleep(3600*0.5)

        elif arg == "unOnlineEvent":
            while True:
                t00 = datetime.datetime.now()
                t00 = t00.strftime("%Y-%m-%d %H:%M:%S")
                logging.warn("===============this round of content start====================%s"%(t00))
                # time.sleep(30)
                unOnlineEvent()
                t01 = datetime.datetime.now()
                t01 = t01.strftime("%Y-%m-%d %H:%M:%S")
                logging.warn("===============this round of content complete====================%s"%(t01))
                # time.sleep(3600*0.5)

        elif arg == "homeGet":
            while True:
                # time.sleep(30)
                options = {}
                options["timing"] = 1
                homeContentFetch(options)
                logging.warn("===============this round of content complete====================")
                time.sleep(3600*1)



        elif arg=='help':
            print "need one or more argument of: weibo, ner, abs, zhihu, baike, douban, baiduNews, relateimg"



