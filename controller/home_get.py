# coding=utf-8

from config import dbConn
from weibo import weibo_relate_docs_get, user_info_get
import json
import datetime, time
import operator
import pymongo
from utils import get_start_end_time
from pymongo.read_preferences import ReadPreference
from channel_get import fetch_channel, newsFetch_channel,loadMoreFetchContent
from para_sim.TextRank4ZH.gist import Gist
import task.requests_with_sleep as requests
# from content_get import Get_Relate_docs
from AI_funcs.sen_compr.text_handler import SentenceCompressor
import re
import tornado.gen


conn = pymongo.MongoReplicaSetClient("h44:27017, h213:27017, h241:27017", replicaSet="myset",
                                     read_preference=ReadPreference.SECONDARY)

mapOfSourceName = {"weibo": "微博",
                   "wangyi": "wangyi",
                   "xinlang": "xinlang",
                   "zhihu": "zhihu"}

DBStore = dbConn.GetDateStore()

special_source = ["观察", "网易"]


@tornado.gen.coroutine
def homeContentFetch(options):
    """

    :rtype :
    """
    # updateTime = ''
    page = 1
    limit = 10
    # if "updateTime" in options.keys():
    #     updateTime = options["updateTime"]
    if "page" in options.keys():
        page = options["page"]
    if 'limit' in options.keys():
        limit = options["limit"]
    if 'timing' in options.keys():
        timing = options['timing']
    else:
        timing = None

    if 'date' in options.keys():
        date = options["date"]
    else:
        date = None

    if 'type' in options.keys():
        type = options["type"]
    else:
        type = None

    if 'timefeedback' in options.keys():
        timefeedback = options['timefeedback']
    else:
        timefeedback = None

    channelId = options.get("channelId", None)

    conn = DBStore._connect_news

    if not timing and not date and not type and not channelId:

        docs = conn['news_ver2']['googleNewsItem'].find({"isOnline": 1}).sort([("createTime", -1)]).skip(
            (page - 1) * limit).limit(limit)
        undocs_list = []

        # elif not timing:

        # request_time, next_update_time, next_update_type, history_date, upate_frequency = get_time_type_date_freq()

    elif date and type:

        day_night = get_day_night_time(date, type)
        docs = []
        for day_night_elem in day_night:
            start_time = day_night_elem[0]
            start_time_yes = start_time + datetime.timedelta(days=-2)
            end_time = day_night_elem[1]
            start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
            end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
            start_time_yes = start_time_yes.strftime('%Y-%m-%d %H:%M:%S')

            doc = conn["news_ver2"]["googleNewsItem"].find({"isOnline": 1, "createTime": {"$gte": start_time,
                                                                                          "$lt": end_time}}).sort(
                [("createTime", -1)])

            for doc_elem in doc:
                docs.append(doc_elem)
            undocs = conn["news_ver2"]["googleNewsItem"].find(
                {"$or": [{"isOnline": 0}, {"isOnline": {"$exists": 0}}], "createTime": {"$gte": start_time_yes},
                 "eventId": {"$exists": 1}}).sort([("createTime", -1)])
            undocs_list = extratInfoInUndocs(undocs)

        docs = sorted(docs, key=operator.itemgetter("createTime"), reverse=True)

    elif channelId:
        docs = fetch_channel(int(channelId), page, limit)
        undocs_list = []

    else:
        # start_time, end_time = get_start_end_time()
        start_time, end_time, update_time, update_type, upate_frequency = get_start_end_time(halfday=True)
        start_time_yes = start_time + datetime.timedelta(days=-2)
        start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
        end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
        start_time_yes = start_time_yes.strftime('%Y-%m-%d %H:%M:%S')


        # docs = conn["news_ver2"]["googleNewsItem"].find({"isOnline": 1, "createTime": {"$gte": start_time,
        #                                                                                "$lt": end_time}}).sort([("createTime", -1)])

        docs = conn["news_ver2"]["googleNewsItem"].find({"isOnline": 1}).sort([("createTime", -1)]).limit(50)

        # undocs = conn["news_ver2"]["googleNewsItem"].find(
        #     {"$or": [{"isOnline": 0}, {"isOnline": {"$exists": 0}}], "createTime": {"$gte": start_time_yes},
        #      "eventId": {"$exists": 1}}).sort([("createTime", -1)])
        # undocs_list = extratInfoInUndocs(undocs)
        undocs_list = []

        # db.googleNewsItem.find({'isOnline':{"$exists": 0},'createTime':{"$gte": '2015-05-15 18:00:00',"$lt": '2015-05-16 06:00:00'}, "eventId": {"$exists": 1} }).sort( { createTime: -1 } ).count()

    special_list = []
    nospecial_list = []

    results_docs = reorganize_news(docs, not channelId)

    for doc in results_docs:
        isWeiboFlag = 0
        isBaikeFlag = 0
        isZhihuFlag = 0
        isImgWallFlag = 0
        isCommentsFlag = 0

        sublist = []
        reorganize_num = 0
        filter_url = []
        if "sublist" in doc.keys():
            sublist = doc["sublist"]
            reorganize_num = reorganize_num + len(sublist)
            set_googlenews_by_url_with_field_and_value(doc['sourceUrl'], "reorganize", sublist)
            for subelem in sublist:
                filter_url.append(subelem["url"])
            del doc["sublist"]

        if "sourceUrl" not in doc.keys():
            print "error"
            continue

        url = doc['sourceUrl']
        title = doc["title"]
        sourceSiteName = doc["sourceSiteName"]

        # baidu_news_num = count_relate_baidu_news(url)

        relate = []
        special_flag = True
        # 标记放到前边的新闻
        if sourceSiteName[:2] in special_source:
            doc["special"] = 1
        elif "special" in doc.keys():
            special_flag = False
        else:
            doc["special"] = 400
            special_flag = False

        if "sourceSiteName" in doc.keys():
            sourceSitename = doc["sourceSiteName"]
            doc["category"] = sourceSitename[2:4]
        else:
            continue
        # 不取没有相关的
        # if not relate:
        #     continue



        if "imgUrls" in doc.keys():
            if not doc["imgUrls"]:
                continue
            if len(doc["imgUrls"]) > 0:
                doc["imgUrl"] = doc["imgUrls"]
                del doc["imgUrls"]

        if "content" in doc.keys():
            del doc["content"]

        if "abstract" in doc.keys():
            del doc["abstract"]

        if "douban" in doc.keys():
            del doc["douban"]

        if "baike" in doc.keys():
            isBaikeFlag = 1
            del doc["baike"]

        if "baiduSearch" in doc.keys():
            del doc["baiduSearch"]

        if "imgWall" in doc.keys():
            if doc["imgWall"]:
                isImgWallFlag = 1

            del doc["imgWall"]

        # 相关新闻每一个来源 选一条
        if relate:
            distinctList, distinctNum, distinct_response_urls, otherNum = GetRelateNews(relate, filter_url)

        else:
            distinctList = []
            distinctNum = 0
            distinct_response_urls = []
            otherNum = 0

        sublist.extend(distinctList)

        if 'eventId' in doc.keys():
            eventId = doc["eventId"]
            for undocs_elem in undocs_list:
                if eventId == undocs_elem["eventId"] and undocs_elem["url"] not in distinct_response_urls and \
                                undocs_elem["url"] not in filter_url:
                    sublist.append(undocs_elem)
                else:
                    continue


        sublist = delete_duplicate_sulist(sublist)

        if "weibo" in doc.keys():
            weibo = doc["weibo"]
            if weibo:
                isWeiboFlag = 1

            if isinstance(weibo, dict):
                if "sourceName" in weibo:
                    weibo["sourceSitename"] = weibo["sourceName"]
                    del weibo["sourceName"]
                    sublist.append(weibo)

                del doc["weibo"]

            elif isinstance(weibo, list) and len(weibo) > 0:
                weibo = weibo[0]
                if "sourceName" in weibo:
                    weibo["sourceSitename"] = weibo["sourceName"]
                    del weibo["sourceName"]
                sublist.append(weibo)

                del doc["weibo"]

        if "zhihu" in doc.keys():
            zhihu = doc["zhihu"]
            if zhihu:
                isZhihuFlag = 1

            # if isinstance(zhihu, dict):
            #     zhihu["sourceSitename"] = "zhihu"
            #     sublist.append(zhihu)
            #     del doc["zhihu"]
            #
            # elif isinstance(doc["zhihu"], list) and len(doc["zhihu"]) > 0 :
            #     zhihu = doc["zhihu"][0]
            #     zhihu["sourceSitename"] = "zhihu"
            #     sublist.append(zhihu)
            #     del doc["zhihu"]
            del doc["zhihu"]

        # doc_crawl_comment = conn["news_ver2"]["commentItems"].find_one({"relateUrl": url})
        # doc_point_comment = conn["news_ver2"]["pointItem"].find_one({"sourceUrl": url})
        # if doc_crawl_comment:
        #     if doc_crawl_comment["comments"]:
        #         isCommentsFlag = 1
        #
        # if doc_point_comment:
        #     if doc_point_comment["srcText"]:
        #         isCommentsFlag = 1

        sublist = add_abs_to_sublist(sublist)
        for sublist_elem in sublist:
            if "text" in sublist_elem.keys():
                del sublist_elem["text"]

        doc["sublist"] = sublist
        # doc["otherNum"] = otherNum + baidu_news_num + reorganize_num
        # docs_relate = conn["news"]["AreaItems"].find({"relateUrl": url}).sort([("updateTime", -1)]).limit(10)
        docs_relate = []
        allrelate = Get_Relate_docs(doc, docs_relate, filterurls=[])
        doc["otherNum"] = len(allrelate)

        if "relate" in doc.keys():
            if doc["relate"]:
                relate = doc["relate"]
                relate = del_dup_relatedoc(relate, sublist)
            del doc["relate"]

        doc["urls_response"] = distinct_response_urls  # 返回的urls，用于获取其他相关新闻时过滤掉 这几条已经有的新闻

        doc["isWeiboFlag"] = isWeiboFlag
        doc["isBaikeFlag"] = isBaikeFlag
        doc["isZhihuFlag"] = isZhihuFlag
        doc["isImgWallFlag"] = isImgWallFlag
        doc["isCommentsFlag"] = isCommentsFlag

        if "paragraph" in doc.keys():
            del doc["paragraph"]

        if "keyword" in doc.keys():
            del doc["keyword"]

        if "auto_tags" in doc.keys():
            del doc["auto_tags"]

        if "compress" in doc.keys():
            del doc["compress"]

        if "sentence_cut" in doc.keys():
            del doc["sentence_cut"]

        if "description" in doc.keys():
            del doc["description"]

        if "reorganize" in doc.keys():
            del doc["reorganize"]


        if "in_tag_detail" in doc.keys():
            del doc["in_tag_detail"]

        if "text" in doc.keys():
            del doc["text"]

        if "in_tag" in doc.keys():
            del doc["in_tag"]

        if "relate_opinion" in doc.keys():
            del doc["relate_opinion"]

        if "ne" in doc.keys():
            del doc["ne"]

        if "similarity" in doc.keys():
            del doc["similarity"]

        if "gist" in doc.keys():
            del doc["gist"]

        if "eventId_detail" in doc.keys():
            del doc["eventId_detail"]

        if "duplicate_check" in doc.keys():
            del doc["duplicate_check"]

        if "unit_vec" in doc.keys():
            del doc["unit_vec"]

        if "sentence" in doc.keys():
            del doc["sentence"]

        # if timefeedback:
        #     doc["timefeedback"]=timefeedback_dict

        # docs_return.append(doc)
        if special_flag:
            special_list.append(doc)
        else:
            nospecial_list.append(doc)

    special_list = sorted(special_list, key=operator.itemgetter("createTime"))
    docs_return = special_list + nospecial_list
    # if timing:
    # docs_return = sorted(docs_return, key=operator.itemgetter("special"))

    # print docs_return
    # return docs_return
    raise tornado.gen.Return(docs_return)

def newsHomeContentFetch(options):
    """

    :rtype :
    """
    # updateTime = ''
    page = 1
    limit = 10
    # if "updateTime" in options.keys():
    #     updateTime = options["updateTime"]
    if "page" in options.keys():
        page = options["page"]
    if 'limit' in options.keys():
        limit = options["limit"]
    if 'timing' in options.keys():
        timing = options['timing']
    else:
        timing = None

    if 'date' in options.keys():
        date = options["date"]
    else:
        date = None

    if 'type' in options.keys():
        type = options["type"]
    else:
        type = None

    if 'timefeedback' in options.keys():
        timefeedback = options['timefeedback']
    else:
        timefeedback = None

    channelId = options.get("channelId", None)

    conn = DBStore._connect_news

    if not timing and not date and not type and not channelId:

        docs = conn['news_ver2']['googleNewsItem'].find({"isOnline": 1}).sort([("createTime", -1)]).skip(
            (page - 1) * limit).limit(limit)
        undocs_list = []

        # elif not timing:

        # request_time, next_update_time, next_update_type, history_date, upate_frequency = get_time_type_date_freq()

    elif date and type:

        day_night = get_day_night_time(date, type)
        docs = []
        for day_night_elem in day_night:
            start_time = day_night_elem[0]
            start_time_yes = start_time + datetime.timedelta(days=-1)
            end_time = day_night_elem[1]
            start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
            end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
            start_time_yes = start_time_yes.strftime('%Y-%m-%d %H:%M:%S')

            doc = conn["news_ver2"]["googleNewsItem"].find({"isOnline": 1, "createTime": {"$gte": start_time,
                                                                                          "$lt": end_time}}).sort(
                [("createTime", -1)])

            for doc_elem in doc:
                docs.append(doc_elem)
            undocs = conn["news_ver2"]["googleNewsItem"].find({"$or": [{"isOnline": 0}, {"isOnline": {"$exists": 0}}],
                                                               "createTime": {"$gte": start_time_yes, "$lt": end_time},
                                                               "eventId": {"$exists": 1}}).sort([("createTime", -1)])
            undocs_list = extratInfoInUndocs(undocs)

        docs = sorted(docs, key=operator.itemgetter("createTime"), reverse=True)

    elif channelId:
        docs = newsFetch_channel(int(channelId), page, limit)
        undocs_list = []
        if channelId >= 0:
            return docs
    else:
        # start_time, end_time = get_start_end_time()
        start_time, end_time, update_time, update_type, upate_frequency = get_start_end_time(halfday=True)
        start_time_yes = start_time + datetime.timedelta(days=-1)
        start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
        end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
        start_time_yes = start_time_yes.strftime('%Y-%m-%d %H:%M:%S')

        docs = conn["news_ver2"]["googleNewsItem"].find({"isOnline": 1, "createTime": {"$gte": start_time,
                                                                                       "$lt": end_time}}).sort(
            [("createTime", -1)])

        undocs = conn["news_ver2"]["googleNewsItem"].find({"$or": [{"isOnline": 0}, {"isOnline": {"$exists": 0}}],
                                                           "createTime": {"$gte": start_time_yes, "$lt": end_time},
                                                           "eventId": {"$exists": 1}}).sort([("createTime", -1)])
        undocs_list = extratInfoInUndocs(undocs)

        # db.googleNewsItem.find({'isOnline':{"$exists": 0},'createTime':{"$gte": '2015-05-15 18:00:00',"$lt": '2015-05-16 06:00:00'}, "eventId": {"$exists": 1} }).sort( { createTime: -1 } ).count()

    special_list = []
    nospecial_list = []

    results_docs = reorganize_news(docs, not channelId)

    for doc in results_docs:
        isWeiboFlag = 0
        isBaikeFlag = 0
        isZhihuFlag = 0
        isImgWallFlag = 0
        isCommentsFlag = 0

        sublist = []
        reorganize_num = 0
        filter_url = []
        if "sublist" in doc.keys():
            sublist = doc["sublist"]
            reorganize_num = reorganize_num + len(sublist)
            set_googlenews_by_url_with_field_and_value(doc['sourceUrl'], "reorganize", sublist)
            for subelem in sublist:
                filter_url.append(subelem["url"])
            del doc["sublist"]

        if "sourceUrl" not in doc.keys():
            print "error"
            continue

        url = doc['sourceUrl']
        title = doc["title"]
        sourceSiteName = doc["sourceSiteName"]

        # baidu_news_num = count_relate_baidu_news(url)

        relate = []
        special_flag = True
        # 标记放到前边的新闻
        if sourceSiteName[:2] in special_source:
            doc["special"] = 1
        elif "special" in doc.keys():
            special_flag = False
        else:
            doc["special"] = 400
            special_flag = False

        if "sourceSiteName" in doc.keys():
            sourceSitename = doc["sourceSiteName"]
            doc["category"] = sourceSitename[2:4]
        else:
            continue
        # 不取没有相关的
        # if not relate:
        #     continue



        if "imgUrls" in doc.keys():
            if not doc["imgUrls"]:
                continue
            if len(doc["imgUrls"]) > 0:
                doc["imgUrl"] = doc["imgUrls"]
                del doc["imgUrls"]

        if "content" in doc.keys():
            del doc["content"]

        if "abstract" in doc.keys():
            del doc["abstract"]

        if "douban" in doc.keys():
            del doc["douban"]

        if "baike" in doc.keys():
            isBaikeFlag = 1
            del doc["baike"]

        if "baiduSearch" in doc.keys():
            del doc["baiduSearch"]

        if "imgWall" in doc.keys():
            if doc["imgWall"]:
                isImgWallFlag = 1

            del doc["imgWall"]

        # 相关新闻每一个来源 选一条
        if relate:
            distinctList, distinctNum, distinct_response_urls, otherNum = GetRelateNews(relate, filter_url)

        else:
            distinctList = []
            distinctNum = 0
            distinct_response_urls = []
            otherNum = 0

        sublist.extend(distinctList)

        if 'eventId' in doc.keys():
            eventId = doc["eventId"]
            for undocs_elem in undocs_list:
                if eventId == undocs_elem["eventId"] and undocs_elem["url"] not in distinct_response_urls and \
                                undocs_elem["url"] not in filter_url:
                    sublist.append(undocs_elem)
                else:
                    continue

        if "weibo" in doc.keys():
            weibo = doc["weibo"]
            if weibo:
                isWeiboFlag = 1

            if isinstance(weibo, dict):
                if "sourceName" in weibo:
                    weibo["sourceSitename"] = weibo["sourceName"]
                    del weibo["sourceName"]
                    sublist.append(weibo)

                del doc["weibo"]

            elif isinstance(weibo, list) and len(weibo) > 0:
                weibo = weibo[0]
                if "sourceName" in weibo:
                    weibo["sourceSitename"] = weibo["sourceName"]
                    del weibo["sourceName"]
                sublist.append(weibo)

                del doc["weibo"]

        if "zhihu" in doc.keys():
            zhihu = doc["zhihu"]
            if zhihu:
                isZhihuFlag = 1


            # if isinstance(zhihu, dict):
            #     zhihu["sourceSitename"] = "zhihu"
            #     sublist.append(zhihu)
            #     del doc["zhihu"]
            #
            # elif isinstance(doc["zhihu"], list) and len(doc["zhihu"]) > 0 :
            #     zhihu = doc["zhihu"][0]
            #     zhihu["sourceSitename"] = "zhihu"
            #     sublist.append(zhihu)
            #     del doc["zhihu"]
            del doc["zhihu"]

        doc_comment = conn["news_ver2"]["commentItems"].find_one({"relateUrl": url})
        if doc_comment:
            if doc_comment["comments"]:
                isCommentsFlag = 1

        sublist = add_abs_to_sublist(sublist)


        doc["sublist"] = sublist
        # doc["otherNum"] = otherNum + baidu_news_num + reorganize_num
        docs_relate = conn["news"]["AreaItems"].find({"relateUrl": url}).sort([("updateTime", -1)]).limit(10)
        allrelate = Get_Relate_docs(doc, docs_relate, filterurls=[])
        doc["otherNum"] = len(allrelate)

        if "relate" in doc.keys():
            if doc["relate"]:
                relate = doc["relate"]
                relate = del_dup_relatedoc(relate, sublist)
            del doc["relate"]

        doc["urls_response"] = distinct_response_urls  # 返回的urls，用于获取其他相关新闻时过滤掉 这几条已经有的新闻

        doc["isWeiboFlag"] = isWeiboFlag
        doc["isBaikeFlag"] = isBaikeFlag
        doc["isZhihuFlag"] = isZhihuFlag
        doc["isImgWallFlag"] = isImgWallFlag
        doc["isCommentsFlag"] = isCommentsFlag

        # if timefeedback:
        #     doc["timefeedback"]=timefeedback_dict

        # docs_return.append(doc)
        if special_flag:
            special_list.append(doc)
        else:
            nospecial_list.append(doc)




    special_list = sorted(special_list, key=operator.itemgetter("createTime"))
    docs_return = special_list + nospecial_list
    # if timing:
    # docs_return = sorted(docs_return, key=operator.itemgetter("special"))

    # print docs_return
    return docs_return


def LoadMoreNewsContent(options):
    if "type" in options.keys():
        type = options["type"]
    if 'time' in options.keys():
        time = options["time"]
    if 'limit' in options.keys():
        limit = options['limit']
    if 'channel_id' in options.keys():
        channel_id = options['channel_id']
    if 'id' in options.keys():
        id = options['id']
    docs = loadMoreFetchContent(int(channel_id), type, time, limit,id)
    return docs


def count_relate_baidu_news(url):
    conn = DBStore._connect_news
    num = conn["news"]["AreaItems"].find({"relateUrl": url}).count()

    return num


# TODO android has a bug to list the channel item ,so just don't do sort for channel items.
def reorganize_news(docs, is_channel=False):
    results_docs = []
    eventId_dict = {}

    for doc in docs:
        if 'eventId' in doc.keys():
            if doc['eventId'] in eventId_dict.keys():
                eventId_dict[doc['eventId']].append(doc)
            else:
                eventId_dict[doc['eventId']] = [doc]
        else:
            results_docs.append(doc)

    for (eventId, eventList) in eventId_dict.items():
        results_docs.append(constructEvent(eventList))

    results_docs = sorted(results_docs, key=operator.itemgetter("createTime"), reverse=not is_channel)
    return results_docs


def constructEvent(eventList):
    result_doc = {}
    sublist = []
    imgUrl_ex = []
    is_notin_flag = True
    for eventElement in eventList:
        if eventElement['eventId'] == eventElement["_id"]:
            result_doc = eventElement
            imgUrl_ex.append(eventElement['imgUrls'])
            is_notin_flag = False

        else:
            subElement = {}
            if 'text' not in eventElement.keys():
                subElement={'sourceSitename': eventElement['originsourceSiteName'], 'url': eventElement['_id'], 'title': eventElement['title'], 'img': eventElement['imgUrls'], 'similarity': eventElement["similarity"], 'unit_vec': eventElement["unit_vec"]}
            elif 'gist' not in eventElement.keys():
                subElement={'sourceSitename': eventElement['originsourceSiteName'], 'url': eventElement['_id'], 'title': eventElement['title'], 'img': eventElement['imgUrls'], 'text': eventElement['text'], 'similarity': eventElement["similarity"], 'unit_vec': eventElement["unit_vec"]}
            elif 'compress' not in eventElement.keys():
                subElement={'sourceSitename': eventElement['originsourceSiteName'], 'url': eventElement['_id'], 'title': eventElement['title'], 'img': eventElement['imgUrls'], 'text': eventElement['text'], 'gist': eventElement['gist'], 'similarity': eventElement["similarity"], 'unit_vec': eventElement["unit_vec"]}
            else:
                subElement={'sourceSitename': eventElement['originsourceSiteName'], 'url': eventElement['_id'], 'title': eventElement['title'], 'img': eventElement['imgUrls'], 'text': eventElement['text'], 'gist': eventElement['gist'], 'similarity': eventElement["similarity"], 'unit_vec': eventElement["unit_vec"], 'compress': eventElement["compress"]}



            sublist.append(subElement)
            result_doc["special"] = 9
            imgUrl_ex.append(eventElement['imgUrls'])

    if is_notin_flag:
        return eventList[0]

    if "special" in result_doc.keys():
        result_doc["sublist"] = sublist
        result_doc["imgUrl_ex"] = imgUrl_ex

    return result_doc


# 相关新闻的获取
def GetRelateNews(relate, filter_url):
    # if not relate:
    #     return

    left_relate = relate["left"]
    mid_relate = relate["middle"]
    bottom_relate = relate["bottom"]
    opinion = relate["opinion"]
    deep_relate = relate["deep_report"]

    sourceNameSet = set()
    distinctList = []
    distinct_response_urls = []
    sumList = []

    total_relate = [left_relate, mid_relate, bottom_relate, opinion, deep_relate]

    for relate in total_relate:
        for e in relate:
            if not e["title"]:
                continue
            if e["sourceSitename"] not in sourceNameSet and e["url"] not in filter_url:
                e["user"] = ""
                distinctList.append(e)
                distinct_response_urls.append(e["url"])
                sourceNameSet.add(e["sourceSitename"])

            sumList.append(e)

    otherNum = len(sumList) - len(distinctList)
    return distinctList, len(distinctList), distinct_response_urls, otherNum


def GetWeibos(title, num):
    if num == 0:
        return

    if num == 1:
        weibo = GetOneWeibo(title)
        return weibo

    weibos = weibo_relate_docs_get.search_relate_docs()
    weibos = json.loads(weibos)

    index = 0
    for weibo in weibos:
        if index == num:
            return weibos[:index]

        weibo_id = weibo["weibo_id"]
        user = user_info_get.get_weibo_user(weibo_id)
        weibos[index]["user"] = user["name"]


def GetOneWeibo(title):
    weibos = weibo_relate_docs_get.search_relate_docs(title, 1)
    weibos = json.loads(weibos)

    if len(weibos) <= 0:
        return

    if "error" in weibos[0].keys():
        return

    weibo = weibos[0]
    weibo_id = weibo["weibo_id"]
    user = user_info_get.get_weibo_user(weibo_id)
    weibo["user"] = user["name"]

    return weibo


def get_time_type_date_freq(update_time, update_type, upate_frequency):
    now = datetime.datetime.now()
    tommorow = now + datetime.timedelta(days=1)
    request_time = int(convertTimestrtosecond(now) * 1000)
    next_update_time = int(convertTimestrtosecond(update_time) * 1000) - request_time
    next_update_type = update_type
    next_update_freq = upate_frequency
    if next_update_type == 1:
        history_date = get_history_date(now)
    else:
        history_date = get_history_date(tommorow)

    return request_time, next_update_time, next_update_type, history_date, next_update_freq


def get_time():
    now = datetime.datetime.now()
    tommorow = now + datetime.timedelta(days=1)
    request_time = int(convertTimestrtosecond(now) * 1000)
    return request_time


def convertTimestrtosecond(date):
    return timestamp(date)


def timestamp(date):
    return time.mktime(date.timetuple())


def get_history_date(now):
    format = '%Y-%m-%d'
    history_date = []
    for i in list(reversed(range(4))):
        yesterday = now + datetime.timedelta(days=-i)
        defaultTimestr = yesterday.strftime(format)
        history_date.append(defaultTimestr)

    return history_date


def get_day_night_time(date, type):
    date = datetime.datetime.strptime(date, '%Y-%m-%d')
    yesterday = date + datetime.timedelta(days=-1)
    yesterday_year = yesterday.year
    yesterday_month = yesterday.month
    yesterday_day = yesterday.day

    today_year = date.year
    today_month = date.month
    today_day = date.day

    tomorrow = date + datetime.timedelta(days=1)
    tomorrow_year = tomorrow.year
    tomorrow_month = tomorrow.month
    tomorrow_day = tomorrow.day

    # 黑夜 if hour in range(0,6):    #取昨天6点-昨天18点 更新时间为今天早上6点
    day_night = []

    if type == '0':  # 0代表白天 1代表黑夜

        day_start_time = datetime.datetime(yesterday_year, yesterday_month, yesterday_day, 18, 0)
        day_end_time = datetime.datetime(today_year, today_month, today_day, 6, 0)
        day_night.append([day_start_time, day_end_time])

    elif type == '1':

        # night1_start_time = datetime.datetime(yesterday_year, yesterday_month, yesterday_day, 6, 0)
        # night1_end_time = datetime.datetime(yesterday_year, yesterday_month, yesterday_day, 18, 0)
        # 白天 elif hour in range(6,18): #取昨天18点~今天6点 更新时间为今天18点
        # 黑夜 elif hour in range(18,24): #取今天6-今天18点 更新时间为明天6点
        night2_start_time = datetime.datetime(today_year, today_month, today_day, 6, 0)
        night2_end_time = datetime.datetime(today_year, today_month, today_day, 18, 0)
        # day_night.append([night1_start_time,night1_end_time])
        day_night.append([night2_start_time, night2_end_time])


    elif type == '99':
        now = datetime.datetime.now()
        start_time = datetime.datetime(yesterday_year, yesterday_month, yesterday_day, 0, 0)
        end_time = now
        day_night.append([start_time, end_time])

    return day_night


def set_googlenews_by_url_with_field_and_value(url, field, value):
    conn["news_ver2"]["googleNewsItem"].update({"sourceUrl": url}, {"$set": {field: value}})


def del_dup_relatedoc(relate, sublist):
    left_relate = relate["left"]
    mid_relate = relate["middle"]
    bottom_relate = relate["bottom"]
    opinion = relate["opinion"]
    deep_relate = relate["deep_report"]
    distinctdict = {"left": [], "middle": [], "bottom": [], "opinion": [], "deep_report": []}
    titleSet = set()
    urlSet = set()
    for sublist_elem in sublist:
        titleSet.add(sublist_elem["title"])
        urlSet.add(sublist_elem["url"])

    total_relate = [left_relate, mid_relate, bottom_relate, opinion, deep_relate]
    i = 0
    for relate in total_relate:
        for e in relate:
            if not e["title"]:
                continue
            if e["title"] in titleSet or e["url"] in urlSet:
                continue
            if i == 0:
                distinctdict["left"].append(e)
            if i == 1:
                distinctdict["middle"].append(e)
            if i == 2:
                distinctdict["bottom"].append(e)
            if i == 3:
                distinctdict["opinion"].append(e)
            if i == 4:
                distinctdict["deep_report"].append(e)
        i = i + 1

    return distinctdict


def extratInfoInUndocs(undocs):
    undocs_list = []
    for doc in undocs:
        url = doc["sourceUrl"]
        sourceSitename = doc["originsourceSiteName"]
        if 'imgUrls' in doc.keys():
            img = doc["imgUrls"]
        else:
            img = ""
        title = doc["title"]
        eventId = doc["eventId"]
        if 'text' not in doc.keys():
            undocs_list.append({"url": url, "sourceSitename": sourceSitename, "img": img, "title": title, "eventId": eventId, 'similarity': doc["similarity"], 'unit_vec': doc["unit_vec"]})
        elif 'gist' not in doc.keys():
            undocs_list.append({"url": url, "sourceSitename": sourceSitename, "img": img, "title": title, "eventId": eventId, "text": doc["text"], 'similarity': doc["similarity"], 'unit_vec': doc["unit_vec"]})
        elif 'compress' not in doc.keys():
            undocs_list.append({"url": url, "sourceSitename": sourceSitename, "img": img, "title": title, "eventId": eventId, "text": doc["text"], "gist": doc["gist"], 'similarity': doc["similarity"], 'unit_vec': doc["unit_vec"]})
        else:
            undocs_list.append({"url": url, "sourceSitename": sourceSitename, "img": img, "title": title, "eventId": eventId, "text": doc["text"], "gist": doc["gist"], 'similarity': doc["similarity"], 'unit_vec': doc["unit_vec"], 'compress': doc["compress"]})
    return undocs_list


def add_abs_to_sublist(sublist):
    result_list = []
    for sublist_elem in sublist:
        if sublist_elem['sourceSitename'] == 'weibo' or 'text' not in sublist_elem.keys() or 'gist' not in sublist_elem.keys():
            result_list.append(sublist_elem)
            continue
        else:
            text = sublist_elem['text']
            gist = sublist_elem['gist']
            # gist = quote(str(gist))
            # title = get_compression_result(gist)
            # sublist_elem['title'] = Gist().get_gist_str(text)
            if "compress" not in sublist_elem.keys():
                sublist_elem['title'] = gist
            else:
                sublist_elem['title'] = sublist_elem["compress"]

            result_list.append(sublist_elem)
    return result_list


def delete_duplicate_sulist(sublist):
    result_list = []
    for sublist_elem in sublist:
        if "unit_vec" not in sublist_elem.keys():
            result_list.append(sublist_elem)
            continue
        is_filter_flag = 0
        for compare_elem in result_list:
            if "unit_vec" not in compare_elem.keys():
                continue
            elem_unit_vec = sublist_elem["unit_vec"]
            compare_elem_unit_vec = compare_elem["unit_vec"]
            sims = calculate_sim(elem_unit_vec, compare_elem_unit_vec)
            if sims > 0.9:
                is_filter_flag = 1
                break
        if is_filter_flag == 0:
            if sublist_elem["similarity"]<0.95:
                result_list.append(sublist_elem)
    return result_list

def calculate_sim(elem_unit_vec, compare_elem_unit_vec):
    sims_value = sum([elem_unit_vec[i]*compare_elem_unit_vec[i] for i in range(len(elem_unit_vec))])
    same_word_num = sum([(1 if elem_unit_vec[i]>0 else 0)*(1 if compare_elem_unit_vec[i]>0 else 0) for i in range(len(elem_unit_vec))])
    if same_word_num>=2:
        sims = sims_value
    else:
        sims = 0.0

    return sims

def Get_Relate_docs(doc, docs_relate, filterurls):
    allrelate = []

    if "reorganize" in doc.keys() and doc["reorganize"]:
        allrelate.extend(doc["reorganize"])

    if "relate" in doc.keys() and doc["relate"]:
        relate = doc["relate"]
        if "reorganize" in doc.keys() and doc["reorganize"]:
            relate = del_dup_relatedoc(relate, doc["reorganize"])
        left_relate = relate["left"]
        mid_relate = relate["middle"]
        bottom_relate = relate["bottom"]
        opinion = relate["opinion"]
        deep_relate = relate["deep_report"]

        allList = [left_relate, mid_relate, bottom_relate, opinion, deep_relate]

        for ones in allList:

            for e in ones:

                relate_url = e["url"]
                # title 为空 跳过
                if 'title' in e.keys():
                    if not e['title']:
                        continue

                if relate_url in filterurls:
                    continue

                # ct_img = Get_by_url(relate_url)
                # #
                # e["img"] = ct_img['img']
                if not "img" in e.keys():
                    e["img"] = ""

                allrelate.append(e)

    for one in docs_relate:
        ls = {}
        url_here = one["sourceUrl"]
        title_here = one["title"]
        sourceSiteName = one["sourceSiteName"]
        updatetime = one["updateTime"]

        imgUrl = ''

        if "imgUrl" in one.keys():
            imgUrls = one["imgUrl"]
            if isinstance(imgUrls, list) and len(imgUrls) > 0:
                imgUrl = imgUrls[-1]
            elif isinstance(imgUrls, dict):
                imgUrl = imgUrls['img']
            elif isinstance(imgUrls, str):
                imgUrl = imgUrls
            elif isinstance(imgUrls, unicode):
                imgUrl = imgUrls.encode('utf-8')


        # if not imgUrl:
        #     continue

        ls["title"] = title_here
        ls["url"] = url_here
        ls["img"] = imgUrl
        ls["sourceSitename"] = sourceSiteName
        ls["updateTime"] = updatetime
        ls['height'] = 75
        ls['width'] = 121

        allrelate.append(ls)

    return allrelate
