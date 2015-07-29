# coding=utf-8

from config import dbConn
import redis
DBStore = dbConn.GetDateStore()
pool = redis.ConnectionPool(host='h213', port=6379)
r = redis.Redis(connection_pool=pool)

def dredgeUpStatus(keys):
    keys=['11111111:魔兽世界','123456:啦啦啦']
    results_docs = {}
    dict = {}
    for key in keys:
        dict[key]=r.hmget(key,"status","insertId")
    results_docs =dict
    print results_docs
    return results_docs
