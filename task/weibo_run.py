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

    # un_runned_docs = conn["news_ver2"]["googleNewsItem"].find()
    un_runned_docs = conn["news_ver2"]["Task"].find({"weiboOk": 0})


    success_num = 0
    fail_num = 0
    for doc in un_runned_docs:
        # url = doc["url"]
        url = doc["url"]
        title = doc["title"]

        keywords = extract_tags(title, 2)
        keywords = " ".join(keywords)

        try:
            weibo_ready = GetOneWeibo(keywords)

        except ConnectionError as e:

            print "weibo connection error, the doc url is:", url
            continue

        if weibo_ready is None:

            conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"weiboOk": 1}})

        if weibo_ready is not None:

            element_weibo = {"sourceName": mapOfSourceName["weibo"], "user": weibo_ready["user"], "url": weibo_ready["url"], "title": weibo_ready["content"]}

            try:
                conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"weibo": element_weibo}})
            except Exception as e:

                print "weiboTaskRun fail, the doc url is:", url
                continue

            conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"weiboOk": 1}})

            success_num += 1
            print "weiboTaskRun success, the doc url is:" + url, "sucess num:", success_num

            continue

        fail_num += 1
        print "weiboTaskRun fail, the doc url is:" + url, "fail num:", fail_num




def GetOneWeibo(title):
    weibos = weibo_relate_docs_get.search_relate_docs(title,1)
    weibos = json.loads(weibos)

    if len(weibos) <= 0:
        return


    if isinstance(weibos, dict) and "error" in weibos.keys():
        return

    weibo = weibos[0]
    weibo_id = weibo["weibo_id"]
    user = user_info_get.get_weibo_user(weibo_id)
    weibo["user"] = user["name"]


    return weibo



# Task : 命名实体识别， 定时分析mongo中新 新闻的命名实体识别
def nerTaskRun():

    un_runned_docs = conn["news_ver2"]["Task"].find({"nerOk": 0})
    # un_runned_docs = conn["news_ver2"]["Task"].find()
    index = 0
    for doc in un_runned_docs:
        url = doc["url"]
        title = doc["title"]

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
            print "ne set fail, the doc url is===>", url
            continue

        conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"nerOk": 1, "contentOk": 1}})
        index += 1
        print "ne set success, the doc url is:", url, "num===>", index




def get_content_by_url(url):

    apiUrl_img = "http://121.41.75.213:8080/extractors_mvc_war/api/getImg?url="
    apiUrl_text = "http://121.41.75.213:8080/extractors_mvc_war/api/getText?url="

    apiUrl_img += url
    apiUrl_text += url

    r_img = requests.get(apiUrl_img)
    r_text = requests.get(apiUrl_text)

    img = (r_img.json())["imgs"]
    text = (r_text.json())["text"]
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

    un_runned_docs = conn["news_ver2"]["Task"].find({"abstractOk": 0})

    success_num = 0
    for doc in un_runned_docs:
        url = doc["url"]
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

    un_runned_docs = conn["news_ver2"]["Task"].find({"contentOk": 0})
    for doc in un_runned_docs:
        url = doc["url"]
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

    un_runned_docs = conn["news_ver2"]["Task"].find({"zhihuOk": 0})

    index = 0
    no_zhihu = 0
    for doc in un_runned_docs:
        index += 1
        title = doc["title"]
        keywords = extract_tags(title, 2)
        keywords = "".join(keywords)

        response_url = doc["url"]

        zhihu = GetZhihu(keywords)
        if zhihu is None:
            #直呼没有， 也标记为处理过
            no_zhihu += 1
            conn["news_ver2"]["Task"].update({"url": response_url}, {"$set": {"zhihuOk": 1}})

            print "no zhihu question, the url is ==>", response_url, "num:", no_zhihu
            continue
        try:
            conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": response_url}, {"$set": {"zhihu": zhihu}})

        except:
            print "update zhihu error, the url is==>", response_url
            continue

        conn["news_ver2"]["Task"].update({"url": response_url}, {"$set": {"zhihuOk": 1}})


        print "zhihuTaskRun complete url:", response_url, "num:", index


def GetZhihu(keyword):

    time.sleep(1)
    apiUrl = "http://www.zhihu.com/search?q={0}&type=question".format(keyword)

    r = requests.get(apiUrl)

    dom =etree.HTML(r.text)

    pat = re.compile('<[^<>]+?>')
    pat_user = re.compile('<[^<>]+?>|[\,，]')

    try:
        element_title = dom.xpath('//div[@class="title"][1]/a')[0]

        raw_content_title = etree.tostring(element_title, encoding='utf-8')

        title = re.sub(pat, '', raw_content_title)

        url = "http://www.zhihu.com" + dom.xpath('//div[@class="title"][1]/a/@href')[0]

        user = dom.xpath('//a[@class="author"][1]/text()')[0]

        result = {"title": title, "url": url, "user": user}

    except Exception as e:

        print "zhihu page Parse error, the url is===>", apiUrl

        result = None


    return result


# 所有任务完成后，设置新闻上线， isOnline为1
def isOnlineTaskRun():
    un_runned_docs = conn["news_ver2"]["Task"].find({"isOnline": 0})

    for doc in un_runned_docs:

        url = doc["url"]
        weiboOk = doc["weiboOk"]
        zhihuOk = doc["zhihuOk"]

        contentOk = doc["contentOk"]
        abstractOk = doc["abstractOk"]
        nerOk = doc["nerOk"]
        if "douban" in doc.keys():
            doubanOk = doc["douban"]

        if "baikeOk" in doc.keys():
            baikeOk = doc["baikeOk"]

        if contentOk==1 and abstractOk==1 and nerOk==1 and doubanOk == 1 and baikeOk == 1:
            try:
                conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"isOnline": 1}})

            except:
                print "isOnlineTaskRun fail, the doc url is:", url
                continue

            conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"isOnline": 1}})

            print "isOnlineTaskRun success, the doc url is:", url

# task 百科
def baikeTaskRun():

    un_runned_docs = conn["news_ver2"]["Task"].find({"baikeOk": 0})

    index = 0
    for doc in un_runned_docs:

        url = doc["url"]
        title = doc["title"]
        keword = Getner(title)

        if keword is None:
            print "Getner is None, the url==>", url
            conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"baikeOk": 1}})
            continue

        re = parseBaike(keword)

        if re is None:

            print "baike is None, the url==>", url
            conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"baikeOk": 1}})
            continue

        try:
            conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"baike": re}})

        except Exception:

            continue

        conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"baikeOk": 1}})
        index += 1
        print "baikeTaskRun, the url is:", url, "num==>", index


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

    un_runned_docs = conn["news_ver2"]["Task"].find({"$or": [{"doubanOk": 0}, {"doubanOk": {"$exists": 0}}]})

    # un_runned_docs = conn["news_ver2"]["Task"].find()

    tagUrl = "http://www.douban.com/tag/%s/?source=topic_search"



    for doc in un_runned_docs:
        douban_tags = []
        title = doc["title"]
        # title = "厦门飞北京一客机冒烟发出紧急代码后备降合肥"
        url = doc["url"]

        tags = extract_tags(title)

        is_db_error = False

        for tag in tags:
            if isDoubanTag(tag):
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

    time.sleep(1)
    url = "http://www.douban.com/tag/%s/?source=topic_search" % tag
    try:
        r = requests.get(url)

        url_after = r.url.encode("utf-8")
        url_after = urllib.unquote(url_after)

        if url == url_after:
            return True
    except:
        return False

    return False



def baiduNewsTaskRun():

    un_runned_docs = conn["news_ver2"]["Task"].find({"$or":[{"baiduSearchOk": 0}, {"baiduSearchOk": {"$exists": 0}}]})

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
        try:
            child = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).wait(timeout=200)
        except:
            print "scrapy error"
            continue

        # t = threading.Timer(200, timeout, [child])
        # t.start()
        # t.join()

        print "complete url===>", url_here,

def timeout(p):

    if p.poll() is None:
        print 'Error: process taking too long to complete--terminating'
        p.kill()


# task 从googleNewsItem 表中取没上线新闻到 Task表
def newsToTaskRun():

    offline_docs = conn["news_ver2"]["googleNewsItem"].find({"$or": [{"isOnline": 0}, {"isOnline": {"$exists": 0}}]})

    index = 0
    for doc in offline_docs:
        index += 1
        url = doc["sourceUrl"]
        title = doc["title"]

        conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"url": url, "title": title, "weiboOk": 0, "zhihuOk": 0,
                                                                 "abstractOk": 0, "contentOk": 0, "nerOk": 0, "isOnline": 0, "baikeOk": 0, "baiduSearchOk": 0}}, upsert=True)
        print "title", title, "num:", index
    print "newsToTaskRun complete"

def mainRun():
    import threading

    exceptNum = 0
    while True:
            try:
                weibo = threading.Thread(name="weiboTask", target=weiboTaskRun)

                ner = threading.Thread(name="nerTask", target=nerTaskRun)

                abst = threading.Thread(name="abstractTask", target=abstractTaskRun)

                zhihu = threading.Thread(name="zhihuTask", target=zhihuTaskRun)

                baike = threading.Thread(name="baikeTask", target=baikeTaskRun)

                douban = threading.Thread(name="doubanTask", target=doubanTaskRun)

                isonline = threading.Thread(name="isOnlineTask", target=isOnlineTaskRun)

                weibo.start()
                ner.start()
                abst.start()
                zhihu.start()
                baike.start()
                douban.start()



                weibo.join()
                ner.join()
                abst.join()
                zhihu.join()
                baike.join()
                douban.join()

                isonline.start()
                isonline.join()

            except:
                exceptNum += 1
                print "fialNum====>",exceptNum


if __name__ == '__main__':


    for arg in sys.argv[1:]:
        print arg
        if arg == 'weibo':
            print "weibo start"
            while True:
                weiboTaskRun()

        elif arg == 'ner':
            print "NER start"
            while True:
                nerTaskRun()

        elif arg == 'abs':
            while True:
                abstractTaskRun()

        elif arg == 'zhihu':
            while True:
                zhihuTaskRun()

        elif arg == 'baike':
            while True:
                baikeTaskRun()

        elif arg == 'douban':
            while True:
                doubanTaskRun()

        elif arg == 'baiduNews':
            while True:
                baiduNewsTaskRun()



