#coding=utf-8

from config import dbConn
import json
import datetime,time
import operator
import pymongo
from pymongo.read_preferences import ReadPreference


def pointFetch(options): #type title abstract content
    DBStore = dbConn.GetDateStore()
    conn = DBStore._connect_news
    # comments = conn['news_ver2']['pointItem'].find({'sourceUrl': options['sourceUrl']})
    comments = conn['news_ver2']['pointItem'].find({'sourceUrl': options['sourceUrl'], 'paragraphIndex': options['paragraphIndex']})
    result = []
    for comment in comments:
        if comment["type"] in ['text_paragraph', 'text_doc', 'speech_paragraph', 'speech_doc']:
            point = {}
            point['userName'] = comment['userName']
            point['userIcon'] = comment['userIcon']
            point['srcText'] = comment['srcText']
            point['type'] = comment['type']
            result.append(point)

    return result
