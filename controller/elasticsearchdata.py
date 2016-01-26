# coding=utf-8

import json
import pymongo
from pymongo.read_preferences import ReadPreference
import re
import tornado
import tornado.gen
import time
from elasticsearch import Elasticsearch
es = Elasticsearch(["120.27.162.230","120.27.163.39"])
# res = es.index(index="toutiaobaijia", doc_type='newsitems')


conn = pymongo.MongoReplicaSetClient("h44:27017, h213:27017, h241:27017", replicaSet="myset",
                                     read_preference=ReadPreference.SECONDARY)

db = conn.news_ver2

docs = db.elasticsearchtest.find()
for doc in docs:
    try:
        del doc["_id"]
        res = es.index(index="news_baijia", doc_type='fulltext', body=doc)
    except:
        pass
