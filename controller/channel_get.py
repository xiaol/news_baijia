# coding=utf-8

from config import dbConn
import re
import pymongo

DBStore = dbConn.GetDateStore()
channelEnum = {'时事': 0, '娱乐': 1, '科技': 2, '国际': 3, '体育': 4, '财经': 5, '港台': 6, '社会': 7}
channelDict = {0: ['内地', '社会', '国内'], 1: ['娱乐'], 2: ['科技'], 3: ['国际'], 4: ['体育'], 5: ['财经'], 6: ['港台'], 7: ['社会']}


def fetch_channel(channelId, page=1, limit=50):
    conn = DBStore._connect_news
    channelTags = [re.compile(x) for x in channelDict[channelId]]
    docs = conn['news_ver2']['googleNewsItem'].find({"isOnline": 1, "sourceSiteName": {"$in": channelTags}}).sort(
        "createTime", pymongo.DESCENDING).limit(50)
    results_docs = []
    for doc in docs:
        results_docs.append(doc)
        print doc

    return results_docs


def newsFetch_channel(channelId, page=1, limit=50):
    conn = DBStore._connect_news
    if channelId >= 0:
        docs = conn['news_ver2']['NewsItems'].find({"channel_id": str(channelId), "imgnum": {'$gt': 0}}).skip(
            (page - 1) * limit).limit(limit)
    else:
        channel_doc = conn['news_ver2']['ChannelItems'].find_one({"channel_id": str(channelId)})
        channel_name = channel_doc["channel_name"][0:2]
        docs = conn['news_ver2']['googleNewsItem'].find(
            {"isOnline": 1, "sourceSiteName": {'$regex': channel_name}}).sort(
            "createTime", pymongo.DESCENDING).skip((page - 1) * limit).limit(limit)
    results_docs = []
    for doc in docs:
        doc.pop('_id')
        if "text" in doc.keys():
            doc.pop('text')
        if "abstract" in doc.keys():
            doc.pop('abstract')
        if "gist" in doc.keys():
            doc.pop('gist')
        if "start_title" in doc.keys():
            doc['sourceSiteName'] = doc['start_title']
        if "update_time" in doc.keys():
            doc['updateTime'] = doc['update_time']
        if "source_url" in doc.keys():
            doc['sourceUrl'] = doc['source_url']
        if "content" in doc.keys():
            for _doc in doc['content']:
                for k, item_doc in _doc.iteritems():
                    if "img" in item_doc.keys():
                        doc['imgUrl'] = item_doc['img']
                        break
        if "content" in doc.keys():
            doc.pop('content')
        results_docs.append(doc)
        print doc

    return results_docs
