#coding=utf-8

from config import dbConn
from weibo import weibo_relate_docs_get, user_info_get
import json
import datetime
import operator

mapOfSourceName = {"weibo":"微博",
                   "wangyi":"wangyi",
                   "xinlang":"xinlang",
                   "zhihu":"zhihu"}

DBStore = dbConn.GetDateStore()

special_source = ["观察", "网易"]

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

    conn = DBStore._connect_news

    if not timing:

        docs = conn['news_ver2']['googleNewsItem'].find({"isOnline": 1}).sort([("updateTime",-1)]).skip((page-1)*limit).limit(limit)

    else:
        # start_time, end_time = get_start_end_time()
        start_time, end_time = get_start_end_time(halfday=True)
        start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
        end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')



        docs = conn["news_ver2"]["googleNewsItem"].find({"isOnline": 1, "createTime": {"$gte": start_time,
                                                                                       "$lt": end_time}}).sort([("createTime", -1)])


    special_list=[]
    nospecial_list=[]

    docs_return = []

    for doc in docs:

        sublist = []
        url = doc['sourceUrl']
        title = doc["title"]
        sourceSiteName = doc["sourceSiteName"]

        baidu_news_num = count_relate_baidu_news(url)

        relate = []
        special_flag=True
        # 标记放到前边的新闻
        if sourceSiteName[:2] in special_source:
            doc["special"] = 1

        else:
            doc["special"] = 400
            special_flag=False

        if "relate" in doc.keys():
            if doc["relate"]:
                relate = doc["relate"]
            del doc["relate"]

        if "sourceSiteName" in doc.keys():
            sourceSitename  = doc["sourceSiteName"]
            doc["category"] = sourceSitename[2:4]
        else:
            continue
        #不取没有相关的
        # if not relate:
        #     continue

        if "weibo" in doc.keys():
            weibo = doc["weibo"]
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

            if isinstance(zhihu, dict):
                zhihu["sourceSitename"] = "zhihu"
                sublist.append(zhihu)
                del doc["zhihu"]

            elif isinstance(doc["zhihu"], list) and len(doc["zhihu"]) > 0 :
                zhihu = doc["zhihu"][0]
                zhihu["sourceSitename"] = "zhihu"
                sublist.append(zhihu)
                del doc["zhihu"]

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
            del doc["baike"]

        if "baiduSearch" in doc.keys():
            del doc["baiduSearch"]

        #相关新闻每一个来源 选一条
        if relate:
            distinctList, distinctNum, distinct_response_urls, otherNum = GetRelateNews(relate)

        else:
            distinctList = []
            distinctNum = 0
            distinct_response_urls = []
            otherNum = 0

        sublist.extend(distinctList)

        doc["sublist"] = sublist
        doc["otherNum"] = otherNum + baidu_news_num
        doc["urls_response"] = distinct_response_urls  #返回的urls，用于获取其他相关新闻时过滤掉 这几条已经有的新闻

        # docs_return.append(doc)
        if special_flag:
            special_list.append(doc)
        else:
            nospecial_list.append(doc)

    special_list= sorted(special_list,key=operator.itemgetter("createTime"))
    docs_return=special_list+nospecial_list
    # if timing:
    # docs_return = sorted(docs_return, key=operator.itemgetter("special"))

    # print docs_return
    return docs_return

def count_relate_baidu_news(url):

    conn = DBStore._connect_news
    num = conn["news"]["AreaItems"].find({"relateUrl":url}).count()

    return num

# 相关新闻的获取
def GetRelateNews(relate):

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
            if e["sourceSitename"] not in sourceNameSet:
                e["user"]=""
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

def get_start_end_time(oneday=False,halfday=False):

    now = datetime.datetime.now()
    yesterday = now + datetime.timedelta(days=-1)
    yesterday_year = yesterday.year
    yesterday_month = yesterday.month
    yesterday_day = yesterday.day

    today_year = now.year
    today_month = now.month
    today_day = now.day

    hour = now.hour
    start_time = ''
    end_time = ''

    if oneday:
        start_time = datetime.datetime(yesterday_year, yesterday_month, yesterday_day, 0, 0)
        end_time = now

        return start_time, end_time

    if halfday:


        if hour in range(0,6):    #取昨晚6点-昨天18点
            start_time = datetime.datetime(yesterday_year, yesterday_month, yesterday_day, 6, 0)
            end_time = datetime.datetime(yesterday_year, yesterday_month, yesterday_day, 18, 0)

        elif hour in range(6,18): #取昨天18点~今天6点
            start_time = datetime.datetime(yesterday_year, yesterday_month, yesterday_day, 18, 0)
            end_time = datetime.datetime(today_year, today_month, today_day, 6, 0)

        elif hour in range(18,24): #取今天6-今天18点
            start_time = datetime.datetime(today_year, today_month, today_day, 6, 0)
            end_time = datetime.datetime(today_year, today_month, today_day, 18, 0)
        return start_time, end_time

    if hour in range(0, 8):  # 取昨天14点~~~20点
        start_time = datetime.datetime(yesterday_year, yesterday_month, yesterday_day, 14, 0)
        end_time = datetime.datetime(yesterday_year, yesterday_month, yesterday_day, 20, 0)

    elif hour in range(8, 14): #取昨天20天~~~今天8点
        start_time = datetime.datetime(yesterday_year, yesterday_month, yesterday_day, 20, 0)
        end_time = datetime.datetime(today_year, today_month, today_day, 8, 0)

    elif hour in range(14, 20): #取今天8点~~~14点
        start_time = datetime.datetime(today_year, today_month, today_day, 8, 0)
        end_time = datetime.datetime(today_year, today_month, today_day, 14, 0)

    elif hour in range(20, 24): #取今天14点~~~20点
        start_time = datetime.datetime(today_year, today_month, today_day, 14, 0)
        end_time = datetime.datetime(today_year, today_month, today_day, 20, 0)

    return start_time, end_time

def GetOneWeibo(title):
    weibos = weibo_relate_docs_get.search_relate_docs(title,1)
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







