#coding=utf-8
# import urllib
import requests
import json
import time
import sys
import re
import time
import datetime
import urllib2
reload(sys)
sys.setdefaultencoding("utf-8")
def search_relate_docs(topic, page):

    # time.sleep(4)
    print topic

    # api_url = "http://14.17.120.252:9091/getInfoByText"
    api_url = "http://14.17.120.252:9091/getTextByApi"
    param = {"text": topic, "page": str(page)}
    r = requests.post(api_url, data=json.dumps(param), timeout=8)

    return r.text

def convertsecondtoTimestr(time):
    format='%Y-%m-%d %H:%M:%S'
    # starttime=datetime.datetime(1970,1,1)
    starttime=datetime.datetime(1970, 1, 1, 8, 0)
    timeDelta=datetime.timedelta(milliseconds=time*1000)
    defaultTime=starttime+timeDelta
    defaultTimestr=defaultTime.strftime(format)
    return defaultTimestr

def getDefaultTimeStr(cls):
    format='%Y-%m-%d %H:%M:%S'
    timeDelta=datetime.timedelta(milliseconds=3600*1000)
    defaultTime=(datetime.datetime.now()-timeDelta)
    defaultTimeStr=defaultTime.strftime(format)
    return defaultTimeStr

def convertbaidutosina(url):
    src_pat=re.compile(r'src=(.*?)&ssid')
    url_search=re.search(src_pat,url)
    if url_search:
        url=url_search.group(1)
        url=urllib2.unquote(url.encode("utf8"))
        return url
    return None


def baidusearch_relate_docs(topic,page):


    json_list_pat=re.compile(r'<a target=\'_blank\'.*?</div></div></a>')
    img_url_pat=re.compile(r'<img class=\'wa-weibo-img\' src=\'(.*?)\'')
    content_pat=re.compile(r'<p class=\'wa-weibo-content\'>(.*?)</p>')
    url_pat=re.compile(r'href=\'(.*?)\'')
    source_name_pat=re.compile(r'<span class=.*?>(.*?)</span>')
    updateTime_pat=re.compile(r'<span class=\'wa\-weibo\-t\' data-time=\'(.*?)\'>')

    print topic
    url='http://opendata.baidu.com/weibo/?ie=utf-8&oe=utf-8&format=json&wd=%s&rn=20&pn=0&first=1428396699&last=1428326859'%topic
    print url
    response = requests.get(url)
    content = response.content
    content=content.decode('utf-8')
    json_list=re.findall(json_list_pat,content)

    result=[]
    for json in json_list:
        print "json,%s"%json
        elem_dict={}
        img_url=re.search(img_url_pat,json)
        if img_url:
            img_url=img_url.group(1)
        print "img_url,%s"%img_url

        content=re.search(content_pat,json)
        if content:
            content=content.group(1)
        print "content,%s"%content

        source_name=re.search(source_name_pat,json)
        if source_name:
            source_name=source_name.group(1)
        print "source_name,%s"%source_name

        url=re.search(url_pat,json)
        if url:
            url=url.group(1)
            url=convertbaidutosina(url)


        print "url,%s"%url

        updateTime=re.search(updateTime_pat,json)
        if updateTime:
            updateTime=updateTime.group(1)
            updateTime=float(updateTime)
            # updateTime=time.ctime(updateTime)
            updateTime=convertsecondtoTimestr(updateTime)
        else:
            updateTime=getDefaultTimeStr()

        print "updateTime,%s"%updateTime


        elem_dict['img_url']=img_url
        elem_dict['content']=content
        elem_dict['source_name']=source_name
        elem_dict['url']=url
        elem_dict['updateTime']=updateTime
        result.append(elem_dict)

    return result





if __name__ == '__main__':
    # print search_relate_docs("柴静","1")
    baidusearch_relate_docs("孙楠","1")
    # source_name=re.compile('<span class=\'wa-weibo-author\'>(.*?)</span>')

    # str='<a target='_blank' class='wa-weibo-table-row' href='http://m.baidu.com/tc?sec=2742&di=69db99f4e9d34ae0&&src=http%3A%2F%2Fm.weibo.cn%2F1528121221%2FCdcALtOVO%3Fwm%3D5091_0010%26from%3Dba_s0010&ssid=&uid=&from=&pu=sz%401320_220&bd_page_type=1&l=1'><div class='wa-weibo-table-cell wa-weibo-table-clickable-cell wa-weibo-item-1'><span class='wa-weibo-author'>真人网</span><span class='wa-weibo-time'><span class='wa-weibo-t' data-time='1428976312'>今天09:51</span>/新浪微博</span><div class='wa-weibo-clear'>&#160;</div><p class='wa-weibo-content'>传网友叫停 孙楠 上爸爸3  孙楠 带子女将上爸爸去哪儿第三季?网友集体叫停 | #传网友叫停 孙楠 上爸爸3#《爸爸去哪儿》人选悬而未决,最近账号 发微博称:“《爸爸去哪儿》第三季将设计全新游戏环节,告别做饭和旅游模式。”并配上一张 孙楠 ...   </p><img class='wa-weibo-img' src='http://ww1.sinaimg.cn/large/5b154785jw1er4uzhgrzyj20c806o0t1.jpg' data-src='http://m.baidu.com/tc?sec=2742&di=3d40248eab580678&&src=http%3A%2F%2Fww1.sinaimg.cn%2Flarge%2F5b154785jw1er4uzhgrzyj20c806o0t1.jpg&ssid=&uid=&from=&pu=sz%401320_220&bd_page_type=1&l=1'/><div class='wa-weibo-clear'>&#160;</div></div></a>'

    # source_name=re.search(source_name,str)
    # source_name=source_name.group(1)
    # print "source_name,%s"%source_name





