# coding=utf-8

from config import dbConn
import json
import datetime,time
import operator
import pymongo
from pymongo.read_preferences import ReadPreference
import urllib2
import cookielib
import traceback

class HttpUtil():
    def __init__(self,proxy = None):
        #proxy = {'http': 'http://210.14.143.53:7620'}
        if proxy != None:
            proxy_handler = urllib2.ProxyHandler(proxy)
            self.opener = urllib2.build_opener(proxy_handler,urllib2.HTTPCookieProcessor(cookielib.CookieJar()))
        else:
            self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))

        self.opener.addheaders=[('User-agent', 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.97 Safari/537.11'),\
                                ]


    def Get(self,url,times=1,timeout=30):
        for i in range(times):
            try:
                resp = self.opener.open(url,timeout=timeout)
                return resp.read()
            except:
                time.sleep(1)
                print traceback.format_exc()
                continue
        return None

    def Post(self,url,data,times=1, timeout=30):
        for i in range(times):
            try:
                resp = self.opener.open(url,data,timeout=timeout)
                return resp.read()
            except:
                time.sleep(1)
                print traceback.format_exc()
                continue
        return None

    def real_url(self,url,times=1,timeout=30):
        for i in range(times):
            try:
                return self.opener.open(url,timeout=timeout).geturl()
            except:
                time.sleep(1)
                print traceback.format_exc()
                continue
        return None

    def unzip(self,data):
        import gzip
        import StringIO
        data = StringIO.StringIO(data)
        gz = gzip.GzipFile(fileobj=data)
        data = gz.read()
        gz.close()
        return data

def get_html(url,encoding='utf-8'):
    httpUtil = HttpUtil()
    content = httpUtil.Get(url)
    if content:
        return content.decode(encoding,'ignore')
    else:
        return ""

def retrieveUserTag(sinaToken, sinaId):
    page, count = 1, 20
    userTagUrl = 'https://api.weibo.com/2/tags.json?' \
                 'access_token=%s&uid=%s&page=%s&count=%s'%(sinaToken, sinaId, page, count)
    friendsUrl = 'https://api.weibo.com/2/friendships/friends/ids.json?' \
                 'access_token=%s&uid=%s&cursor=%s'%(sinaToken, sinaId, 0)
    result = []
    try:
        html = get_html(userTagUrl)
        # print "zuoyuan", html
        tags = json.loads(html)
    except Exception, e:
        print e
        return result
    for tag in tags:
        for (k,v) in tag.items():
            if isinstance(v, basestring):
                result.append(v)

    try:
        html = get_html(friendsUrl)
        # print 'baiyuan', html
        friends = json.loads(html)
        # print 'baiyuan', html
    except Exception,e:
        print e
        return result

    count = 0
    friendsList = []
    friendsTag = []
    tagsAll = []
    for friend in friends['ids']:
        friendsList.append(friend)
        if count%19 == 0:
            tagBatchUrl = 'https://api.weibo.com/2/tags/tags_batch.json?' \
                      'access_token=%s&uids=%s'%(sinaToken, urllib2.quote(','.join(map(str,friendsList))))
            try:
                html = get_html(tagBatchUrl)
                # print html
                tagBatch = json.loads(html)
                tagsAll.extend(tagBatch)
            except Exception,e:
                print e
            friendsList = []
        count = count + 1

    for friendTag in tagsAll:
        for oneTag in friendTag['tags']:
            for (k, v) in oneTag.items():
                if k != u'weight':
                    friendsTag.append(v)

    for friendTag in tagsAll:
        sinaFriendTag = []
        hit = False
        for oneTag in friendTag['tags']:
            for (k, v) in oneTag.items():
                if k != u'weight':
                    sinaFriendTag.append(v)
                    friendsTag.remove(v)
                    if v in friendsTag:
                        result.append(v)

    for i in set(result):
        print i

    return set(result)

def retrieveUserInfo(sinaToken, sinaId):
    userInfoUrl = "https://api.weibo.com/2/users/show.json?" \
                  "access_token=%s&uid=%s" % (sinaToken, sinaId)
    html = get_html(userInfoUrl)
    print html

def TagsFetch(options):
    print options
    DBStore = dbConn.GetDateStore()
    # if "userId" in options.keys() and "platformType" in options.keys() and "token" in options.keys():
    if options['platformType'] == 'SinaWeibo' or options['platformType'] == '1':
        sinaToken = options['token']
        sinaId = options['userId']
        tags = retrieveUserTag(sinaToken, sinaId)
        options['tags'] = list(tags)
        update_tags(options)
        return options
    else:
        print "uerId/platformType value is None"
        return None


def update_tags(options):
    DBStore = dbConn.GetDateStore()
    conn = DBStore._connect_news
    if conn["news_ver2"]["Tags"].find_one({"userId": options['userId'], "platformType": options['platformType']}) == None:
        conn["news_ver2"]["Tags"].insert({"userId": options['userId'], "platformType": options['platformType'], "tags": options['tags']})
    else:
        conn["news_ver2"]["Tags"].update({"tags": options['tags']}, {"$set": {"userId": options['userId'], "platformType": options['platformType']}})


if __name__ == '__main__':
    DBStore = dbConn.GetDateStore()
    conn = DBStore._connect_news
    record = conn["news_ver2"]["loginItem"].find_one({"userName": "信心不逆的左元", "platformType": "1"})
    retrieveUserTag(record["token"], record["userId"])
