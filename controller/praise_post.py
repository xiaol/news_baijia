#coding=utf-8

from config import dbConn
import json
import datetime,time
import operator
import pymongo
from pymongo.read_preferences import ReadPreference



def AddPraise(userId, platformType, uuid, sourceUrl, commentId, deviceType):
    DBStore = dbConn.GetDateStore()
    conn = DBStore._connect_news
    praise = {}
    praise['userId'] = userId
    praise['platformType'] = platformType
    praise['uuid'] = uuid
    praise['sourceUrl'] = sourceUrl
    praise['commentId'] = commentId
    now = datetime.datetime.now()
    praise['createTime'] = now
    praise['deviceType'] = deviceType
    is_praise = conn['news_ver2']['praiseItem'].find_one({'userId': userId, 'platformType': platformType, 'commentId': commentId})

    if is_praise:
        result = {'response': 200}
    else:
        conn['news_ver2']['praiseItem'].insert(praise)
        result = {'response': 200}
    return result