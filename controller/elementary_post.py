# coding=utf-8

from config import dbConn
import pymongo

DBStore = dbConn.GetDateStore()

@tornado.gen.coroutine
def getElementary():
    conn = DBStore._connect_news
    docs = conn['news_ver2']['elementary'].find({"title": {"$ne": None}}).sort("createTime", pymongo.DESCENDING).limit(
        30)
    results_docs = []
    for doc in docs:
        if "_id" in doc.keys():
            if len(doc["title"]) > 9:
                continue
            doc.pop('_id')
            results_docs.append(doc)
    # return results_docs
    raise tornado.gen.Return(results_docs)
