#coding=utf-8

from config import dbConn
import json
import datetime,time
import operator
import pymongo
from pymongo.read_preferences import ReadPreference
from  home_get import get_time



def imUserFetch(options):
    DBStore = dbConn.GetDateStore()
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

def imContentFetch(options):
    DBStore = dbConn.GetDateStore()
    # "$or":[{"googleSearchOk": 0}, {"googleSearchOk": {"$exists": 0}}]
    if "jpushId" in options.keys():
        conn = DBStore._connect_news
        docs = conn['news_ver2']['imItem'].find({"$or":[{'senderId': options['jpushId']}, {'receiverId': options['jpushId']}]})

        if docs:
            result = []
            for doc in docs:

                print "jpushId,%salread exists in databases"%options['jpushId']
                content = doc["merge_listInfos"]
                if doc["senderId"] == options['jpushId']:
                    type = 0
                else:
                    type = 1
                for content_elem in content:
                    result_elem=[]
                    content=[]
                    for sperate_elem in content_elem["content"].split("sperateby1000s"):
                        content.append({"content": sperate_elem, "type": type, "imgUrl": None})
                    result_elem={"serviceId": "0005150a7dd", "updateTime": content_elem["msgTime"], "content": content}
                    result.append(result_elem)

            result = merge_messageBytype(result)

            return result
        else:
            return [{"serviceId": "0005150a7dd","updateTime": None,"content": []}]

    else:

        print "jpushid is none"
        return {"response": "404"}



def imListFetch(options):
    DBStore = dbConn.GetDateStore()
    # "$or":[{"googleSearchOk": 0}, {"googleSearchOk": {"$exists": 0}}]
    if "jpushId" in options.keys() and options["jpushId"]:
        conn = DBStore._connect_news
        docs = conn['news_ver2']['imItem'].find({"$or":[{'senderId': options['jpushId']}, {'receiverId': options['jpushId']}]})

        if docs:
            result = []
            for doc in docs:
                print "jpushId,%salread exists in databases"%options['jpushId']
                content = doc["listInfos"]
                if doc["senderId"] == options['jpushId']:
                    jpushId = doc["receiverId"]
                    lastMsgTime = content[-1]["msgTime"]

                else:
                    jpushId = doc["senderId"]
                    lastMsgTime = content[-1]["msgTime"]
                result.append({"jpushId": jpushId, "lastMsgTime": lastMsgTime})


            result= sorted(result,key=operator.itemgetter("lastMsgTime"),reverse=True)
            result= delDuplicateById(result)
            result_ex=[]
            for result_elem in result:
                userId, platformType=searchUseridByJpushid(result_elem["jpushId"])
                if len(userId) > 0 and len(platformType) >0:
                    userName, userIcon = searchUserNameIconByUserid(userId, platformType)
                else:
                    userName = ""
                    userIcon = ""

                result_elem["userId"] = userId
                result_elem["platformType"] = platformType
                result_elem["userName"] = userName
                result_elem["userIcon"] = userIcon
                result_ex.append(result_elem)
            return result_ex
        else:
            print "Don't talk to  anyone"
            return {"response": "303"}

    else:
        print "jpushid is none"
        return {"response": "404"}




def merge_messageBytype(result):
    merge_listInfos=[]
    msgTimeSet = []
    result= sorted(result,key=operator.itemgetter("updateTime"))
    for item in result:
        msgTime_ex = item["updateTime"]/1000000

        if msgTime_ex in msgTimeSet:
           position = msgTimeSet.index(msgTime_ex)
           merge_listInfos[position]["content"] = merge_listInfos[position]["content"]+item["content"]
        else:
            msgTimeSet.append(msgTime_ex)
            merge_listInfos.append(item)

    return merge_listInfos


def delDuplicateById(result):
    jpushIdSet = []
    uniqueResult = []
    for elem in result:
        jpushId =elem["jpushId"]
        if jpushId in jpushIdSet:
            continue
        else:
            jpushIdSet.append(jpushId)
            uniqueResult.append(elem)
    return uniqueResult


def searchUseridByJpushid(jpushId):
    DBStore = dbConn.GetDateStore()
    conn = DBStore._connect_news
    doc = conn['news_ver2']['imUserItem'].find_one({'jpushId': jpushId})
    if doc:
        userId=doc["userId"]
        platformType=doc["platformType"]
    else:
        userId = ""
        platformType = ""

    return userId, platformType

def searchUserNameIconByUserid(userId, platformType):
    DBStore = dbConn.GetDateStore()
    conn = DBStore._connect_news
    doc = conn['news_ver2']['loginItem'].find_one({'userId': userId, 'platformType':platformType})
    if doc:
        userName = doc["userName"]
        userIcon = doc["userIcon"]
    else:
        userName = ""
        userIcon = ""
    return userName, userIcon

def searchChannelList():
    DBStore = dbConn.GetDateStore()
    conn = DBStore._connect_news
    docs = conn['news_ver2']['ChannelItems'].find().sort("channel_id",pymongo.ASCENDING)
    results_docs = []
    for doc in docs:
        doc.pop('_id')
        results_docs.append(doc)
        print doc
    results_docs = sorted(results_docs, key=lambda channel: int(channel["channel_id"]))
    return results_docs




