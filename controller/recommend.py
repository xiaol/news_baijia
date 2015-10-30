# coding=utf-8

import json
import pymongo
from pymongo.read_preferences import ReadPreference
import re
import tornado
import tornado.gen
import redis
import random
r = redis.Redis(host='121.41.75.213', port=6379, db=1)

conn = pymongo.MongoReplicaSetClient("h44:27017, h213:27017, h241:27017", replicaSet="myset",
                                     read_preference=ReadPreference.SECONDARY)

@tornado.gen.coroutine
def recommend(deviceId, channelId):
    db = conn.news_ver2
    doc_num = db.recommendItem.count()
    random_num = random.random()*doc_num
    already_visit_set = r.smembers(deviceId)
    if channelId == "TJ0001":
        docs = db.recommendItem.find({"_id":{'$gte': random_num}}).sort("createTime",pymongo.DESCENDING).limit(30)
    else:
        docs = db.recommendItem.find({"channelId":channelId, "_id":{'$gte': random_num}}).sort("createTime",pymongo.DESCENDING).limit(50)
    doc_list = []
    i = 0
    for doc in docs:
        if i>=15:
            break
        del doc["_id"]
        if doc["sourceUrl"] in already_visit_set:
            continue
        else:
            doc_list.append(doc)
            r.sadd(deviceId, doc["sourceUrl"])
            i = i +1
    # r.hmset("deviceId",{"googleNewsItems":docs_return})
    raise tornado.gen.Return(doc_list)
