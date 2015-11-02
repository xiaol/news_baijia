# coding=utf-8

import json
import pymongo
from pymongo.read_preferences import ReadPreference
import re
import tornado
import tornado.gen
import redis
import random
from  task.data_structure import convertNewsItems, convertGoogleNewsItems
from  content_get import Get_Relate_docs, get_points,count_praise,project_comments_to_paragraph

r = redis.Redis(host='121.41.75.213', port=6379, db=1)

conn = pymongo.MongoReplicaSetClient("h44:27017, h213:27017, h241:27017", replicaSet="myset",
                                     read_preference=ReadPreference.SECONDARY)

@tornado.gen.coroutine
def recommend(deviceId, channelId):
    db = conn.news_ver2
    doc_num = db.recommendItem.count()
    random_num = random.random()*doc_num
    already_visit_set = r.smembers(deviceId)
    if channelId == "TJ0001":
        docs = db.recommendItem.find({"_id":{'$gte': random_num}}).sort("createTime",pymongo.DESCENDING).limit(30)
    else:
        docs = db.recommendItem.find({"channelId":channelId, "_id":{'$gte': random_num}}).sort("createTime",pymongo.DESCENDING).limit(50)
    doc_list = []
    i = 0
    for doc in docs:
        if type(doc["imgUrls"]) != list:
            doc["imgUrls"] = [doc["imgUrls"]]
        if i>=15:
            break
        del doc["_id"]
        if doc["sourceUrl"] in already_visit_set:
            continue
        else:
            doc_list.append(doc)
            r.sadd(deviceId, doc["sourceUrl"])
            i = i +1
    # r.hmset("deviceId",{"googleNewsItems":docs_return})
    raise tornado.gen.Return(doc_list)

@tornado.gen.coroutine
def fetchDetail(newsId, collection):
    if collection == "NewsItem":
        doc = conn["news_ver2"]["NewsItems"].find_one({"newsId": newsId})
        result = convertNewsItems([doc], outFieldFilter = False)[0]
    elif collection == "googleNewsItem":
        doc = conn["news_ver2"]["googleNewsItem"].find_one({"newsId": newsId})
        result = convertGoogleNewsItems([doc], outFieldFilter = False)[0]
    else:
        return
    if not result:
        return
    url = result["sourceUrl"]
    docs_relate = conn["news"]["AreaItems"].find({"relateUrl": url}).sort([("updateTime", -1)]).limit(10)
    doc_comment = conn["news_ver2"]["commentItems"].find_one({"relateUrl": url})
    allrelate = Get_Relate_docs(doc, docs_relate, filterurls=[])
    for relate_elem in allrelate:
        if "text" in relate_elem.keys():
            del relate_elem["text"]

    if "imgUrls" in result.keys():
        result['imgUrl'] = doc['imgUrls']

    result["relate"] = allrelate
    result_points = []

    praise = conn['news_ver2']['praiseItem'].find({'sourceUrl': url})  # ({'uuid': uuid, 'commentId': commentId})
    praise_list = []
    for praise_elem in praise:
        praise_list.append(praise_elem)

    pointsCursor = conn["news_ver2"]["pointItem"].find({"sourceUrl": url}).sort([("type", -1)])
    points_fromdb = get_points(pointsCursor, praise_list, userId, platformType)

    if doc_comment and 'content' in doc:
        if doc_comment["comments"]:
            for doc_comment_elem in doc_comment["comments"]:
                dict_len = len(doc_comment_elem)
                comment_result = doc_comment_elem[str(dict_len)]
                if 'comment_id' in comment_result.keys():
                    # praise_num = praise.find({'commentId': comment_result["comment_id"]}).count()
                    praise_num = count_praise({'commentId': comment_result["comment_id"]}, praise_list)
                    up = int(comment_result['up'])
                    comment_result['up'] = up + praise_num
                if userId and platformType and 'comment_id' in comment_result.keys():
                    isPraiseFlag = count_praise(
                        {'userId': userId, 'platformType': platformType, 'commentId': comment_result["comment_id"]},
                        praise_list)
                    if isPraiseFlag:
                        comment_result['isPraiseFlag'] = 1
                    else:
                        comment_result['isPraiseFlag'] = 0
                else:
                    comment_result['isPraiseFlag'] = 0

            points = project_comments_to_paragraph(doc, doc_comment["comments"])
            result_points.extend(points)
    points_fromdb.extend(result_points)

    paragraph_comment_count = {}
    flag = False
    for point_ele in points_fromdb:
        if point_ele['paragraphIndex'] in paragraph_comment_count:
            paragraph_comment_count[point_ele['paragraphIndex']] += 1
        else:
            paragraph_comment_count[point_ele['paragraphIndex']] = 1
    for point_ele in points_fromdb:
        point_ele['comments_count'] = paragraph_comment_count[point_ele['paragraphIndex']]
        # ariesy 2015-6-17 提取语音弹幕
        if (flag == False and "speech_paragraph" == point_ele["type"] or "speech_doc" == point_ele["type"]):
            flag = True
            result["isdoc"] = True
            result["docUrl"] = point_ele["srcText"]
            result["docTime"] = point_ele["srcTextTime"]
            result["docUserIcon"] = point_ele["userIcon"]
    result["point"] = points_fromdb
    if (flag == False):
        result["isdoc"] = False

    if "relate_opinion" in doc.keys():
        if "common_opinion" in doc["relate_opinion"].keys():
            del doc["relate_opinion"]["common_opinion"]
        result["relate_opinion"] = doc["relate_opinion"]

    result["rc"] = 200
    raise tornado.gen.Return(result)



