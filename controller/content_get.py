#coding=utf-8
from PIL import Image

from config import dbConn
import requests

DBStore = dbConn.GetDateStore()

def fetchContent(url, filterurls, updateTime=None):

    conn = DBStore._connect_news

    doc = conn["news_ver2"]["googleNewsItem"].find_one({"sourceUrl": url})

    if not doc:
        return

    if updateTime is None:
        updateTime = ''

    docs_relate = conn["news"]["AreaItems"].find({"relateUrl": url}).sort([("updateTime",-1)]).limit(10)

    result = {}

    allrelate = Get_Relate_docs(doc, docs_relate, filterurls)

    if "imgUrls" in doc.keys():
        result['imgUrl'] = doc['imgUrls']

    if 'abstract' in doc.keys():
        result['abs'] = doc['abstract']

    if 'content' in doc.keys():
        result['content'] = doc['content']

    if 'ne' in doc.keys():
        result['ne'] = doc['ne']

    if 'zhihu' in doc.keys():
        zhihu = doc['zhihu']
        if isinstance(zhihu, dict):
            result['zhihu'] = [zhihu]
        elif isinstance(zhihu, list) and len(zhihu) > 0:
            result['zhihu'] = zhihu

    if 'weibo' in doc.keys():
        weibo = doc['weibo']
        if isinstance(weibo, dict):
            result['weibo'] = [weibo]
        elif isinstance(weibo, list) and len(weibo) > 0:
            result['weibo'] = weibo


    if 'douban' in doc.keys():
        douban = doc['douban']
        if isinstance(douban, list) and len(douban) > 0:
            result['douban'] = douban


    if 'baike' in doc.keys():
        baike = doc['baike']
        if isinstance(baike, dict):
            baike['abs'] = baike['abstract']
            del baike['abstract']
            result['baike'] = [baike]

        if isinstance(baike, list) and len(baike) > 0:
            result['baike'] = baike

    if 'originsourceSiteName' in doc.keys():
        result['originsourceSiteName'] = doc['originsourceSiteName']

    if 'imgUrls' in doc.keys():
        imgs = doc['imgUrls']
        if isinstance(imgs, list) and len(imgs) >0:
            result['imgUrl'] = imgs[-1]


    if "root_class" in doc.keys():
        result["root_class"] = doc["root_class"]

    if "sourceSitename" in doc.keys():
        category = doc["sourceSitename"]
        result["category"] = category[2:4]

    result["updateTime"] = doc["updateTime"]
    result["title"] = doc["title"]

    result["relate"] = allrelate
    result["rc"] = 200

    return result

def Get_Relate_docs(doc, docs_relate, filterurls):

    allrelate = []

    if "relate" in doc.keys() and doc["relate"]:
        relate = doc["relate"]

        left_relate = relate["left"]
        mid_relate = relate["middle"]
        bottom_relate = relate["bottom"]
        opinion = relate["opinion"]
        deep_relate = relate["deep_report"]

        allList = [left_relate, mid_relate, bottom_relate, opinion, deep_relate]

        for ones in allList:

            for e in ones:

                relate_url = e["url"]
                #title 为空 跳过
                if 'title' in e.keys():
                    if not e['title']:
                        continue

                if relate_url in filterurls:
                    continue

                # ct_img = Get_by_url(relate_url)
                # #
                # e["img"] = ct_img['img']
                if not "img" in e.keys():
                    e["img"] = ""

                allrelate.append(e)

    for one in docs_relate:
        ls = {}
        url_here = one["sourceUrl"]
        title_here = one["title"]
        sourceSiteName = one["sourceSiteName"]
        updatetime = one["updateTime"]

        imgUrl = ''

        if "imgUrl" in one.keys():
            imgUrls = one["imgUrl"]
            if isinstance(imgUrls, list) and len(imgUrls) > 0:
                imgUrl = imgUrls[-1]
            elif isinstance(imgUrls, dict):
                imgUrl = imgUrls['img']
            elif isinstance(imgUrls, str):
                imgUrl = imgUrls

        # if not imgUrl:
        #     continue

        ls["title"] = title_here
        ls["url"] = url_here
        ls["img"] = imgUrl
        ls["sourceSitename"] = sourceSiteName
        ls["updateTime"] = updatetime

        allrelate.append(ls)

    return allrelate


# def Get_by_url(url):
#
#     apiUrl_img = "http://121.41.75.213:8080/extractors_mvc_war/api/getImg?url="
#     apiUrl_text = "http://121.41.75.213:8080/extractors_mvc_war/api/getText?url="
#
#     apiUrl_img += url
#     apiUrl_text += url
#
#     r_img = requests_with_sleep.get(apiUrl_img)
#     r_text = requests_with_sleep.get(apiUrl_text)
#
#     img = (r_img.json())["imgs"]
#     print(type(img))
#     text = (r_text.json())["text"]
#
#     result = {}
#     img_result = []
#     if not img or not len(img)>0:
#         return None
#
#     # result['img'] = img[-1]
#     '''
#     for i in img:
#         if i.endswith('.gif'):
#             img.remove(i)
#         if 'weima' in i:
#             img.remove(i)
#         if ImgMeetCondition(i) == False:
#             img.remove(i)
#     result['img'] = img[0]
#     # result['img'] = img[3]
#
#
#     if result['img'].startswith('/'):
#         print('!!!!!!!!!!!')
#         print(result['img'])
#         aa = url.find('/', 7)
#         print(url[:aa])
#         result['img'] = url[:aa] + result['img']
#     elif result['img'].startswith('..'):
#         count = 0
#         while result['img'].startswith('..'):
#             count += 1
#             result['img'] = result['img'][3:]
#         print(result['img'])
#         get_list = url.split('/')
#         last_list = get_list[2:-1-count]
#         result['img'] = get_list[0] + '//' + '/'.join(last_list) + '/' + result['img']
#         print(result['img'])
#     elif result['img'].startswith('.'):
#         get_list = url.split('/')
#         print(get_list)
#         last_list = get_list[2:-1]
#         print(last_list)
#         result['img'] = get_list[0] + '//' + '/'.join(last_list) + result['img'][1:]
#         print(result['img'])
#     '''
#     for i in img:
#         # result['img'] = i
#         result_i = i
#         if result_i.startswith('/'):
#             print('!!!!!!!!!!!')
#             print(result_i)
#             aa = url.find('/', 7)
#             print(url[:aa])
#             result_i = url[:aa] + result_i
#             print(result_i)
#             # img.remove(i)
#             # img.append(result_i)
#             img_result.append(result_i)
#         elif result_i.startswith('..'):
#             count = 0
#             while result_i.startswith('..'):
#                 count += 1
#                 result_i = result_i[3:]
#             print(result_i)
#             get_list = url.split('/')
#             last_list = get_list[2:-1-count]
#             result_i = get_list[0] + '//' + '/'.join(last_list) + '/' + result_i
#             print(result_i)
#             # img.remove(i)
#             # img.append(result_i)
#             img_result.append(result_i)
#
#         elif result_i.startswith('.'):
#             get_list = url.split('/')
#             print(get_list)
#             last_list = get_list[2:-1]
#             print(last_list)
#             result_i = get_list[0] + '//' + '/'.join(last_list) + result_i[1:]
#             print(result_i)
#             # img.remove(i)
#             # img.append(resuolt_i)
#             img_result.append(result_i)
#         if result_i.endswith('.gif'):
#             # img.remove(result_i)
#             img_result.remove(result_i)
#         if 'weima' in result_i:
#             img_result.remove(result_i)
#         if ImgMeetCondition(result_i) == True:
#             img_result.remove(result_i)
#     result['img'] = img_result[0]
#     return result


import urllib, cStringIO
def ImgMeetCondition(url):
    img_url = url
    # img_url = 'http://www.01happy.com/wp-content/uploads/2012/09/bg.png'
    try:
        file = cStringIO.StringIO(urllib.urlopen(img_url).read())
        im = Image.open(file)
    except IOError:
        print "IOError, imgurl===>", img_url, "url ====>", url
        return True
    width, height = im.size
    print(width, height)
    if width <= 200 or height <= 200:
        return True
    print width, "+", height, " url=======>", img_url
    return False



if __name__ == '__main__':

    # print(Get_by_url("http://xinmin.news365.com.cn/tyxw/201503/t20150323_1779650.html"))
    # print(Get_by_url("http://www.jfdaily.com/guonei/new/201503/t20150323_1348362.html"))
    # print(Get_by_url("http://sports.sina.com.cn/l/s/2015-03-24/10287553303.shtml"))
    # print(ImgMeetCondition("http://xinmin.news365.com.cn/images/index_3.jpg"))
    print (ImgMeetCondition("http://img6.cutv.com/forum/201406/04/150731hffegglg1es9bufa.jpg"))