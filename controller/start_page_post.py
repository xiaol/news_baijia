#coding=utf-8

from config import dbConn
import pymongo


DBStore = dbConn.GetDateStore()



def getStartPageContent():
    conn = DBStore._connect_news
    docs = conn['news_ver2']['googleNewsItem'].find({"originsourceSiteName": "网易新闻图片","imgUrls":{"$ne":None},"isOnline": 1}).sort("updateTime", pymongo.DESCENDING).limit(1)
    docs_news = conn["news_ver2"]["googleNewsItem"].find({"isOnline": 1}).sort([("createTime", -1)]).limit(10)
    results_docs = {}
    news_dict = []
    for doc in docs:
        if "imgUrls" in doc.keys():
            results_docs['imgUrl'] = doc['imgUrls']
        if "title" in doc.keys():
            results_docs['title'] = doc['title']
        if "updateTime" in doc.keys():
            results_docs['updateTime'] = doc['updateTime']
        if "sourceUrl"in doc.keys():
            url = doc['sourceUrl']
    news_dict.append(url)
    for doc in docs_news:
        if "sourceUrl"in doc.keys():
            if(doc['sourceUrl']!=url):
                news_dict.append(doc['sourceUrl'])
    results_docs['news_url_list']= news_dict
    return results_docs