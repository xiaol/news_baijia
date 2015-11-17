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

from lxml import etree

from Logger import openlog, DBG, INFO, ERR
import Logger

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
    try:
        return s.decode('gb2312')
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
                ERR('error_err', str(e), url)
                raise

            try:
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
            ERR(traceback.format_exc(), e)
            text = None
            continue

    return text

if __name__ == '__main__':
    # openlog('page.log')
    # print get_page('http://www.ftchinese.com/')
    print get_page("http://www.xilu.com/news/jixiantiaozhanyanbo_2.html")
