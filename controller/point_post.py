#coding=utf-8

from config import dbConn
import json
import datetime,time
import operator
import pymongo
from pymongo.read_preferences import ReadPreference

conn = pymongo.MongoReplicaSetClient("h44:27017, h213:27017, h241:27017", replicaSet="myset",
                                                             read_preference=ReadPreference.SECONDARY)
DBStore = dbConn.GetDateStore()



def AddPoint(sourceUrl, srcText, desText, paragraphIndex, type, uuid, userIcon, userName): #type title abstract content

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

    conn['news_ver2']['pointItem'].update({}, point, upsert=True)
    result = {'response': 200}
    return result