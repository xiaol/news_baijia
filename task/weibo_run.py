#coding=utf-8

from controller.config import dbConn

conn = dbConn.GetDateStore()

def weiboTaskRun():

    un_runned_docs = conn["news_ver2"]["googleNewsItem"].find({"weibo": {"$exists": 0}})

    for doc in un_runned_docs:
        title = un_runned_docs["title"]


