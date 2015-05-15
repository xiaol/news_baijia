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

    if "message" in options.keys() and options["message"]:
        options["msgTime"] = get_time()
        jpushId = str(options['jpushId'])
        message = options["message"]
        msgType = options["msgType"]

        _jpush = jpush.JPush(app_key, master_secret)
        push = _jpush.create_push()
        # push.audience = jpush.all_
        push.audience = {"registration_id": [jpushId]}
        push.message = jpush.message(msg_content={'msgTime': options["msgTime"], "msgType": msgType, "message": message})
        push.platform = jpush.all_
        push.send()


        Item = {'_id': jpushId}
        conn = DBStore._connect_news
        doc = conn['news_ver2']['imItem'].find_one(Item)

        if doc:
            print "jpush_id,%salread exists in databases" % options['jpushId']

            listInfos = doc['listInfos']
            listInfos = listInfos+[{'msgTime': options["msgTime"], 'msgType': msgType, 'message': options["message"]}]
            set_im_by_jpushId_with_field_and_value(options, "listInfos", listInfos)
            merge_listInfos = merge_message(listInfos)
            set_im_by_jpushId_with_field_and_value(options, "merge_listInfos", merge_listInfos)

            return {"response": 200}
        else:
            listInfos = [{'msgTime': options["msgTime"], 'msgType': msgType, 'message': options["message"]}]
            result = {}
            result["_id"] = options['jpushId']
            result["jpushId"] = options['jpushId']
            result["listInfos"] = listInfos
            result["merge_listInfos"] = listInfos
            item_dict = dict(result)
            conn['news_ver2']['imItem'].save(item_dict)
            return {"response": 200}
    else:
        print "message value is None"
        return {"response": 404}

def set_im_by_jpushId_with_field_and_value(options, field, value):
    conn["news_ver2"]["imItem"].update({"_id": options['jpushId']}, {"$set": {field: value}})

def merge_message(listInfos):
    merge_listInfos = []
    msgTimeSet = []
    for item in listInfos:
        msgTime_ex = item["msgTime"]/10000000
        msgType_ex = item["msgType"]
        if [msgType_ex, msgTime_ex] in msgTimeSet:
            position = msgTimeSet.index([msgType_ex, msgTime_ex])
            merge_listInfos[position]["message"] = merge_listInfos[position]["message"]+"."+item["message"]
        else:
            msgTimeSet.append([msgType_ex, msgTime_ex])
            merge_listInfos=merge_listInfos+[item]
    return merge_listInfos
