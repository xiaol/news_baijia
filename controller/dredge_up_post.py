# coding=utf-8

from config import dbConn
import json
import datetime, time
import operator
import pymongo
from pymongo.read_preferences import ReadPreference
from weibo.Comments import guid
import redis
DBStore = dbConn.GetDateStore()
pool = redis.ConnectionPool(host='h213', port=6379)
r = redis.Redis(connection_pool=pool)

def startDredgeUp(user_id, content):
    r.lpush(user_id,content)
    print 'keys:',r.keys(user_id)
    print 'list len:',r.llen(user_id)
    result = {'response': 200}
    return result
