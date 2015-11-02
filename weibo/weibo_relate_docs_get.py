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
import lxml.etree as etree
# import task.requests_with_sleep as requests
# import urllib
# import HTMLParser
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




def baidusearch_relate_docs_1(topic, page):

    # print topic
    url='http://opendata.baidu.com/weibo/?ie=utf-8&oe=utf-8&format=json&wd=%s&rn=20&pn=0'%topic
    result = extractInfoByUrl(url)

    url_ex1='http://opendata.baidu.com/weibo/?ie=utf-8&oe=utf-8&format=json&wd=%s&rn=20&pn=20'%topic
    result_ex1 = extractInfoByUrl(url_ex1)

    url_ex2='http://opendata.baidu.com/weibo/?ie=utf-8&oe=utf-8&format=json&wd=%s&rn=20&pn=40'%topic
    result_ex2 = extractInfoByUrl(url_ex2)

    result.extend(result_ex1)
    result.extend(result_ex2)

    return result


def extractInfoByUrl(url):

    json_list_pat=re.compile(r'<a target=\'_blank\'.*?</div></div></a>')
    img_url_pat=re.compile(r'<img class=\'wa-weibo-img\' src=\'(.*?)\'')
    content_pat=re.compile(r'<p class=\'wa-weibo-content\'>(.*?)</p>')
    url_pat=re.compile(r'href=\'(.*?)\'')
    source_name_pat=re.compile(r'<span class=.*?>(.*?)</span>')
    updateTime_pat=re.compile(r'<span class=\'wa\-weibo\-t\' data-time=\'(.*?)\'>')

    # print url
    response = requests.get(url)
    content = response.content
    content=content.decode('utf-8')
    json_list=re.findall(json_list_pat,content)

    result=[]
    for json in json_list:
        # print "json,%s"%json
        elem_dict={}
        img_url=re.search(img_url_pat,json)
        if img_url:
            img_url=img_url.group(1)
        # print "img_url,%s"%img_url

        content=re.search(content_pat,json)
        if content:
            content=content.group(1)
        # print "content,%s"%content

        source_name=re.search(source_name_pat,json)
        if source_name:
            source_name=source_name.group(1)
        # print "source_name,%s"%source_name

        url=re.search(url_pat,json)
        if url:
            url=url.group(1)

            url=convertbaidutosina(url)


        # print "url,%s"%url

        updateTime=re.search(updateTime_pat,json)
        if updateTime:
            updateTime=updateTime.group(1)
            updateTime=float(updateTime)
            # updateTime=time.ctime(updateTime)
            updateTime=convertsecondtoTimestr(updateTime)
        else:
            updateTime=getDefaultTimeStr()

        # print "updateTime,%s"%updateTime


        elem_dict['img_url']=img_url
        elem_dict['content']=content
        elem_dict['source_name']=source_name
        elem_dict['url']=url
        elem_dict['updateTime']=updateTime
        result.append(elem_dict)

    return result

def trim_bracket(content):
    bracket_pat=re.compile(r'<.*?>')
    content = re.sub(bracket_pat, "", content)
    return content


def baidusearch_relate_weibo(topic):
    result = []
    url ='http://www.baidu.com/s?rtt=2&tn=baiduwb&rn=20&cl=2&wd={0}'.format(topic)
    r = requests.get(url)
    dom = etree.HTML(r.text)
    try:
        elements = dom.xpath('//li[@id]')
    except Exception as e:

        print "weibo page Parse error, the url is===>", url
        return result

    for element in elements:
        try:
            img_url = element.xpath('./div[@class="weibo_detail"]/div[@class="weibo_img_holder"]/div/img/@data-bgimg')[0]
            # print(etree.tostring(element, pretty_print=True))
            source_name = element.xpath('./div[@class="weibo_detail"]/p/a/text()')[0]
            content = ''.join(element.xpath('./div[@class="weibo_detail"]/p/descendant-or-self::text()')[1:])
            # print type(content)
            content = content.replace(u"：", "")
            print "content,%s"%content
            url = element.xpath('./div[@class="weibo_detail"]/div[@class="weibo_info"]/div[@class="m"]/a/@href')[0]
            updateTime = element.xpath('./div[@class="weibo_detail"]/div[@class="weibo_info"]/div[@class="m"]/a/text()')[0]
            img_urls = [img_url]
            profile_image_url = element.xpath('./div[@class="weibo_face"]/a/img/@src')[0]
            like_count = 0
            comments_count = 0
            reposts_count = 0
            elem_dict={}
            elem_dict['img_url'] = img_url
            elem_dict['content'] = content
            elem_dict['source_name'] = source_name
            elem_dict['url'] = url
            elem_dict['updateTime'] = updateTime
            elem_dict['img_urls'] = img_urls
            elem_dict['profile_image_url'] = profile_image_url
            elem_dict['like_count'] = like_count
            elem_dict['comments_count'] = comments_count
            elem_dict['reposts_count'] = reposts_count
            result.append(elem_dict)
        except:
            continue
    return result



def baidusearch_relate_docs(topic, page):
    result =[]
    # url = html_parser.unescape(url)
    # url=url
    # url=urllib.quote(url)
    # html_parser = HTMLParser.HTMLParser()
    # url = html_parser.unescape('http://m.weibo.cn/page/pageJson?containerid=&containerid=100103type%3D7%26q%3D%s%26topids%3D3846804812165441%2C3846900455810225%2C3847133662958521%26title%3D%E7%B2%BE%E9%80%89%E5%BE%AE%E5%8D%9A%26weibo_type%3Dhot%26t%3D&title=%E7%B2%BE%E9%80%89%E5%BE%AE%E5%8D%9A&cardid=weibo_page&uid=&luicode=10000011&lfid=100103type%3D1%26q%3D%s&v_p=11&ext=&fid=100103type%3D7%26q%3D%s%26topids%3D3846804812165441%2C3846900455810225%2C3847133662958521%26title%3D%E7%B2%BE%E9%80%89%E5%BE%AE%E5%8D%9A%26weibo_type%3Dhot%26t%3D&uicode=10000011&page=4'%topic)
    # url='http://m.weibo.cn/page/pageJson?containerid=&containerid=100103type%3D7%26q%3D{0}%26topids%3D3846804812165441%2C3846900455810225%2C3847133662958521%26title%3D%E7%B2%BE%E9%80%89%E5%BE%AE%E5%8D%9A%26weibo_type%3Dhot%26t%3D&title=%E7%B2%BE%E9%80%89%E5%BE%AE%E5%8D%9A&cardid=weibo_page&uid=&luicode=10000011&lfid=100103type%3D1%26q%3D{0}&v_p=11&ext=&fid=100103type%3D7%26q%3D{0}%26topids%3D3846804812165441%2C3846900455810225%2C3847133662958521%26title%3D%E7%B2%BE%E9%80%89%E5%BE%AE%E5%8D%9A%26weibo_type%3Dhot%26t%3D&uicode=10000011&page=1'.format(topic)
    # url='http://m.weibo.cn/page/pageJson?containerid=&containerid=100103type%3D7%26q%3D{0}%26topids%3D3846804812165441%2C3846900455810225%2C3847133662958521%26weibo_type%3Dhot%26t%3D&cardid=weibo_page&uid=&luicode=10000011&lfid=100103type%3D1%26q%3D{0}&v_p=11&ext=&fid=100103type%3D7%26q%3D{0}%26topids%3D3846804812165441%2C3846900455810225%2C3847133662958521%26weibo_type%3Dhot%26t%3D&uicode=10000011&page=1'.format(topic)
    url='http://m.weibo.cn/page/pageJson?containerid=&containerid=100103type%3D1%26q%3D{0}&type=all&queryVal={0}&luicode=20000174&title={0}&v_p=11&ext=&fid=100103type%3D1%26q%3D{0}&uicode=10000011&page=1'.format(topic)
    print url
    response = requests.get(url)
    contents = response.content
    # print "content,%s" %content
    try:
        dict_obj=json.loads(contents)
        cards=dict_obj["cards"]
        for card in cards:
            if card["card_type"] == 16:
                continue

            card_group = card["card_group"]
            for card_group_elem in card_group:
                if "scheme" not in card_group_elem.keys():
                    continue
                url = card_group_elem["scheme"]
                if "mblog" not in card_group_elem.keys():
                    continue
                mblog = card_group_elem["mblog"]
                like_count = mblog["like_count"]
                comments_count = mblog["comments_count"]
                reposts_count = mblog["reposts_count"]

                content = mblog["text"]
                content = trim_bracket(content)
                print "content,%s"%content
                updateTime = mblog["created_at"]
                if "pics" in mblog.keys():
                    pics = mblog["pics"]
                else:
                    pics = []
                img_urls=[]
                for pic in pics:
                    img_urls.append(pic["url"])
                if img_urls:
                    img_url = img_urls[0]
                else:
                    img_url = ""
                user = mblog["user"]
                source_name = user["screen_name"]
                profile_image_url = user["profile_image_url"]
                elem_dict={}
                elem_dict['img_url'] = img_url
                elem_dict['content'] = content
                elem_dict['source_name'] = source_name
                elem_dict['url'] = url
                elem_dict['updateTime'] = updateTime
                elem_dict['img_urls'] = img_urls
                elem_dict['profile_image_url'] = profile_image_url
                elem_dict['like_count'] = like_count
                elem_dict['comments_count'] = comments_count
                elem_dict['reposts_count'] = reposts_count
                result.append(elem_dict)
    except Exception as e:
        print e
        return result
    return result



if __name__ == '__main__':
    # print search_relate_docs("柴静","1")
    # baidusearch_relate_docs("刘翔","1")
    # baidusearch_relate_docs("刘强东","1")
    result = baidusearch_relate_weibo("白酒掺敌敌畏谣言成真:冒牌茅台酒疑似被检出")
    # baidusearch_relate_docs("宣传片+机制+危机+大学+事件","1")
    # baidusearch_relate_docs("煎蛋+烈日+高温+民众+印度","1")
    # source_name=re.compile('<span class=\'wa-weibo-author\'>(.*?)</span>')
    # convertsecondtoTimestr(1429845960.0

    # urllib2.unquote("%0a")

    # str='<a target='_blank' class='wa-weibo-table-row' href='http://m.baidu.com/tc?sec=2742&di=69db99f4e9d34ae0&&src=http%3A%2F%2Fm.weibo.cn%2F1528121221%2FCdcALtOVO%3Fwm%3D5091_0010%26from%3Dba_s0010&ssid=&uid=&from=&pu=sz%401320_220&bd_page_type=1&l=1'><div class='wa-weibo-table-cell wa-weibo-table-clickable-cell wa-weibo-item-1'><span class='wa-weibo-author'>真人网</span><span class='wa-weibo-time'><span class='wa-weibo-t' data-time='1428976312'>今天09:51</span>/新浪微博</span><div class='wa-weibo-clear'>&#160;</div><p class='wa-weibo-content'>传网友叫停 孙楠 上爸爸3  孙楠 带子女将上爸爸去哪儿第三季?网友集体叫停 | #传网友叫停 孙楠 上爸爸3#《爸爸去哪儿》人选悬而未决,最近账号 发微博称:“《爸爸去哪儿》第三季将设计全新游戏环节,告别做饭和旅游模式。”并配上一张 孙楠 ...   </p><img class='wa-weibo-img' src='http://ww1.sinaimg.cn/large/5b154785jw1er4uzhgrzyj20c806o0t1.jpg' data-src='http://m.baidu.com/tc?sec=2742&di=3d40248eab580678&&src=http%3A%2F%2Fww1.sinaimg.cn%2Flarge%2F5b154785jw1er4uzhgrzyj20c806o0t1.jpg&ssid=&uid=&from=&pu=sz%401320_220&bd_page_type=1&l=1'/><div class='wa-weibo-clear'>&#160;</div></div></a>'

    # source_name=re.search(source_name,str)
    # source_name=source_name.group(1)
    # print "source_name,%s"%source_name





