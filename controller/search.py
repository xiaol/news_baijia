# coding=utf-8

import json
import pymongo
from pymongo.read_preferences import ReadPreference
import re
import tornado
import tornado.gen

conn = pymongo.MongoReplicaSetClient("h44:27017, h213:27017, h241:27017", replicaSet="myset",
                                     read_preference=ReadPreference.SECONDARY)

@tornado.gen.coroutine
def search(keyword, start):
    db = conn.news_ver2
    docs_googleNewsItem = db.googleNewsItem.find({"title":re.compile(keyword)}).sort("createTime",pymongo.ASCENDING).skip(int(start)/2).limit(7)
    docs_NewsItems = db.NewsItems.find({"title":re.compile(keyword)}).sort("create_time", pymongo.ASCENDING).skip(int(start)-int(start)/2).limit(8)
    doc_list = []
    for doc in docs_googleNewsItem:
        del doc["_id"]
        doc_list.append(doc)
    for doc in docs_NewsItems:
        del doc["_id"]
        doc_list.append(doc)
    raise tornado.gen.Return(doc_list)
