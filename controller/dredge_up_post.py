# coding=utf-8

from config import dbConn
import datetime
import pymongo
import redis

DBStore = dbConn.GetDateStore()
pool = redis.ConnectionPool(host='h213', port=6379)
r = redis.Redis(connection_pool=pool)


def dredgeUpStatus(keys):
    keys = ['11111111:魔兽世界', '123456:啦啦啦']
    results_docs = {}
    dict = {}
    for key in keys:
        dict[key] = r.hmget(key, "status", "insertId")
    results_docs = dict
    print results_docs
    return results_docs


def createAlbum(user_id, album_title, album_des, album_img, album_news_count):
    conn = DBStore._connect_news
    db = conn["news_ver2"]["AlbumItems"]
    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.insert({"user_id": user_id, "album_title": album_title, "album_des": album_des, "album_img": album_img,
               "album_news_count": album_news_count, "create_time": time})
    results_docs = {}
    docs = db.find({"user_id": user_id, "create_time": time}).limit(1)
    for doc in docs:
        results_docs['album_id'] = str(doc['_id'])

    return results_docs


def fetchAlbumList(user_id):
    conn = DBStore._connect_news
    db = conn["news_ver2"]["AlbumItems"]
    docs = db.find({"user_id": user_id}).sort(
        "create_time", pymongo.ASCENDING)
    if docs.count() == 0:
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.insert({"user_id": user_id, "album_title": "默认", "album_des": "", "album_img": "2130837689",
                   "album_news_count": "0", "create_time": time})
        docs = db.find({"user_id": user_id, "create_time": time}).limit(1)

    results = []
    for doc in docs:
        results_docs = {}
        if "_id" in doc.keys():
            results_docs['album_id'] = str(doc['_id'])
        if "user_id" in doc.keys():
            results_docs['user_id'] = doc['user_id']
        if "album_title" in doc.keys():
            results_docs['album_title'] = doc['album_title']
        if "album_des" in doc.keys():
            results_docs['album_des'] = doc['album_des']
        if "album_img" in doc.keys():
            results_docs['album_img'] = doc['album_img']
        if "album_news_count" in doc.keys():
            results_docs['album_news_count'] = doc['album_news_count']
        if "create_time" in doc.keys():
            results_docs['create_time'] = doc['create_time']
        results.append(results_docs)
    return results
