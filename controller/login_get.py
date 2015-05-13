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
def loginContentFetch(options):
    if "userId" in options.keys() and "platformType" in options.keys():
        userId = options['userId']
        platformType = options['platformType']
        Item = {'userId':userId, 'platformType':platformType}
        conn = DBStore._connect_news
        doc = conn['news_ver2']['loginItem'].find_one(Item)
        if doc:
            options_ex = {}

            print "user_id,%salread exists in databases"%options['userId']
            options["lastLoginTime"] = get_time()
            options["expiresIn"] = long(options["expiresIn"])
            options["expiresTime"] = long(options["expiresTime"])

            #TODO use bulk update, don't update one by one
            set_login_by_userId_platformType_with_field_and_value(options, "uuid", options["uuid"])
            set_login_by_userId_platformType_with_field_and_value(options, "token", options["token"])
            set_login_by_userId_platformType_with_field_and_value(options, "userIcon", options["userIcon"])
            set_login_by_userId_platformType_with_field_and_value(options, "userGender", options["userGender"])
            set_login_by_userId_platformType_with_field_and_value(options, "userName", options["userName"])
            set_login_by_userId_platformType_with_field_and_value(options, "expiresIn", options["expiresIn"])
            set_login_by_userId_platformType_with_field_and_value(options, "expiresTime", options["expiresTime"])
            set_login_by_userId_platformType_with_field_and_value(options, "lastLoginTime", options["lastLoginTime"])
            options["firstLoginTime"] = doc["firstLoginTime"]
            options_ex["user"] = options
            options_ex["response"] = 200

            return options_ex

        else:
            options_ex={}
            options["firstLoginTime"] = get_time()
            options["lastLoginTime"] = get_time()
            options_ex["user"] = options
            options_ex["response"] = 200
            item_dict=dict(options)
            conn['news_ver2']['loginItem'].save(item_dict)

            return options_ex
    else:
        print "uerId/platformType value is None"
        return None

def set_login_by_userId_platformType_with_field_and_value(options, field, value):
    conn["news_ver2"]["loginItem"].update({"userId": options['userId'], "platformType": options['platformType']}, {"$set": {field: value}})




















