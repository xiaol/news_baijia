# -*- coding: utf-8 -*-
import traceback
import os
import time
import urlparse
import sys
import datetime
try:
    import simplejson as json
except:
    import json
import urllib2
from urllib import quote_plus
import codecs
import threading
import random
from StringIO import StringIO
import gzip
import re
import cookielib
import logging

import HTMLParser
hparser = HTMLParser.HTMLParser()

def decode_safe(s):
    if type(s) == unicode:
        return s
    try:
        return s.decode('gbk')
    except:
        pass
    try:
        return s.decode('gb18030')
    except:
        pass
    try:
        return s.decode('utf-8')
    except:
        pass
    try:
        return s.decode('big5')
    except:
        pass

def get_page(url, cookiejar = None, post_data = None, max_retry = 10, need_proxy=False, timeout = 10, referer = None, add_headers = {}):
    
    text = None
    for i in range(0, max_retry):
        try:
            handlers = []
            if need_proxy:
                proxy_handler = urllib2.ProxyHandler({'http': '%s:%s' % (squid['ip'], int(squid['port']))})
                handlers.append(proxy_handler)
            if cookiejar != None:
                cookie_processor = urllib2.HTTPCookieProcessor(cookiejar)
                handlers.append(cookie_processor)

            opener = urllib2.build_opener(*handlers)
            request = urllib2.Request(url)
            request.add_header('Accept-Encoding', 'gzip')
            request.add_header('Accept-Language', 'zh-CN,en-US,en')
            request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.43 Safari/537.31')
            request.add_header('Accept', 'application/json,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8,q=0.01')
            if referer != None:
                request.add_header('Referer', referer)
            if add_headers != {}:
                for k in add_headers:
                    request.add_header(k, add_headers[k])
            try:
                if post_data == None:
                    rsp = opener.open(request, timeout=timeout)
                else:
                    rsp = opener.open(request, timeout=timeout, data=post_data)
                current_url = rsp.geturl()
                rsp_text = rsp.read()
            except Exception, e:
                raise

            try:
                t0 = time.time()
                if rsp.info().get('Content-Encoding') == 'gzip':
                    buf = StringIO(rsp_text)
                    f = gzip.GzipFile(fileobj=buf)
                    rsp_text = f.read()

                if rsp.info().get('Content-Type') == 'application/x-shockwave-flash': 
                    text = rsp_text
                else:
                    text = decode_safe(rsp_text)
            except:
                raise
            
            break
        except Exception, e:
            text = None
            continue

    return text



#2015-04-06 14:46:04

a = re.compile(u'\d{4}[-/]\d{1,2}[-/]\d{1,2}\s\d{1,2}:\d{1,2}:\d{1,2}')

#2015-01-01

b = re.compile(u'\d{4}-\d{1,2}-\d{1,2}')

#2015年04月06日20:36

c = re.compile(ur'\d{4}[\u4e00-\u9fa5]\d{1,2}[\u4e00-\u9fa5]\d{1,2}[\u4e00-\u9fa5]\d{1,2}:\d{1,2}')

#2015年02月06日 06:31

d = re.compile(ur'\d{4}[\u4e00-\u9fa5]\d{1,2}[\u4e00-\u9fa5]\d{1,2}[\u4e00-\u9fa5]\s\d{1,2}:\d{1,2}')

#2015-08-20 07:58

e = re.compile(u'\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}:\d{1,2}')

#2015年4月6日

f = re.compile(ur'\d{4}[\u4e00-\u9fa5]\d{1,2}[\u4e00-\u9fa5]\d{1,2}[\u4e00-\u9fa5]')

#2015/9/12 22:14:01

# g = re.compile(u'\d{4}/\d{1,2}/\d{1,2}\s\d{1,2}:\d{1,2}:\d{1,2}')

list = [a, c, d, e, b, f]

def time_match(url):
    text = get_page(url)
    for regex in list:
        # try:
        if re.search(regex, text):
            update_time = re.search(regex, text).group(0)
            update_time = formatTime(update_time)
            return update_time
        else:
            continue
        # except:
        #     return getDefaultTimeStr()
    return u'9999-10-15 07:21:00'
    # return getDefaultTimeStr()


def formatTime(timeStr):
    digital_pat=re.compile(r'\d+')
    digitals=re.findall(digital_pat,timeStr)
    resultArr=[]
    i=0
    for digit in digitals:
        if len(digit)<2:
            digit='0'+digit
        if i==3 and timeStr.endswith('pm'):
            hour=int(digit)+12
            digit=str(hour)
        resultArr.append(digit)
        if i<2:
            resultArr.append('-')
        elif i==2:
            resultArr.append(' ')
        elif i<5:
            resultArr.append(':')
        i=i+1

    hour = getDefaultTimeStr().split(" ")[-1].split(':')[-3]
    minute = getDefaultTimeStr().split(':')[-2]
    second = getDefaultTimeStr().split(':')[-1]
    if i == 3:
        resultArr.append(hour)
        resultArr.append(':')
        resultArr.append(minute)
        resultArr.append(':')
        resultArr.append(second)
    elif i ==4:
        resultArr.append(minute)
        resultArr.append(':')
        resultArr.append(second)
    elif i ==5:
        resultArr.append(second)
    elif i ==6:
        pass
    else:
        return getDefaultTimeStr()
    return ''.join(resultArr)

def getDefaultTimeStr():
    format='%Y-%m-%d %H:%M:%S'
    timeDelta=datetime.timedelta(milliseconds=3600*1000)
    defaultTime=(datetime.datetime.now()-timeDelta)
    defaultTimeStr=defaultTime.strftime(format)
    return defaultTimeStr


if __name__ == "__main__":
    # print time_match('http://news.163.com/15/0823/20/B1NRLMK000014SEH.html')
    # print time_match('http://www.chinanews.com/ty/2015/08-26/7490736.shtml')

    # print time_match('http://news.ifeng.com/a/20151015/44973865_0.shtml')
    # print time_match('http://bbs.tiexue.net/post2_9544426_1.html')
    # print time_match(u"2015-04-06 14:46:04 123456")
    # print time_match(u"2015-01-01eee")
    # print time_match(u"2015年04月06日20:36wwww")
    # print time_match(u"2015年02月06日 06:31")
    # print time_match(u"2015-08-20 07:58www")
    # print time_match(u"2015年4月6日")
