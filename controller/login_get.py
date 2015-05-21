#coding=utf-8

from config import dbConn
import json
import datetime,time
import operator
import pymongo
from pymongo.read_preferences import ReadPreference
from  home_get import get_time


def loginContentFetch(options):
    DBStore = dbConn.GetDateStore()
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
            set_login_by_userId_platformType_with_field_and_value(options)
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

def set_login_by_userId_platformType_with_field_and_value(options):
    DBStore = dbConn.GetDateStore()
    conn = DBStore._connect_news
    conn["news_ver2"]["loginItem"].update({"userId": options['userId'], "platformType": options['platformType']},
                                          {"$set": {
                                                    "uuid": options["uuid"],
                                                    "token": options["token"],
                                                    "userIcon": options["userIcon"],
                                                    "userGender": options["userGender"],
                                                    "userName": options["userName"],
                                                    "expiresIn": options["expiresIn"],
                                                    "expiresTime": options["expiresTime"],
                                                    "lastLoginTime": options["lastLoginTime"]

                                                    }

                                           })




















