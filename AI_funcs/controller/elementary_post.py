# coding=utf-8

from config import dbConn
import pymongo

DBStore = dbConn.GetDateStore()


def getElementary():
    conn = DBStore._connect_news
    docs = conn['news_ver2']['elementary'].find({"title": {"$ne": None}}).sort("createTime", pymongo.DESCENDING).limit(
        30)
    results_docs = []
    for doc in docs:
        if "_id" in doc.keys():
            doc.pop('_id')
            results_docs.append(doc)
    return results_docs
