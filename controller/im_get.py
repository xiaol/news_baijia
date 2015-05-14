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

def imContentFetch(options):
    if "message" in options.keys() and options["message"]:
        options["commTime"] = get_time()
        userId = options['userId']
        Item = {'userId': userId}
        conn = DBStore._connect_news
        doc = conn['news_ver2']['imItem'].find_one(Item)

        if doc:
            print "user_id,%salread exists in databases"%options['userId']
            listInfos=doc['listInfos']
            listInfos=listInfos+[{'commTime': options["commTime"], 'message': options["message"]}]
            set_im_by_userId_with_field_and_value(options, "listInfos", listInfos)
            # listInfos_cp = listInfos[:]
            merge_listInfos=merge_message(listInfos)
            # merge_listInfos = []
            # set_im_by_userId_with_field_and_value(options, "listInfos", listInfos_cp)
            set_im_by_userId_with_field_and_value(options, "merge_listInfos", merge_listInfos)
            return None
        else:
            listInfos = [{'commTime': options["commTime"], 'message': options["message"]}]
            result = {}
            result["_id"] = options['userId']
            result["userId"] = options['userId']
            result["listInfos"] = listInfos
            result["merge_listInfos"] = listInfos
            item_dict = dict(result)
            conn['news_ver2']['imItem'].save(item_dict)
            return None
    else:
        print "message value is None"
        return None

def set_im_by_userId_with_field_and_value(options, field, value):
    conn["news_ver2"]["imItem"].update({"_id": options['userId']}, {"$set": {field: value}})

def merge_message(listInfos):
    merge_listInfos = []
    commTimeSet = []
    for item in listInfos:
        commTime_ex=item["commTime"]/10000000
        if commTime_ex in commTimeSet:
            position = commTimeSet.index(commTime_ex)
            merge_listInfos[position]["message"] = merge_listInfos[position]["message"]+"."+item["message"]
        else:
            commTimeSet.append(commTime_ex)
            merge_listInfos=merge_listInfos+[item]
    return merge_listInfos