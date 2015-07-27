# -*- coding:utf8 -*-
__author__ = 'Gavin'
import urllib2
import json

from controller.config import dbConn
import datetime,time


def sentence_compress(text):
    url_get_base = "http://ltpapi.voicecloud.cn/analysis/?"
    api_key = 'o3o924B6KYeIKZCuJYvLXYSv0jfkyoZe2xRffxdJ'
    #fmt = format
    fmt = 'json'
    pattern = 'all'
    # print "%sapi_key=%s&text=%s&format=%s&pattern=%s" % (url_get_base,api_key,text,fmt,pattern)
    try:
        result_json = urllib2.urlopen("%sapi_key=%s&text=%s&format=%s&pattern=%s" % (url_get_base,api_key,text,fmt,pattern))
    except Exception, e:
        print e
    result = json.loads(result_json.read().strip())
    dependency = ['SBV', 'HED', 'VOB']
    noun = ['n', 'nd', 'nl', 'nz' , 'ns', 'nh', 'r' , 'p' , 'v']
    mm = []
    ss = []
    for x in result[0][0]:
        if x['relate'] in dependency or x['pos'] in noun:
            ss.append(x.get('cont', ''))
    ss = [s for s in ss if s]
    ss = ''.join(ss)
    print ss


def find_abstract_from_googlNews():
    DBStore = dbConn.GetDateStore()
    conn = DBStore._connect_news
    result_doc = conn["news_ver2"]["googleNewsItem"].find({"isOnline":1}).limit(100)

    docs = []
    for result_doc_elem in result_doc:

        doc = result_doc_elem["abstract"]
        doc = doc.encode('utf-8')
        docs.append(doc)

    return docs




if __name__ == '__main__':

    t1 = '王盛才拿着电筒循声扫去，发现一身穿花衬衣、颈挎救生圈的男子瘫在岸边'
    t2 = '【河北肃宁发生特大枪击案已致4死5伤 两干警围捕时牺牲】据通报，今日凌晨，付佐乡一村民刘双瑞手持双管猎枪对其住所周边村民进行枪击'
    t3 = '由长江航务管理局、荆州市政府、重庆市政府及船方代表等组成验收组，对“东方之星”号客轮现场清理工作完成情况进行验收，验收完毕后，对船体进行封存'
    t4 = '据了解，在去年高考期间，6月8日下午15时许，芜湖市南瑞实验中学高考考点英语考试听力测试时，高考英语听力磁带曾突发故障，磁带断裂无法进行英语听力部分考试，考场内近千名考生受到影响'
    t5 = '6月5日，美国海军两艘两栖攻击舰LHD6“好人理查德”号与LHD2“埃塞克斯”号，分别进入中国东海海域与香港水域'
    txt_li = [t1, t2, t3, t4 , t5]
    txts = find_abstract_from_googlNews()
    for txt in txts:
        print txt
        sentence_compress(txt)
        print '-----------------------'




