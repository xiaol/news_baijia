#coding=utf-8

from config import dbConn
import json
import datetime,time
import operator
import pymongo
from pymongo.read_preferences import ReadPreference
from weibo.Comments import guid


DBStore = dbConn.GetDateStore()



def AddPoint(sourceUrl, srcText, desText, paragraphIndex, type, uuid, userIcon, userName, userId, platformType, srcTextTime): #type title abstract content
    conn = DBStore._connect_news
    point = {}
    point['sourceUrl'] = sourceUrl
    point['srcText'] = srcText
    point['desText'] = desText
    point['paragraphIndex'] = paragraphIndex
    point['type'] = type
    point['uuid'] = uuid
    point['userIcon'] = userIcon
    point['userName'] = userName
    now = datetime.datetime.now()
    point['createTime'] = now
    point['userId'] = userId
    point['platformType'] = platformType
    point['srcTextTime'] = srcTextTime
    point['commentId'] = guid('news_baijia')
    conn['news_ver2']['pointItem'].insert(point)

    result = point
    result.pop('_id', None)
    result.pop('createTime', None)

    result['response'] = 200
    # result = {'response': 200, 'commentId': point['commentId']}
    return result