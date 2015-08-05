# coding=utf-8

from config import dbConn
import datetime
import pymongo
import redis, bson

DBStore = dbConn.GetDateStore()
pool = redis.ConnectionPool(host='h213', port=6379)
r = redis.Redis(connection_pool=pool)


def dredgeUpStatus(user_id, album_id, is_add):
    conn = DBStore._connect_news
    db = conn["news_ver2"]["AlbumItems"]
    if is_add == "1":
        id = bson.objectid.ObjectId(album_id)
        doc = db.find_one({"_id": id})
        if "album_news_count" in doc.keys():
            count = int(doc["album_news_count"]) + 1
            db.update({"_id": id}, {"$set": {"album_news_count": str(count)}})
    results_docs = {}
    result_dict = []
    dict = r.hgetall("ExcavatorItems")
    for d, x in dict.items():
        list = x.split('&')
        if user_id in list:
            current = r.hgetall(user_id + ":" + d)
            if current.get("alid") == album_id:
                results_docs[user_id + ":" + d] = r.hgetall(user_id + ":" + d)
    result_list = sorted(results_docs.keys(), key=lambda a: results_docs[a]['createTime'], reverse=True)
    for l in result_list:
        result = {}
        result[l] = results_docs[l]
        result_dict.append(result)
    return result_dict


def createAlbum(user_id, album_title, album_des, album_img, album_news_count):
    conn = DBStore._connect_news
    db = conn["news_ver2"]["AlbumItems"]
    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    object_id = db.insert(
        {"user_id": user_id, "album_title": album_title, "album_des": album_des, "album_img": album_img,
         "album_news_count": album_news_count, "create_time": time})
    results_docs = {}
    results_docs['album_id'] = str(object_id)

    return results_docs


def updateAlbum(album_id, album_title, album_des, album_img, album_news_count):
    conn = DBStore._connect_news
    album_id = bson.objectid.ObjectId(album_id)
    db = conn["news_ver2"]["AlbumItems"]
    results_docs = {}
    db.update({"_id": album_id}, {"$set": {"album_title": album_title, "album_des": album_des, "album_img": album_img,
                                           "album_news_count": album_news_count}})
    results_docs['response'] = 200

    return results_docs


def removeAlbum(album_id, default_album_id):
    conn = DBStore._connect_news
    album_id = bson.objectid.ObjectId(album_id)
    default_album_id = bson.objectid.ObjectId(default_album_id)
    db = conn["news_ver2"]["AlbumItems"]
    results_docs = {}
    db.remove({"_id": album_id})

    conn["news_ver2"]["NewsItems"].update({"album_id": album_id}, {"$set": {"album_id": default_album_id}})

    results_docs['response'] = 200

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
