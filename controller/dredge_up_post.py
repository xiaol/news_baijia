# coding=utf-8

from config import dbConn
import datetime
import pymongo
import redis, bson
import tornado
import urllib2
import urllib
import json

DBStore = dbConn.GetDateStore()
pool = redis.ConnectionPool(host='h213', port=6379)
r = redis.Redis(connection_pool=pool)

#zuoyuan
@tornado.gen.coroutine
def dredgeUpStatusforiOS(uid, album, key):
    key = urllib.quote(key.encode('utf8'))
    url = 'http://60.28.29.37:8083/excavator?uid=%s&album=%s&key=%s' % (uid, album, key)
    try:
        response = urllib2.urlopen(url, timeout = 10)
        s = json.loads(response.read())
        key = s["key"]
        dict = r.hgetall(key)
    except:
        dict = {}
    result_dict = {}
    try:
        result_dict['status'] = dict['status']
    except:
        result_dict['status'] = '100'
    try:
        result_dict['content'] = json.loads(dict['newsContent'])['content']
        for i in result_dict['content']:
            if "src" in i.keys():
                result_dict['postImg'] = i["src"]
                break
        if 'postImg' not in result_dict.keys():
            result_dict['postImg'] = ''
    except:
        result_dict['content'] = ''
        result_dict['postImg'] = ''
    try:
        result_dict['douban'] = json.loads(dict['douban'])
    except:
        result_dict['douban'] = ''
    try:
        result_dict['zhihu'] = json.loads(dict['zhihu'])
    except:
        result_dict['zhihu'] = ''
    try:
        result_dict['weibo'] = json.loads(dict['weibo'])
    except:
        result_dict['weibo'] = ''
    try:
        result_dict['baike'] = json.loads(dict['baike'])
    except:
        result_dict['baike'] = ''
    try:
        result_dict['searchItems'] = json.loads(dict['searchItems'])
    except:
        result_dict['searchItems'] = ''
    raise tornado.gen.Return(result_dict)
#zuoyuan

@tornado.gen.coroutine
def dredgeUpStatus(user_id, album_id, is_add):
    conn = DBStore._connect_news
    db = conn["news_ver2"]["AlbumItems"]
    if is_add == "1":
        id = bson.objectid.ObjectId(album_id)
        doc = db.find_one({"_id": id})
        if "album_news_count" in doc.keys():
            count = int(doc["album_news_count"]) + 1
            db.update({"_id": id}, {"$set": {"album_news_count": str(count)}})
    result_dict = []
    dict = r.hgetall("ExcavatorItems")
    for d, x in dict.items():
        list = x.split('&')
        if user_id in list:
            current = r.hgetall(user_id + ":" + d)
            if current.get("alid") == album_id:
                result_dict.append(r.hgetall(user_id + ":" + d))
    result_dict = sorted(result_dict, key=lambda s: s['createTime'], reverse=True)
    for l in result_dict:
        if "content" in l.keys():
            l.pop("content")
        if "aggreItems" in l.keys():
            l.pop("aggreItems")
        if "user_id" in l.keys():
            l.pop("user_id")
        if "title" in l.keys():
            l.pop("title")
        if "alid" in l.keys():
            l.pop("alid")
        if "completeTime" in l.keys():
            l.pop("completeTime")
    raise tornado.gen.Return(result_dict)


def createAlbum(user_id, album_id, album_title, album_des, album_img, album_news_count, create_time):
    conn = DBStore._connect_news
    db = conn["news_ver2"]["AlbumItems"]
    album_id = bson.objectid.ObjectId(album_id)
    if create_time is None:
        create_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if album_title:
        object_id = db.insert(
        {"_id": album_id, "user_id": user_id, "album_title": album_title, "album_des": album_des,
         "album_img": album_img,
         "album_news_count": album_news_count, "create_time": create_time})
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
        db.insert({"user_id": user_id, "album_title": "默认", "album_des": "", "album_img": "2130837576",
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
