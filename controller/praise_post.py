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
    result = {}
    result['response'] = 200

    if is_praise:
        is_praise.pop('_id', None)
        is_praise.pop('createTime', None)
        result['commentId'] = is_praise['commentId']
        result['sourceUrl'] = is_praise["sourceUrl"]
        result['uuid'] = is_praise['uuid']
        result['userId'] = is_praise['userId']
        result['platformType'] = is_praise['platformType']
    else:
        conn['news_ver2']['praiseItem'].insert(praise)
        praise.pop('_id', None)
        praise.pop('createTime', None)
        result['commentId'] = praise['commentId']
        result['sourceUrl'] = praise["sourceUrl"]
        result['uuid'] = praise['uuid']
        result['userId'] = praise['userId']
        result['platformType'] = praise['platformType']

    return result