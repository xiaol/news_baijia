#coding=utf-8

import pymongo
import datetime
import time

today_start = time.strftime("%Y-%m-%d") + ' ' + '00:00:00'

conn = pymongo.Connection("h213", 27017)
db = conn.news_ver2.googleNewsItem
docs = db.find({'sourceSiteName':u'谷歌体育新闻', 'updateTime':{'$gt':today_start}})
new_doc = {}
for doc in docs:
    if "content" in doc.keys():
        new_doc["content"] = doc["content"]
    try:
        new_doc["text"] = doc["text"]
        new_doc["sourceUrl"] = doc["sourceUrl"]
        new_doc["title"] = doc["title"]
        new_doc["_id"] = doc["_id"]
        conn.news_ver2.caimaotiyu.save(new_doc)
    except:
        pass
