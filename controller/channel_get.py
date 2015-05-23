# coding=utf-8

from config import dbConn
import re
import pymongo

DBStore = dbConn.GetDateStore()
channelEnum = {'时事': 0, '娱乐': 1, '科技': 2, '国际': 3, '体育': 4, '财经': 5, '港台':6, '社会':7}
channelDict = {0: ['内地', '社会', '国内'], 1: ['娱乐'], 2: ['科技'], 3: ['国际'], 4: ['体育'], 5: ['财经'], 6:['港台'], 7:['社会']}


def fetch_channel(channelId, page=1, limit=50):
    conn = DBStore._connect_news
    channelTags = [re.compile(x) for x in channelDict[channelId]]
    docs = conn['news_ver2']['googleNewsItem'].find({"isOnline": 1, "sourceSiteName": {"$in": channelTags}}).sort("createTime", pymongo.DESCENDING).limit(50)
    results_docs = []
    for doc in docs:
        results_docs.append(doc)
        print doc

    return results_docs

