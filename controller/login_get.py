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
            print "user_id,%salread exists in databases"%options['userId']
            options["last_login_time"] = get_time()
            set_login_by_userId_platformType_with_field_and_value(options, "uuid", options["uuid"])
            set_login_by_userId_platformType_with_field_and_value(options, "token", options["token"])
            set_login_by_userId_platformType_with_field_and_value(options, "userIcon", options["userIcon"])
            set_login_by_userId_platformType_with_field_and_value(options, "userGender", options["userGender"])
            set_login_by_userId_platformType_with_field_and_value(options, "userName", options["userName"])
            set_login_by_userId_platformType_with_field_and_value(options, "expiresIn", options["expiresIn"])
            set_login_by_userId_platformType_with_field_and_value(options, "expiresTime", options["expiresTime"])
            set_login_by_userId_platformType_with_field_and_value(options, "last_login_time", options["last_login_time"])
            options["first_login_time"] = doc["first_login_time"]

            return options

        else:
            options["first_login_time"] = get_time()
            options["last_login_time"] = get_time()
            item_dict=dict(options)
            conn['news_ver2']['loginItem'].save(item_dict)
            return options
    else:
        print "uerId/platformType value is None"
        return None

def set_login_by_userId_platformType_with_field_and_value(options, field, value):
    conn["news_ver2"]["loginItem"].update({"userId": options['userId'], "platformType": options['platformType']}, {"$set": {field: value}})




















