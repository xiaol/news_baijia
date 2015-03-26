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

    un_runned_docs = conn["news_ver2"]["googleNewsItem"].find()
    # un_runned_docs = conn["news_ver2"]["Task"].find({"weiboOk": 0})


    success_num = 0
    fail_num = 0
    for doc in un_runned_docs:
        # url = doc["url"]
        url = doc["sourceUrl"]
        title = doc["title"]

        keywords = extract_tags(title, 2)
        keywords = " ".join(keywords)

        try:
            weibo_ready = GetOneWeibo(keywords)

        except ConnectionError as e:

            print "weibo connection error, the doc url is:", url
            continue

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
    index = 0
    for doc in un_runned_docs:
        url = doc["url"]
        content = get_content_by_url(url)

        #获取内容 有问题，跳过
        if not content:
            continue

        content_after_cut = jieba.cut(content)

        content_after_cut = "".join(content_after_cut)

        ne = getNe(content_after_cut)

        #ner 有问题，跳过
        if not ne:
            continue

        try:
            conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"ne": ne}})
        except:
            print "ner fail, the doc url is:", url
            continue

        conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"nerOk": 1, "contentOk": 1}})
        index += 1
        print "ner success, the doc url is:", url, "num:", index




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
    print '>>>>>>>>>',r.text, "encoding", r.encoding
    json_r = json.loads(r.text)
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
    pass


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

        if weiboOk and zhihuOk and contentOk and abstractOk and nerOk:
            try:
                conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {"isOnline": 1}})

            except:
                print "isOnlineTaskRun fail, the doc url is:", url
                continue

            conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"isOnline": 1}})

            print "isOnlineTaskRun success, the doc url is:", url


# task 从googleNewsItem 表中取没上线新闻到 Task表
def newsToTaskRun():

    offline_docs = conn["news_ver2"]["googleNewsItem"].find({"$or": [{"isOnline": 0}, {"isOnline": {"$exists": 0}}]})

    index = 0
    for doc in offline_docs:
        index += 1
        url = doc["sourceUrl"]
        title = doc["title"]

        conn["news_ver2"]["Task"].update({"url": url}, {"$set": {"url": url, "title": title, "weiboOk": 0, "zhihuOk": 0,
                                                                 "abstractOk": 0, "contentOk": 0, "nerOk": 0, "isOnline": 0}}, upsert=True)
        print "title", title, "num:", index
    print "newsToTaskRun complete"

def mainRun():

    while True:
        try:
            weiboTaskRun()

            nerTaskRun()

            abstractTaskRun()

            zhihuTaskRun()

            isOnlineTaskRun()

        except:
            continue

if __name__ == '__main__':
    # weiboTaskRun()

    #newsToTaskRun()

    # nerTaskRun()

    abstractTaskRun()






