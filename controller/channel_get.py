# coding=utf-8

from config import dbConn
import re
import pymongo
import operator
import json
DBStore = dbConn.GetDateStore()
channelEnum = {'时事': 0, '娱乐': 1, '科技': 2, '国际': 3, '体育': 4, '财经': 5, '港台': 6, '社会': 7}
channelDict = {0: ['内地', '社会', '国内'], 1: ['娱乐'], 2: ['科技'], 3: ['国际'], 4: ['体育'], 5: ['财经'], 6: ['港台'], 7: ['社会']}
special_source = ["观察", "网易"]

def fetch_channel(channelId, page=1, limit=50):
    conn = DBStore._connect_news
    channelTags = [re.compile(x) for x in channelDict[channelId]]
    docs = conn['news_ver2']['googleNewsItem'].find({"isOnline": 1, "sourceSiteName": {"$in": channelTags}}).sort(
        "createTime", pymongo.DESCENDING).limit(limit)
    results_docs = []
    for doc in docs:
        results_docs.append(doc)
        print doc

    return results_docs


def newsFetch_channel(channelId, page=1, limit=50):
    conn = DBStore._connect_news
    if channelId >= 0:
        docs = conn['news_ver2']['NewsItems'].find({"channel_id": str(channelId), "imgnum": {'$gt': 0}, 'create_time':{ '$exists': True}}).sort("create_time", pymongo.DESCENDING).skip(
            (page - 1) * limit).limit(limit)
    else:
        channel_doc = conn['news_ver2']['ChannelItems'].find_one({"channel_id": str(channelId)})
        channel_name = channel_doc["channel_name"][0:2]
        docs = conn['news_ver2']['googleNewsItem'].find(
            {"isOnline": 1, "sourceSiteName": {'$regex': channel_name}}).sort(
            "createTime", pymongo.DESCENDING).skip((page - 1) * limit).limit(limit)
    results_docs = []
    docs = reorganize_news(docs)
    for doc in docs:
        if "_id" in doc.keys():
            doc['id']= str(doc['_id'])
            del doc['_id']
        if "text" in doc.keys():
            doc.pop('text')
        if "abstract" in doc.keys():
            doc.pop('abstract')
        if "gist" in doc.keys():
            doc.pop('gist')
        if "start_title" in doc.keys():
            sourceSitename = doc["start_title"]
            doc["category"] = sourceSitename[2:4]
            doc['sourceSiteName'] = doc['start_title']
        if "update_time" in doc.keys():
            doc['updateTime'] = doc['update_time']
        if "source_url" in doc.keys():
            url = doc['source_url']
            doc['sourceUrl'] = doc['source_url']
        doc['imgUrl']=getImg(doc)
        if "content" in doc.keys():
            doc.pop('content')
        isWeiboFlag = 0
        isBaikeFlag = 0
        isZhihuFlag = 0
        isImgWallFlag = 0
        isCommentsFlag = 0
        if "douban" in doc.keys():
            del doc["douban"]
        if "baike" in doc.keys():
            isBaikeFlag = 1
            del doc["baike"]
        if "baiduSearch" in doc.keys():
            del doc["baiduSearch"]

        if "abstract" in doc.keys():
            del doc["abstract"]
        if "imgWall" in doc.keys():
            if doc["imgWall"]:
                isImgWallFlag = 1

            del doc["imgWall"]
        sublist = []
        filter_url=[]
        undocs_list = []

        if "sublist" in doc.keys():
            sublist = doc["sublist"]
            del doc["sublist"]

        if "weibo" in doc.keys():
            weibo = doc["weibo"]
            if weibo:
                isWeiboFlag = 1

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
            if zhihu:
                isZhihuFlag = 1
            del doc["zhihu"]

        doc_comment = conn["news_ver2"]["commentItems"].find_one({"relateUrl": url})
        if doc_comment:
            if doc_comment["comments"]:
                isCommentsFlag = 1

        doc["isWeiboFlag"] = isWeiboFlag
        doc["isBaikeFlag"] = isBaikeFlag
        doc["isZhihuFlag"] = isZhihuFlag
        doc["isImgWallFlag"] = isImgWallFlag
        doc["isCommentsFlag"] = isCommentsFlag
        results_docs.append(doc)
        print doc

    return results_docs

def getImg(doc):
    if "content" in doc.keys():
        for _doc in doc['content']:
            for k, item_doc in _doc.iteritems():
                if "img" in item_doc.keys():
                   return item_doc['img']

def reorganize_news(docs):
    results_docs = []
    eventId_dict = {}

    for doc in docs:
        if 'eventId' in doc.keys():
            if doc['eventId'] in eventId_dict.keys():
                eventId_dict[doc['eventId']].append(doc)
            else:
                eventId_dict[doc['eventId']] = [doc]
        else:
            results_docs.append(doc)

    for (eventId, eventList) in eventId_dict.items():
        results_docs.append(constructEvent(eventList))

    results_docs= sorted(results_docs,key=operator.itemgetter("create_time"))
    return results_docs

def constructEvent(eventList):
    result_doc = {}
    sublist = []
    for eventElement in eventList:
        if eventElement['eventId'] == eventElement["source_url"]:
            result_doc = eventElement

        else:
            subElement={'sourceSitename': eventElement['start_title'], 'url': eventElement['source_url'], 'title': eventElement['title']}
            sublist.append(subElement)
    result_doc["sublist"] = sublist

    return result_doc

def GetRelateNews(relate, filter_url):

    # if not relate:
    #     return

    left_relate = relate["left"]
    mid_relate = relate["middle"]
    bottom_relate = relate["bottom"]
    opinion = relate["opinion"]
    deep_relate = relate["deep_report"]

    sourceNameSet = set()
    distinctList = []
    distinct_response_urls = []
    sumList = []


    total_relate = [left_relate, mid_relate, bottom_relate, opinion, deep_relate]

    for relate in total_relate:
        for e in relate:
            if not e["title"]:
                continue
            if e["sourceSitename"] not in sourceNameSet and e["url"] not in filter_url:
                e["user"]=""
                distinctList.append(e)
                distinct_response_urls.append(e["url"])
                sourceNameSet.add(e["sourceSitename"])

            sumList.append(e)

    otherNum = len(sumList) - len(distinctList)
    return distinctList, len(distinctList), distinct_response_urls, otherNum
