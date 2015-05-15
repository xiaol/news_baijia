__author__ = 'yangjiwen'
import jpush as jpush
from conf import app_key, master_secret
from controller.home_get import get_time
import pymongo
from pymongo.read_preferences import ReadPreference
from controller.config import dbConn


conn = pymongo.MongoReplicaSetClient("h44:27017, h213:27017, h241:27017", replicaSet="myset",
                                                             read_preference=ReadPreference.SECONDARY)

DBStore = dbConn.GetDateStore()

def imContentFetch(options):

    if "content" in options.keys() and options["content"]:
        options["msgTime"] = get_time()
        jpushId = str(options['receiverId'])
        content = options["content"]
        msgType = options["msgType"]

        _jpush = jpush.JPush(app_key, master_secret)
        push = _jpush.create_push()
        # push.audience = jpush.all_
        push.audience = {"registration_id": [jpushId]}
        push.message = jpush.message(msg_content={'msgTime': options["msgTime"], "msgType": msgType, "content": content, "receiverId": options["receiverId"], "senderId": options["senderId"]})
        push.platform = jpush.all_
        push.send()


        Item = {'senderId': options["senderId"], "receiverId": options["receiverId"]}
        conn = DBStore._connect_news
        doc = conn['news_ver2']['imItem'].find_one(Item)

        if doc:
            print "jpush_id,%salread exists in databases" % options['receiverId']
            listInfos = doc['listInfos']
            listInfos = listInfos+[{'msgTime': options["msgTime"], 'msgType': msgType, 'content': options["content"]}]
            set_im_by_jpushId_with_field_and_value(options, "listInfos", listInfos)
            merge_listInfos = merge_message(listInfos)
            set_im_by_jpushId_with_field_and_value(options, "merge_listInfos", merge_listInfos)

            return {"response": 200}
        else:
            listInfos = [{'msgTime': options["msgTime"], 'msgType': msgType, 'content': options["content"]}]
            result = {}
            result["senderId"] = options['senderId']
            result["receiverId"] = options['receiverId']
            result["listInfos"] = listInfos
            result["merge_listInfos"] = listInfos
            item_dict = dict(result)
            conn['news_ver2']['imItem'].save(item_dict)
            return {"response": 200}
    else:
        print "message value is None"
        return {"response": 404}

def set_im_by_jpushId_with_field_and_value(options, field, value):
    conn["news_ver2"]["imItem"].update({'senderId': options["senderId"], "receiverId": options["receiverId"]}, {"$set": {field: value}})

def merge_message(listInfos):
    merge_listInfos = []
    msgTimeSet = []
    for item in listInfos:
        msgTime_ex = item["msgTime"]/10000000
        msgType_ex = item["msgType"]
        if [msgType_ex, msgTime_ex] in msgTimeSet:
            position = msgTimeSet.index([msgType_ex, msgTime_ex])
            merge_listInfos[position]["content"] = merge_listInfos[position]["content"]+"."+item["content"]
        else:
            msgTimeSet.append([msgType_ex, msgTime_ex])
            merge_listInfos=merge_listInfos+[item]
    return merge_listInfos
