# coding=utf-8

from config import dbConn
import pymongo
import tornado

DBStore = dbConn.GetDateStore()

def getStartPageContent():
    conn = DBStore._connect_news
    docs = conn['news_ver2']['googleNewsItem'].find(
        {"originsourceSiteName": {"$in": ["网易新闻图片","观察者网"]}, "imgUrls": {"$ne": None}, "isOnline": 1}).sort(
        "updateTime", pymongo.DESCENDING).limit(1)
    docs_news = conn["news_ver2"]["googleNewsItem"].find({"isOnline": 1}).sort([("createTime", -1)]).limit(20)
    results_docs = {}
    news_dict = []
    img_url =""
    for doc in docs:
        if "imgUrls" in doc.keys():
            results_docs['imgUrl'] = doc['imgUrls']
        if "title" in doc.keys():
            results_docs['title'] = doc['title']
        if "updateTime" in doc.keys():
            results_docs['updateTime'] = doc['updateTime']
        if "sourceUrl" in doc.keys():
            img_url = doc['sourceUrl']
        if "sourceSiteName" in doc.keys():
            sourceSitename = doc["sourceSiteName"]
            results_docs["category"] = sourceSitename[2:4]
    news_dict.append(img_url)
    for doc in docs_news:
        if "sourceUrl" in doc.keys():
            if (doc['sourceUrl'] != img_url):
                news_dict.append(doc['sourceUrl'])
    results_docs['news_url_list'] = news_dict
    conn['news_ver2']['startPage'].remove()
    conn['news_ver2']['startPage'].save(results_docs)

if __name__ == "__main__":
    getStartPageContent()
    print "start page complete" 
