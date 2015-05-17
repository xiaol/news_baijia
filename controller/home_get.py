#coding=utf-8

from config import dbConn
from weibo import weibo_relate_docs_get, user_info_get
import json
import datetime,time
import operator
import pymongo
from utils import get_start_end_time
from pymongo.read_preferences import ReadPreference
conn = pymongo.MongoReplicaSetClient("h44:27017, h213:27017, h241:27017", replicaSet="myset",
                                                             read_preference=ReadPreference.SECONDARY)


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

    if 'date' in options.keys():
        date = options["date"]
    else:
        date = None

    if 'type' in options.keys():
        type = options["type"]
    else:
        type = None

    if 'timefeedback' in options.keys():
        timefeedback=options['timefeedback']
    else:
        timefeedback = None


    conn = DBStore._connect_news

    if not timing and not date and not type:

        docs = conn['news_ver2']['googleNewsItem'].find({"isOnline": 1}).sort([("createTime",-1)]).skip((page-1)*limit).limit(limit)

    # elif not timing:

        # request_time, next_update_time, next_update_type, history_date, upate_frequency = get_time_type_date_freq()

    elif date and type:

        day_night=get_day_night_time(date, type)
        docs=[]
        for day_night_elem in day_night:
            start_time = day_night_elem[0]
            end_time = day_night_elem[1]
            start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
            end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')

            doc = conn["news_ver2"]["googleNewsItem"].find({"isOnline": 1, "createTime": {"$gte": start_time,
                                                                                            "$lt": end_time}}).sort([("createTime", -1)])

            for doc_elem in doc:
                docs.append(doc_elem)

        docs= sorted(docs, key=operator.itemgetter("createTime"), reverse=True)

    else:
        # start_time, end_time = get_start_end_time()
        start_time, end_time, update_time, update_type, upate_frequency = get_start_end_time(halfday=True)
        start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
        end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')


        docs = conn["news_ver2"]["googleNewsItem"].find({"isOnline": 1, "createTime": {"$gte": start_time,
                                                                                       "$lt": end_time}}).sort([("createTime", -1)])

    special_list=[]
    nospecial_list=[]

    results_docs = reorganize_news(docs)

    for doc in results_docs:

        sublist = []
        reorganize_num = 0
        if "sublist" in doc.keys():
            sublist = doc["sublist"]
            reorganize_num = reorganize_num + len(sublist)
            set_googlenews_by_url_with_field_and_value(doc['sourceUrl'], "reorganize", sublist)
            del doc["sublist"]

        if "sourceUrl" not in doc.keys():
            print "error"
            continue
        url = doc['sourceUrl']
        title = doc["title"]
        sourceSiteName = doc["sourceSiteName"]

        baidu_news_num = count_relate_baidu_news(url)

        relate = []
        special_flag=True
        # 标记放到前边的新闻
        if sourceSiteName[:2] in special_source:
            doc["special"] = 1
        elif "special" in doc.keys():
            special_flag = False
        else:
            doc["special"] = 400
            special_flag = False

        if "relate" in doc.keys():
            if doc["relate"]:
                relate = doc["relate"]
                relate = del_dup_relatedoc(relate, sublist)
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

        if "imgWall" in doc.keys():
            del doc["imgWall"]

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
        doc["otherNum"] = otherNum + baidu_news_num + reorganize_num
        doc["urls_response"] = distinct_response_urls  #返回的urls，用于获取其他相关新闻时过滤掉 这几条已经有的新闻

        # if timefeedback:
        #     doc["timefeedback"]=timefeedback_dict

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

def reorganize_news(docs):
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

    print "hello"
    results_docs= sorted(results_docs,key=operator.itemgetter("createTime"))
    return results_docs


def constructEvent(eventList):
    result_doc = {}
    sublist = []
    imgUrl_ex=[]
    is_notin_flag=True
    for eventElement in eventList:
        if eventElement['eventId'] == eventElement["_id"]:
            result_doc = eventElement
            imgUrl_ex.append(eventElement['imgUrls'])
            is_notin_flag=False

        else:
            subElement={}
            subElement={'sourceSitename': eventElement['originsourceSiteName'], 'url': eventElement['_id'], 'title': eventElement['title'], 'img': eventElement['imgUrls']}
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


def get_time_type_date_freq(update_time,update_type,upate_frequency):
    now = datetime.datetime.now()
    tommorow = now + datetime.timedelta(days=1)
    request_time = int(convertTimestrtosecond(now)*1000)
    next_update_time = int(convertTimestrtosecond(update_time)*1000) - request_time
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
    request_time = int(convertTimestrtosecond(now)*1000)
    return request_time





def convertTimestrtosecond(date):
    return timestamp(date)

def timestamp(date):
    return time.mktime(date.timetuple())

def get_history_date(now):
    format='%Y-%m-%d'
    history_date=[]
    for i  in list(reversed(range(4))):
        yesterday = now + datetime.timedelta(days=-i)
        defaultTimestr=yesterday.strftime(format)
        history_date.append(defaultTimestr)

    return history_date






def get_day_night_time(date,type):

    date = datetime.datetime.strptime(date,'%Y-%m-%d')
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

    #黑夜 if hour in range(0,6):    #取昨天6点-昨天18点 更新时间为今天早上6点
    day_night=[]

    if type=='0': #0代表白天 1代表黑夜

        day_start_time = datetime.datetime(yesterday_year, yesterday_month, yesterday_day, 18, 0)
        day_end_time = datetime.datetime(today_year, today_month, today_day, 6, 0)
        day_night.append([day_start_time, day_end_time])

    elif type=='1':

        # night1_start_time = datetime.datetime(yesterday_year, yesterday_month, yesterday_day, 6, 0)
        # night1_end_time = datetime.datetime(yesterday_year, yesterday_month, yesterday_day, 18, 0)
        #白天 elif hour in range(6,18): #取昨天18点~今天6点 更新时间为今天18点
        #黑夜 elif hour in range(18,24): #取今天6-今天18点 更新时间为明天6点
        night2_start_time = datetime.datetime(today_year, today_month, today_day, 6, 0)
        night2_end_time = datetime.datetime(today_year, today_month, today_day, 18, 0)
        # day_night.append([night1_start_time,night1_end_time])
        day_night.append([night2_start_time,night2_end_time])


    elif type=='99':
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
    distinctdict = {"left":[], "middle":[], "bottom":[], "opinion":[], "deep_report":[]}
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

    return  distinctdict














