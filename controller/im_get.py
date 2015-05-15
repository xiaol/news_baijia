#coding=utf-8

from config import dbConn
import json
import datetime,time
import operator
import pymongo
from pymongo.read_preferences import ReadPreference
from  home_get import get_time

conn = pymongo.MongoReplicaSetClient("h44:27017, h213:27017, h241:27017", replicaSet="myset",
                                                             read_preference=ReadPreference.SECONDARY)
DBStore = dbConn.GetDateStore()

def imUserFetch(options):

    if "uuid" in options.keys() and options["uuid"] and "jpushId" in options.keys() and options["jpushId"]:
        options['_id'] = options["jpushId"]
        Item = {'_id': options['_id']}
        conn = DBStore._connect_news
        doc = conn['news_ver2']['imUserItem'].find_one(Item)

        if doc:
            print "_id,%salread exists in databases"%options['_id']
            item_dict = dict(options)
            conn['news_ver2']['imUserItem'].save(item_dict)
            return {"response": "200"}
        else:
            item_dict = dict(options)
            conn['news_ver2']['imUserItem'].save(item_dict)
            return {"response": "200"}

    else:

        print "uuid or jpushid is none"
        return {"response": "404"}
