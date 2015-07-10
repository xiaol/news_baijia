#coding=utf-8
__author__ = 'Ivan liu'

import time
import datetime
import sys
import re
import logging

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

from task.weibo_run_re import filter_unrelate_news


def fetch_docs_by_tags(last_update, tags, data_space=True):
    start_time, end_time, update_time, update_type, update_frequency = get_start_end_time(halfday=True)
    start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
    end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
    re_tags = [re.compile(x) for x in tags]
    if data_space:
        if not last_update:
            docs = conn["news_ver2"]["googleNewsItem"].find({"isOnline": 1, "title": {'$in': re_tags},
                                                         "createTime": {"$gte": end_time}}).sort([("createTime", pymongo.DESCENDING)])
        else:
            docs = conn["news_ver2"]["googleNewsItem"].find({"isOnline": 1, "title": {'$in': re_tags},
                                                     "createTime": {"$gte": start_time, '$lte': end_time}}).sort([("createTime", pymongo.DESCENDING)])

    else:
        docs = conn["news_ver2"]["googleNewsItem"].find({"title": {'$in': re_tags},
                                                        "createTime": {"$gte": start_time}}).sort([("createTime", pymongo.DESCENDING)])
    return docs



def fetch_news_docs_by_tags(channelId,last_update, tags, data_space=True):
    start_time, end_time, update_time, update_type, update_frequency = get_start_end_time(halfday=True)
    start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
    end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
    re_tags = [re.compile(x) for x in tags]
    if data_space:
        if not last_update:
            docs = conn["news_ver2"]["googleNewsItem"].find({"isOnline": 1, "title": {'$in': re_tags},
                                                         "createTime": {"$gte": end_time}}).sort([("createTime", pymongo.DESCENDING)])
        else:
            docs = conn["news_ver2"]["googleNewsItem"].find({"isOnline": 1, "title": {'$in': re_tags},
                                                     "createTime": {"$gte": start_time, '$lte': end_time}}).sort([("createTime", pymongo.DESCENDING)])

    else:

        docs = conn['news_ver2']['NewsItems'].find({"title": {'$in': re_tags}, "channel_id": str(channelId), "imgnum": {'$gt': 0}, 'update_time': {"$gte": start_time}})
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

def load_baiduHotWord():
    start_time, end_time, update_time, update_type, update_frequency = get_start_end_time(halfday=True)
    start_time = start_time + datetime.timedelta(days=-1)
    start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
    end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')

    elements = conn["news_ver2"]["elementary"].find({"createTime": {"$gte": start_time}}).sort([("createTime", pymongo.DESCENDING)])
    results = elementary(elements)
    return results



def update_elementary():
    pass


def reload_elementary():
    pass


def set_googlenews_by_url_with_field_and_value(url, field, value):
    conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {field: value}})

def set_news_by_url_with_field_and_value(url, field, value):

    conn["news_ver2"]["NewsItems"].update({"source_url": url}, {"$set": {field: value}})


def set_news_by_url_with_field_and_value_dict(url, condition_dict):

    conn["news_ver2"]["NewsItems"].update({"source_url": url}, {"$set":
                                                                        {"in_tag": condition_dict["in_tag"],
                                                                         "in_tag_detail": condition_dict["in_tag_detail"],
                                                                         "eventId": condition_dict["eventId"],
                                                                         "eventId_detail": condition_dict["eventId_detail"],
                                                                         "similarity": condition_dict["similarity"],
                                                                         "unit_vec": condition_dict["unit_vec"],
                                                                         "keyword": condition_dict["keyword"]
                                                                         }
                                                               })


def set_googlenews_by_url_with_field_and_value_dict(url, condition_dict):

    conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set":
                                                                        {"in_tag": condition_dict["in_tag"],
                                                                         "in_tag_detail": condition_dict["in_tag_detail"],
                                                                         "eventId": condition_dict["eventId"],
                                                                         "eventId_detail": condition_dict["eventId_detail"],
                                                                         "similarity": condition_dict["similarity"],
                                                                         "unit_vec": condition_dict["unit_vec"],
                                                                         "keyword": condition_dict["keyword"]
                                                                         }
                                                               })


def generate_googlenews_eventId_with_HotWord(baiduHotWord):
    for element in baiduHotWord['elements']:
        eventCount = 0
        top_story = ''
        if type(element) is list:
            events = fetch_docs_by_tags(True, element, False)
        else:
            events = fetch_docs_by_tags(True, [element], False)

        events_list = []
        for events_elem in events:
            if "text" in events_elem.keys():
                events_list.append(events_elem)
        if len(events_list) < 2:
            continue
        events=filter_unrelate_news(events_list, events_list[0])
        url = events[0]['_id']

        if len(events) < 2:
            continue
        for story in events:
            if "eventId" in story.keys():
                if "eventId_detail" in story.keys():
                    eventId_detail = story["eventId_detail"]
                else:
                    eventId_detail = [story["eventId"]]
                eventId_detail.append(url)
                if "in_tag_detail" in story.keys():
                    in_tag_detail = story["in_tag_detail"]
                else:
                    in_tag_detail = story["in_tag"]
                in_tag_detail.append(",")
                in_tag_detail.extend(element)
                set_googlenews_by_url_with_field_and_value_dict(story["sourceUrl"],{"in_tag": element
                                                                            , "in_tag_detail": in_tag_detail
                                                                            , "eventId": url
                                                                            , "eventId_detail": eventId_detail
                                                                            , "similarity": story["similarity"]
                                                                            , "unit_vec": story["unit_vec"]
                                                                            , "keyword": story["keyword"]

                                                                              })

            else:
                set_googlenews_by_url_with_field_and_value_dict(story["sourceUrl"],{"in_tag": element
                                                                            , "in_tag_detail": element
                                                                            , "eventId": url
                                                                            , "eventId_detail": [url]
                                                                            , "similarity": story["similarity"]
                                                                            , "unit_vec": story["unit_vec"]
                                                                            , "keyword": story["keyword"]
                                                                              })

            eventCount += 1
        print 'found topic events count ===>' , eventCount


def generate_news_eventId_with_HotWord(baiduHotWord):
    for element in baiduHotWord['elements']:

        for channelId in range(16):
            events = fetch_news_docs_by_tags(channelId, True, element, False)
            events_list = []
            for events_elem in events:
                text=""
                if "content" in events_elem.keys():
                    content = events_elem["content"]
                    index = 0
                    for content_elem in content:
                        if str(index) in content_elem.keys():
                            content_elem_dict = content_elem[str(index)]
                        else:
                            index +=1
                            continue
                        index +=1
                        if "txt" in content_elem_dict.keys():
                            text += content_elem_dict["txt"]
                if text != "":
                    events_elem["text"] = text
                    events_list.append(events_elem)

            if len(events_list) < 2:
                continue
            events=filter_unrelate_news(events_list, events_list[0])
            if len(events) < 2:
                continue
            url = events[0]['source_url']
            eventCount = 0
            for story in events:
                if "eventId" in story.keys():
                    if "eventId_detail" in story.keys():
                        eventId_detail = story["eventId_detail"]
                    else:
                        eventId_detail = [story["eventId"]]
                    eventId_detail.append(url)
                    if "in_tag_detail" in story.keys():
                        in_tag_detail = story["in_tag_detail"]
                    else:
                        in_tag_detail = story["in_tag"]
                    in_tag_detail.append(",")
                    in_tag_detail.extend(element)
                    set_news_by_url_with_field_and_value_dict(story["source_url"],{"in_tag": element
                                                                            , "in_tag_detail": in_tag_detail
                                                                            , "eventId": url
                                                                            , "eventId_detail": eventId_detail
                                                                            , "similarity": story["similarity"]
                                                                            , "unit_vec": story["unit_vec"]
                                                                            , "keyword": story["keyword"]

                                                                              })

                else:
                    set_news_by_url_with_field_and_value_dict(story["source_url"],{"in_tag": element
                                                                            , "in_tag_detail": element
                                                                            , "eventId": url
                                                                            , "eventId_detail": [url]
                                                                            , "similarity": story["similarity"]
                                                                            , "unit_vec": story["unit_vec"]
                                                                            , "keyword": story["keyword"]
                                                                              })

                eventCount += 1
            print 'found topic events count ===>' , eventCount

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
    for arg in sys.argv[1:]:
        print arg
        if arg == 'ClusterGogoleNews':
            print "ClusterGogoleNews start"
            while True:
                baiduHotWord = load_baiduHotWord()
                generate_googlenews_eventId_with_HotWord(baiduHotWord)
                logging.warn("===============this round of ClusterGogoleNewsWithbaiduHotWord complete====================")
                time.sleep(3600*4)
        elif arg == 'ClusterNews':
            print "ClusterNews start"
            while True:
                baiduHotWord = load_baiduHotWord()
                generate_news_eventId_with_HotWord(baiduHotWord)
                logging.warn("===============this round of ClusterNewsWithbaiduHotWord complete====================")
                time.sleep(3600*4)

    # elements = pre_load_elementary()
    # baiduHotWord = load_baiduHotWord()
    # baiduHotWord = generate_eventId_with_HotWord(baiduHotWord)
    # update_event(elements)
    #task()






