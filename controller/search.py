# coding=utf-8

import json
import pymongo
from pymongo.read_preferences import ReadPreference
import re
import tornado
import tornado.gen
from task.data_structure import convertGoogleNewsItems, convertNewsItems 
from elasticsearch import Elasticsearch
es = Elasticsearch(["120.27.162.230","120.27.163.39"])

@tornado.gen.coroutine
def search_cartoon(keyword, page):
    res = es.search(index="cartoon", body={"from" : 15*(int(page)-1), "size" : 15, "query": {"match": { "tags" : keyword }}})
    docs = []
    for doc in res["hits"]["hits"]:
        docs.append(doc["_source"])
    raise tornado.gen.Return(docs)

@tornado.gen.coroutine
def search_tags(keyword, page):
    res = es.search(index="news", body={"from" : 15*(int(page)-1), "size" : 15, "query": {"match": { "tags" : keyword }}})
    docs = []
    for doc in res["hits"]["hits"]:
        docs.append(doc["_source"])
    raise tornado.gen.Return(docs)

es1 = Elasticsearch(["120.27.162.230","120.27.163.39"])

@tornado.gen.coroutine
def search(keyword, page):
    res = es1.search(index="news_baijia", body={"from": 15*(int(page)-1), "size":15, "query": {"term": {"title":keyword}}})
    docs = []
    for doc in res["hits"]["hits"]:
        docs.append(doc["_source"])
    raise tornado.gen.Return(docs)
