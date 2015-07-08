#coding=utf-8

from config import dbConn
import pymongo


DBStore = dbConn.GetDateStore()



def getStartPageContent():
    conn = DBStore._connect_news
    docs = conn['news_ver2']['googleNewsItem'].find({"originsourceSiteName": "观察者网"}).sort("updateTime", pymongo.DESCENDING).limit(1)
    results_docs = {}
    for doc in docs:
        if "imgUrls" in doc.keys():
            results_docs['imgUrl'] = doc['imgUrls']
        if "title" in doc.keys():
            results_docs['title'] = doc['title']
        if "updateTime" in doc.keys():
            results_docs['updateTime'] = doc['updateTime']
    return results_docs