# coding=utf-8

from controller.config import dbConn
from weibo import weibo_relate_docs_get, user_info_get
import json
import datetime, time
import operator
import pymongo
from controller.utils import get_start_end_time
from pymongo.read_preferences import ReadPreference
# from channel_get import fetch_channel, newsFetch_channel,loadMoreFetchContent
from para_sim.TextRank4ZH.gist import Gist
import task.requests_with_sleep as requests
# from content_get import Get_Relate_docs
from AI_funcs.sen_compr.text_handler import SentenceCompressor
import re
import tornado.gen
from task.weibo_run_re import is_error_code, getDefaultTimeStr
import logging


conn = pymongo.MongoReplicaSetClient("h44:27017, h213:27017, h241:27017", replicaSet="myset",
                                     read_preference=ReadPreference.SECONDARY)


mapOfchannel =   {"谷歌今日焦点": "热点",
                   "热门专题": "精选",
                   "今日焦点": "社会",
                   "社会观察家": "社会",
                   "外媒观光团": "外媒",
                   "贵圈乱不乱": "娱乐",
                   "科技嗨起来": "科技",
                   "直男常备": "体育",
                   "股往今来": "财经",
                   "高逼格Get": "时尚",
                   "围观大奇葩": "搞笑",
                   "追剧看片": "影视",
                   "音痴恐惧症":"音乐",
                   "重口味":"重口味",
                   "X星人沦陷区":"萌宠",
                   "萌师强化班":"二次元"

                   }

DBStore = dbConn.GetDateStore()




def extractContent(content):
    contentlist = []
    i = 0
    for doc in content:
        for key in doc.keys():
            if doc[key].keys()[0] == 'img_info' and contentlist[-1].keys()[1] == 'img':
                contentlist[-1]['img_info'] = doc[key].values()[0]
                contentlist[-1]['index'] = i - 1
                i = i + 1
            else:
                contentDoc = doc[key]
                contentDoc['index'] = i
                contentlist.append(contentDoc)
                i = i + 1
    return contentlist

def extractContentByGoogle(content):
    text_list = content.split('\n')
    result_list = []
    i = 0
    for text_elem in text_list:
        if not text_elem.strip():
            continue
        else:
            result_list.append({"txt": text_elem, "index": i})
            i = i + 1

    return result_list


def extractImgUrls(content):
    for _doc in content:
        for k, item_doc in _doc.iteritems():
            if "img" in item_doc.keys():
                return  item_doc['img']

    return ""

def extractCommentNum(url):
    pointsCursorNum = conn["news_ver2"]["pointItem"].find({"sourceUrl": url}).count()
    docComment = conn["news_ver2"]["commentItems"].find_one({"relateUrl": url})
    if docComment:
        docCommentNum = len(docComment["comments"])
    return pointsCursorNum + docCommentNum



def convertGoogleNewsItems(docs = []):    #输入GoogleNewItems数据(list里面包含字典)  输出 统一数据格式(list里面包含字典)
    result = []
    for doc in docs:
        if "_id" in doc.keys():
            del doc["_id"]
        if "originsourceSiteName" in doc.keys():
            del doc["originsourceSiteName"]
        if "description" in doc.keys():
            del doc["description"]
        if "page" in doc.keys():
            del doc["page"]
        if "category" not in doc.keys():
            if "sourceSiteName" in doc.keys():
                sourceSitename = doc["sourceSiteName"]
                if sourceSitename == "地球图辑队":
                    doc["category"] = "社会"
                else:
                    doc["category"] = sourceSitename[2:4]
            else:
                continue
        doc["channel"] = mapOfchannel["谷歌今日焦点"]

        doc["channelId"] = "99"
        del doc["root_class"]
        if "auto_tags" in doc.keys():
            del doc["auto_tags"]
        if "ne" in doc.keys():
            del doc["ne"]
        if "content" not in doc.keys():
            if "text" in doc.keys():
                doc["content"] = doc["text"]
            else:
                doc["content"] = ""

        if "content" in doc.keys():
            doc["content"] = extractContentByGoogle(doc["content"])
        if "text" in doc.keys():
            del doc["text"]
        if "isOnline" in doc.keys():
            del doc["isOnline"]
        if "tag" in doc.keys():
            del doc["tag"]
        if "gist" in doc.keys():
            del doc["gist"]
        doc["commentNum"] = extractCommentNum(doc["sourceUrl"])
        result.append(doc)

    return result
#输出示例： 多出relate|category
        # 如下字段可能有 (|douban|weibo|zhihu|abstract|"imgWall"|”compress“|baike)
# {
#   “updateTime”（新闻发布时间）: "2015-10-14 15:04:52",
#   “sourceUrl”（新闻url）: "http://www.techweb.com.cn/tele/2015-10-14/2212661.shtml",
#   “title”（新闻标题）: "苹果A9处理器被判侵权面临8.6亿美元罚款",
#   “relate”（抓取到的相关观点）: {
#     “middle”（中间部分）: [
#       {
#         "url": "http://games.sina.com.cn/y/n/2015-10-14/fxirmqc5105913.shtml",
#         "sourceSitename": "新浪网",
#         "title": "苹果被判侵犯威斯康星大学专利"
#       }
#     ],
#     “opinion”（观点部分）: [
#
#     ],
#     “deep_report”（深入报道部分）: [
#
#     ],
#     “left”（左边部分）: [
#       {
#         “sourceSitename”（新闻来源网站）: "TechWeb",
#         “gist”（算法得出新闻摘要）: "据悉，在去年一月份威斯康星大学校友研究基金会就曾经针对苹果A7处理器未经允许使用其计算机微架构专利起诉过苹果公司，涉及到的产品是当时的iPhone5s与iPadAir，而之后A8与A8X芯片也出现同样的问题",
#         “img”（新闻图片）: "http://s1.techweb.com.cn/static/img/aliyun20151012.jpg?2015092301",
#         “title”（新闻标题）: null,
#         “url”（新闻url）: "http://www.techweb.com.cn/tele/2015-10-14/2212661.shtml",
#         “text”(算法抽取新闻正文内容): "正当人们对于苹果iPhone 6s/6s Plus存在台积电。。。。",
#         “compress”（算法提取新闻主干）: "而之后A8与A8X芯片也出现同样的问题。。。。"
#       }
#     ],
#     “bottom”（底部部分）: [
#
#     ]
#   },
#   “category”（新闻所属分类。。科技、财经。。。）: "热点",
#   “sourceSiteName”(新闻从哪个来源爬取): "谷歌科技新闻",
#   “createTime”（新闻爬取时间）: "2015-10-14 14:00:12",
#   “channel”（新闻所属大频道）: "最热门",
#   “channelId” : "99"
#   “douban”（豆瓣信息）: [
#     [
#       “加拿大”（关键词）,
#       "http://www.douban.com/link2/?url=http%3A%2F%2Fwww.douban.com%2Fgroup%2F355054%2F&query=%E5%8A%A0%E6%8B%BF%E5%A4%A7&cat_id=1019&type=search&pos=0”（url连接）
#     ]
#
#   “weibo”（微博信息）: [
#     {
#       "reposts_count": 0,
#       "sourceSitename": "weibo",
#       "img": "",
#       "title": "【广州一女子为追回爱犬被偷狗贼轧断腿】 网页链接 (想看更多合你口味的内容，马上下载 今日头条) 网页链接",
#       "url": "http://m.weibo.cn/1641537045/CF3bje7Z2?",
#       "profileImageUrl": "http://tp1.sinaimg.cn/5353551228/180/5712031240/1",
#       "like_count": 0,
#       "comments_count": 0,
#       "user": "杨彦朋15267",
#       "imgs": [
#
#       ]
#     },
#
#   “zhihu”（知乎信息）: [
#     {
#       "url": "http://www.zhihu.com/question/36031126",
#       "user": "王鹏飞",
#       "title": "苹果A9处理器?"
#     },
#   ],
#
#   “imgUrls”（新闻url）: "http://upload.techweb.com.cn/2015/1014/1444805229847.jpg",
#   “abstract”(算法算出新闻摘要): "据悉，在去年一月份威斯康星大学校友研究基金会就曾经针对苹果A7处理器未经允许使用其计算机微架构专利起诉过苹果公司，涉及到的产品是当时的iPhone5s与iPadAir，而之后A8与A8X芯片也出现同样的问题",
#   “imgWall”(图片集):[
#   {
#       “note”(图片信息描述): "10月13日，广东广州，刘女士家遭....",
#       “img”(图片url): "http://img4.cache.netease.com/photo/0001/2015-10-14/B5SVE24200AP0001.jpg"
#     },
#
#
#   ”compress“:(算法算出文章主干)
#   “baike”(百科部分): {
#     "url": "http://baike.baidu.com/view/3647.htm",
#     “abstract”（算法算出百科摘要）: "加拿大(Canada),为北美洲最北的国家,西抵太平洋,东迄大西洋,北至北冰洋,东北部和丹麦领地格陵兰岛相望,东部和法属圣皮埃尔和密克隆群岛相望,南方与美国本土接壤,...          ",
#     "title": "加拿大_百度百科
#     “commentNum”:评论数量
#
# }

def convertNewsItems(docs = []):  #输入NewsItems数据(list里面包含字典)  输出 统一数据格式(list里面包含字典)
    result = []
    for doc in docs:
        del doc["_id"]
        if "update_time" in doc.keys():
            doc["updateTime"] = doc["update_time"]
            del doc["update_time"]
        if "author" in doc.keys():
            del doc["author"]
        if "tags" in doc.keys():
            del doc["tags"]
        if "url" in doc.keys():
            del doc["url"]
        if "imgnum" in doc.keys():
            del doc["imgnum"]
        if "source_url" in doc.keys():
            doc["sourceUrl"] = doc["source_url"]
            del doc["source_url"]
        if 'content' in doc.keys():
            doc["imgUrls"] = extractImgUrls(doc["content"])
            doc["content"] = extractContent(doc["content"])
        if "source" in doc.keys():
            del doc["source"]
        if "start_url" in doc.keys():
            del doc["start_url"]
        if "start_title" in doc.keys():
            doc["sourceSiteName"] = doc["start_title"]
            del doc["start_title"]
        if "channel" in doc.keys():
            doc["channel"] = mapOfchannel(doc["channel"])
        if "channel_id" in doc.keys():
            doc["channelId"] = doc["channel_id"]
            del doc["channel_id"]
        doc["commentNum"] = extractCommentNum(doc["sourceUrl"])
        result.append(doc)
        if "create_time" in doc.keys():
            doc["createTime"] = doc["create_time"]
            del doc["create_time"]


    return result

#输出示例：
#  {
#   "updateTime": "06-15 23:35",
#   "title": "尼加拉瓜农民集会 抗议中企修建运河",
#   "sourceUrl": "http://m.sohu.com/n/415068683/",
#   "imgUrls":
#   "content": [
#     {
#
#         "img": "http://s9.rr.itc.cn/g/wapChange/20156_15_23/a7az0j424387611781.jpg"
#         "index":0
#         "img_info": "活动组织方宣称，有15000人参与了此次示威"
#     },
#
#     {
#         "txt": "活动组织方宣称，有15000人参与了此次示威 备受关注的尼加拉瓜运河发展项目自去年12月正式启动以来，虽然尚未动工，却已经引来了许多当地反对的声浪。大公网据墨西哥国家通讯社报道称，数千名尼加拉瓜农民13日参加抗议活动，反对在尼加拉瓜境内修建跨洋运河。"
#
#     }
#
#   ]
#   "sourceSiteName": "搜狐要闻-国际",
#   "channel": "头条焦点",
#   "channelId": "0"
#   "createTime":(可能没有该字段)
#   “commentNum”:评论数量
# }






            # for doc_elem in doc:
            #     docs.append(doc_elem)
            # undocs = conn["news_ver2"]["googleNewsItem"].find(
            #     {"$or": [{"isOnline": 0}, {"isOnline": {"$exists": 0}}], "createTime": {"$gte": start_time_yes},
            #      "eventId": {"$exists": 1}}).sort([("createTime", -1)])
            # undocs_list = extratInfoInUndocs(undocs)

if __name__ == '__main__':
    # channelId = 6
    # page = 1
    # limit = 50
    # docs_newsItem = conn['news_ver2']['NewsItems'].find({"channel_id": str(channelId), "imgnum": {'$gt': 0}, 'create_time': {'$exists': True}}).sort("create_time",
    #                                                                                                      pymongo.DESCENDING).skip((page - 1) * limit).limit(limit)
    #
    #
    # result = convertNewsItems(docs_newsItem)

    doc = conn["news_ver2"]["googleNewsItem"].find({"sourceUrl": "http://news.163.com/photoview/00AP0001/101834.html"}).sort([("createTime", -1)]).limit(1)

    result = convertGoogleNewsItems(doc)
    print "eof"
