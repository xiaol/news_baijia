#coding=utf-8
from jieba.analyse import extract_tags
import jieba
import pymongo
from pymongo.read_preferences import ReadPreference
import json
import sys
from requests.exceptions import ConnectionError
import requests
import re
import subprocess
import time
import lxml.etree as etree
import sys
import urllib
import threading
import logging
import os
print "=========",os.getcwd()
reload(sys)
sys.setdefaultencoding('utf8')

arg = sys.path[0].split('/')
path_add = arg[:-1]
path_add = '/'.join(path_add)

sys.path.append(path_add+"/weibo/")
sys.path.append(path_add)
print sys.path
try:
    from weibo import weibo_relate_docs_get, user_info_get
except ImportError:
    import weibo_relate_docs_get
    import user_info_get

from abstract import KeywordExtraction


conn = pymongo.MongoReplicaSetClient("h44:27017, h213:27017, h241:27017", replicaSet="myset",
                                                             read_preference=ReadPreference.SECONDARY)
mapOfSourceName = {"weibo":"微博"}


# Task : 微博获取任务，定时获取数据，存到mongo
def weiboTaskRun():

    # un_runned_docs = conn["news_ver2"]["Task"].find()
    un_runned_docs = conn["news_ver2"]["Task"].find({"weiboOk": 0}).sort([("updateTime", -1)])

    success_num = 0

    url_title_pairs = []
    for doc in un_runned_docs:
        # url = doc["url"]
        url = doc["url"]
        title = doc["title"]
        url_title_pairs.append([url, title])

    for url, title in url_title_pairs:

        keywords = extract_tags(title, 2)
        keywords = " ".join(keywords)

        try:
            weibo_ready = GetWeibo(keywords)

        except ConnectionError as e:

            continue

        if weibo_ready is None:

            conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"weiboOk": 1}})

        if weibo_ready is not None:

            try:
                conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"weibo": weibo_ready}})
            except Exception as e:
                print "weiboTaskRun save weibo fail, the doc url is:", url
                continue

            conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"weiboOk": 1}})

            success_num += 1
            print "weiboTaskRun success, the doc url is:" + url, "sucess num:", success_num


def GetWeibo(title):

    # if one:
    weibos = weibo_relate_docs_get.search_relate_docs(title,1)
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

    # un_runned_docs = conn["news_ver2"]["Task"].find({"nerOk":0}).sort([("updateTime", -1)])   #OK 大写
    un_runned_docs = conn["news_ver2"]["Task"].find()
    index = 0

    url_title_pairs = []
    for doc in un_runned_docs:
        url = doc["url"]
        title = doc["title"]
        url_title_pairs.append([url, title])


    for url, title in url_title_pairs:
        content = get_content_by_url(url)

        #获取内容 有问题，跳过
        if not content:
            continue

        title_after_cut = jieba.cut(title)

        title_after_cut = " ".join(title_after_cut)

        ne = getNe(title_after_cut)

        #ner 有问题，跳过
        if not ne:
            conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"nerOk": 1}})
            continue

        try:
            conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"ne": ne}})
        except:
            print "ne set fail, the doc url is===> ", url
            continue

        conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"nerOk": 1, "contentOk": 1}})
        index += 1
        print "ne set success, the doc url is:", url, "num===> ", index




def get_content_by_url(url):

    time.sleep(4)
    apiUrl_text = "http://121.41.75.213:8080/extractors_mvc_war/api/getText?url="

    apiUrl_text += url

    r_text = requests.get(apiUrl_text)
    text = (r_text.json())["text"]
    img = GetImgByUrl(url)['img']

    try:
        conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"imgUrls": img, "content": text}})
    except Exception as e:
        print ">>>>>>>>save content error", e, "the url is :", url
        return None

    return text


def getNe(content_after_cut):

    print "content_after_cut", content_after_cut
    apiUrl = "http://121.41.75.213:8080/ner_mvc/api/ner?sentence=" + content_after_cut

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
        content = get_content_by_url(url)

        if not content:
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


# 正文，和图片获取 task
def cont_pic_titleTaskRun():

    # un_runned_docs = conn["news_ver2"]["Task"].find({"contentOk": 0})
    un_runned_docs = conn["news_ver2"]["Task"].find().sort([("updateTime", -1)])

    urls = []
    for doc in un_runned_docs:
        url = doc["url"]
        urls.append(url)

    for url in urls:
        content_pic = get_content_by_url(url)

        try:
            conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"content": content_pic}})

        except Exception as e:

            print "cont_pic_titleTaskRun fail, the doc url is:", url
            continue

        conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"contentOk": 1}})

        print "cont_pic_titleTaskRun success, the doc url is:", url


# 对应新闻，相关知乎的话题，task
def zhihuTaskRun():

    un_runned_docs = conn["news_ver2"]["Task"].find({"zhihuOk": 0}).sort([("updateTime", -1)])
    # un_runned_docs = conn["news_ver2"]["Task"].find()


    url_title_pairs = []

    for doc in un_runned_docs:

        title = doc["title"]
        url = doc["url"]
        url_title_pairs.append([url, title])

    index = 0
    no_zhihu = 0
    for url, title in url_title_pairs:

        index += 1
        keywords = extract_tags(title, 2)
        keywords = "".join(keywords)

        zhihu = GetZhihu(keywords)
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

    time.sleep(4)
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

    for doc in un_runned_docs:

        url = doc["url"]

        weiboOk = 0
        zhihuOk = 0
        contentOk = 0


        abstractOk = 0
        nerOk = 0
        if "contentOk" in doc.keys():
            contentOk = doc["contentOk"]

        if "weiboOk" in doc.keys():
            weiboOk = doc["weiboOk"]

        if "zhihuOk" in doc.keys():
            zhihuOk = doc["zhihuOk"]

        if "abstractOk" in doc.keys():
            abstractOk = doc["abstractOk"]

        if "nerOk" in doc.keys():
            nerOk = doc["nerOk"]

        doubanOk = 0
        baikeOk = 0
        weiboOk = 0
        zhihuOk = 0
        baiduSearchOk = 0

        if "baiduSearchOk" in doc.keys():
            baiduSearchOk = doc["baiduSearchOk"]

        if "zhihuOk" in doc.keys():
            zhihuOk = doc["zhihuOk"]

        if "weiboOk" in doc.keys():
            weiboOk = doc["weiboOk"]

        if "douban" in doc.keys():
            doubanOk = doc["douban"]

        if "baikeOk" in doc.keys():
            baikeOk = doc["baikeOk"]

        if contentOk==1 and abstractOk==1 and nerOk==1 and doubanOk == 1 and baikeOk == 1 and weiboOk == 1 \
                and zhihuOk == 1 and baiduSearchOk == 1 and ImgMeetCondition(url):
            try:
                conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"isOnline": 1}})

            except:
                print "isOnlineTaskRun fail, the doc url is:", url
                continue

            conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"isOnline": 1}})

            print "isOnlineTaskRun success, the doc url is:", url


def ImgMeetCondition(url):

    doc = conn['news_ver2']['googleNewsItem'].find_one({"sourceUrl": url})
    if not "imgUrls" in doc.keys() or not doc['imgUrls']:
        return False

    img_url = doc['imgUrls']


    return True

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
        keword = Getner(title)
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

    time.sleep(4)
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

    # un_runned_docs = conn["news_ver2"]["Task"].find({"$or": [{"doubanOk": 0}, {"doubanOk": {"$exists": 0}}]}).sort([("updateTime", -1)])

    un_runned_docs = conn["news_ver2"]["Task"].find()

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

    time.sleep(6)
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

    # un_runned_docs = conn["news_ver2"]["Task"].find({"$or":[{"baiduSearchOk": 0}, {"baiduSearchOk": {"$exists": 0}}]}).sort([("updateTime", -1)])

    un_runned_docs = conn["news_ver2"]["Task"].find().sort([("updateTime", -1)])

    url_title_pairs = []
    for doc in un_runned_docs:

        url = doc["url"]
        title = doc["title"]
        if not url or not title:
            continue

        ls = [url, title]

        url_title_pairs.append(ls)


    for url_title_pair in url_title_pairs:

        url_here = url_title_pair[0]
        title_here = url_title_pair[1]

        topic = Getner(title_here)
        if not topic:
            topic = extract_tags(title_here, 2)
            topic = 's'.join(topic)

        # cmd = 'scrapy crawl news.baidu.com -a url=' + url_here + ' -a topic=\"'+ topic + '\"'

        cmd = 'sh script.sh ' + url_here + ' ' + topic
        print cmd
        print "=======>", sys.get
        child = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).wait()

        print "complete url===>", url_here,

def timeout(p):

    if p.poll() is None:
        print 'Error: process taking too long to complete--terminating'
        p.kill()


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

    un_runned_docs = conn["news_ver2"]["Task"].find({"$or": [{"relateImgOk": 0}, {"relateImgOk": {"$exists": 0}}]}).sort([("updateTime", -1)])

    # un_runned_docs = conn["news_ver2"]["googleNewsItem"].find()

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

def doImgGetAndSave(k, relate, url):

    sub_relate = relate[k]
    for e in sub_relate:
        if not "url" in e.keys():
            continue
        img = GetImgByUrl(url)['img']
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

        for i in imgs:
            if i.endswith('.gif'):
                imgs.remove(i)
            if 'weima' in i:
                imgs.remove(i)
        result['img'] = imgs[0]

    # while result['img'].startswith('/'):
    #     print('!!!!!!!!!!!')
    #     print(result['img'])
        if result['img'].startswith('/'):
            # print('!!!!!!!!!!!')
            # print(result['img'])
            aa = url.find('/', 7)
            # print(url[:aa])
            result['img'] = url[:aa] + result['img']
    else:
        result['img'] = ""

    return result


if __name__ == '__main__':



    for arg in sys.argv[1:]:
        print arg
        if arg == 'weibo':
            print "weibo start"
            index=0
            while True:
                time.sleep(60)
                index += 1
                weiboTaskRun()
                logging.warn("===============this round of weibo complete====================")

        elif arg == 'ner':
            print "NER start"
            while True:
                time.sleep(60)
                nerTaskRun()
                logging.warn("===============this round of NER complete====================")

        elif arg == 'abs':
            while True:
                time.sleep(40)
                abstractTaskRun()
                logging.warn("===============this round of abs complete====================")

        elif arg == 'zhihu':
            while True:
                time.sleep(60)
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
                # time.sleep(300)
                baiduNewsTaskRun()
                logging.warn("===============this round of baiduNews complete====================")
        elif arg == 'relateimg':
            while True:
                time.sleep(40)
                GetImagTaskRun()
                logging.warn("===============this round of relateimg complete====================")
        elif arg == "isOnline":
            while True:

                time.sleep(300)
                isOnlineTaskRun()
                logging.warn("===============this round of isonline complete====================")

        elif arg=='help':
            print "need one or more argument of: weibo, ner, abs, zhihu, baike, douban, baiduNews, relateimg"



