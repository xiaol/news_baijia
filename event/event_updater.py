#coding=utf-8
__author__ = 'Ivan liu'

import time
import datetime
import sys
import re

import pymongo
from pymongo.read_preferences import ReadPreference

conn = pymongo.MongoReplicaSetClient("h44:27017, h213:27017, h241:27017", replicaSet="myset",
                                                             read_preference=ReadPreference.SECONDARY)
reload(sys)
sys.setdefaultencoding('utf8')

arg = sys.path[0].split('/')
path_add = arg[:-1]
path_add = '/'.join(path_add)

sys.path.append(path_add+"/controller/")
sys.path.append(path_add)
try:
    from controller.utils import get_start_end_time
except ImportError:
    from utils import get_start_end_time
    print "import error"

from elementary import elementary


def fetch_docs_by_tags(last_update, tags):
    start_time, end_time, update_time, update_type, update_frequency = get_start_end_time(halfday=True)
    start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
    end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
    re_tags = [re.compile(x) for x in tags]

    if not last_update:
        docs = conn["news_ver2"]["googleNewsItem"].find({"isOnline": 1, "title": {'$in': re_tags},
                                                         "createTime": {"$gte": end_time}}).sort([("createTime", pymongo.DESCENDING)])
    else:
        docs = conn["news_ver2"]["googleNewsItem"].find({"isOnline": 1, "title": {'$in': re_tags},
                                                         "createTime": {"$gte": start_time, '$lte': end_time}}).sort([("createTime", pymongo.DESCENDING)])
    return docs


def update_event(elements):
    for element in elements['elements']:
        event_count = 0
        top_story = ''
        if type(element) is list:
            events = fetch_docs_by_tags(True, element)
        else:
            events = fetch_docs_by_tags(True, [element])
        if events.count() < 2:
            continue
        for story in events:
            #if story.get("eventId", None):  //TODO
            if event_count is 0:
                set_googlenews_by_url_with_field_and_value(story['sourceUrl'], "eventId", story["_id"])
                top_story = story["_id"]
            set_googlenews_by_url_with_field_and_value(story["sourceUrl"], "eventId", top_story)
            event_count += 1
        print 'found topic events count ===>', element, '+', event_count


def pre_load_elementary():
    elements = conn['news_ver2']['elementary'].find({})
    results = elementary(elements)
    return results

def update_elementary():
    pass


def reload_elementary():
    pass


def set_googlenews_by_url_with_field_and_value(url, field, value):
    conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {field: value}})


def task():
    coll = conn['local']['oplog.rs']
    cursor = coll.find(tailable=True)
    while cursor.alive:
        try:
            doc = cursor.next()
            if doc['ns'] == 'news_ver2.elementary':
                print doc
            print doc['ns'], doc['op']
        except StopIteration:
            time.sleep(1)


if __name__ == '__main__':
    elements = pre_load_elementary()
    update_event(elements)
    #task()
