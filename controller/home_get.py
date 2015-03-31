#coding=utf-8

from config import dbConn
from weibo import weibo_relate_docs_get, user_info_get
import json
from jieba.analyse import extract_tags

mapOfSourceName = {"weibo":"微博",
                   "wangyi":"wangyi",
                   "xinlang":"xinlang",
                   "zhihu":"zhihu"}

DBStore = dbConn.GetDateStore()

def homeContentFetch(options):

    """

    :rtype :
    """
    updateTime = ''
    limit = 5
    if "updateTime" in options.keys():
        updateTime = options["updateTime"]
    if 'limit' in options.keys():
        limit = options["limit"]

    conn = DBStore._connect_news

    docs = conn['news_ver2']['googleNewsItem'].find({"updateTime": {"$gt": updateTime}, "content": {"$exists": 1}}).sort([("updateTime",-1)]).limit(limit)

    index = 0

    docs_return = []

    for doc in docs:

        sublist = []
        title = doc["title"]

        relate = []

        if "relate" in doc.keys():
            relate = doc["relate"]

        #不取没有相关的
        if not relate:
            continue

        del doc["relate"]


        if "weibo" in doc.keys():
            weibo = doc["weibo"]
            if isinstance(weibo, dict):
                if "sourceName" in weibo:
                    weibo["sourceSitename"] = weibo["sourceName"]
                    del weibo["sourceName"]
                    sublist.append(weibo)

                del doc["weibo"]

            elif isinstance(weibo, list) and len(weibo) > 0:
                weibo = weibo[0]
                if "sourceName" in weibo:
                    weibo["sourceSitename"] = weibo["sourceName"]
                    del weibo["sourceName"]
                sublist.append(weibo)

                del doc["weibo"]

        if "zhihu" in doc.keys():
            zhihu = doc["zhihu"]

            if isinstance(zhihu, dict):
                zhihu["sourceSitename"] = "zhihu"
                sublist.append(zhihu)
                del doc["zhihu"]

            elif isinstance(doc["zhihu"], list) and len(doc["zhihu"]) > 0 :
                zhihu = doc["zhihu"][0]
                zhihu["sourceSitename"] = "zhihu"
                sublist.append(zhihu)
                del doc["zhihu"]

        if "imgUrls" in doc.keys():
            if not doc["imgUrls"]:
                continue
            if len(doc["imgUrls"]) > 0:
                doc["imgUrl"] = doc["imgUrls"][-1]
                del doc["imgUrls"]

        if "content" in doc.keys():
            del doc["content"]

        if "abstract" in doc.keys():
            del doc["abstract"]

        if "douban" in doc.keys():
            del doc["douban"]

        if "baike" in doc.keys():
            del doc["baike"]

        if "baiduSearch" in doc.keys():
            del doc["baiduSearch"]

        #相关新闻每一个来源 选一条
        distinctList, distinctNum, distinct_response_urls, otherNum = GetRelateNews(relate)

        sublist.extend(distinctList)

        doc["sublist"] = sublist
        doc["otherNum"] = otherNum
        doc["urls_response"] = distinct_response_urls  #返回的urls，用于获取其他相关新闻时过滤掉 这几条已经有的新闻

        docs_return.append(doc)


    print docs_return
    return docs_return


# 相关新闻的获取
def GetRelateNews(relate):

    if not relate:
        return

    left_relate = relate["left"]
    mid_relate = relate["middle"]
    bottom_relate = relate["bottom"]
    opinion = relate["opinion"]
    deep_relate = relate["deep_report"]

    sourceNameSet = set()
    distinctList = []
    distinct_response_urls = []
    sumList = []

    for e in mid_relate:
        if not e["title"]:
            continue
        if e["sourceSitename"] not in sourceNameSet:
            e["user"]=""
            distinctList.append(e)
            distinct_response_urls.append(e["url"])
            sourceNameSet.add(e["sourceSitename"])

        sumList.append(e)

    for e in left_relate:
        if not e["title"]:
            continue
        if e["sourceSitename"] not in sourceNameSet:
            e["user"]=""
            distinctList.append(e)
            distinct_response_urls.append(e["url"])
            sourceNameSet.add(e["sourceSitename"])

        sumList.append(e)


    for e in bottom_relate:

        if not e["title"]:
            continue
        if e["sourceSitename"] not in sourceNameSet:
            e["user"]=""
            distinctList.append(e)
            distinct_response_urls.append(e["url"])
            sourceNameSet.add(e["sourceSitename"])

        sumList.append(e)

    for e in opinion:
        if not e["title"]:
            continue
        if e["sourceSitename"] not in sourceNameSet:
            e["user"]=""
            distinctList.append(e)
            distinct_response_urls.append(e["url"])
            sourceNameSet.add(e["sourceSitename"])

        sumList.append(e)

    for e in deep_relate:
        if not e["title"]:
            continue
        if e["sourceSitename"] not in sourceNameSet:
            e["user"]=""
            distinctList.append(e)
            distinct_response_urls.append(e["url"])
            sourceNameSet.add(e["sourceSitename"])

        sumList.append(e)

    otherNum = len(sumList) - len(distinctList)
    return distinctList, len(distinctList), distinct_response_urls, otherNum

def GetWeibos(title, num):

    if num == 0:
        return

    if num == 1:
        weibo = GetOneWeibo(title)
        return weibo

    weibos = weibo_relate_docs_get.search_relate_docs()
    weibos = json.loads(weibos)

    index = 0
    for weibo in weibos:
        if index == num:
            return weibos[:index]

        weibo_id = weibo["weibo_id"]
        user = user_info_get.get_weibo_user(weibo_id)
        weibos[index]["user"] = user["name"]


def GetOneWeibo(title):
    weibos = weibo_relate_docs_get.search_relate_docs(title,1)
    weibos = json.loads(weibos)

    if len(weibos) <= 0:
        return

    if "error" in weibos[0].keys():
        return

    weibo = weibos[0]
    weibo_id = weibo["weibo_id"]
    user = user_info_get.get_weibo_user(weibo_id)
    weibo["user"] = user["name"]


    return weibo







