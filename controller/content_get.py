#coding=utf-8


from config import dbConn
import requests

DBStore = dbConn.GetDateStore()

def fetchContent(url, filterurls, updateTime=None):

    conn = DBStore._connect_news

    doc = conn["news_ver2"]["googleNewsItem"].find_one({"sourceUrl": url})

    if updateTime is None:
        updateTime = ''

    docs_relate = conn["news"]["AreaItems"].find({"relateUrl": url, "updateTime": {"$lt": updateTime}}).sort([("updateTime",-1)]).limit(10)

    result = {}

    if "relate" in doc.keys():

        relate = doc["relate"]
        if 'abstract' in doc.keys():
            result['abs'] = doc['abstract']

        if 'content' in doc.keys():
            result['content'] = doc['content']

        if 'ne' in doc.keys():
            result['ne'] = doc['ne']

        if 'zhihu' in doc.keys():
            zhihu = doc['zhihu']
            if isinstance(zhihu, dict):
                result['zhihu'] = doc['zhihu']
            elif isinstance(zhihu, list) and len(zhihu) > 0:
                result['zhihu'] = zhihu[0]

        if 'weibo' in doc.keys():
            weibo = doc['weibo']
            if isinstance(weibo, dict):
                result['weibo'] = weibo
            elif isinstance(weibo, list) and len(weibo) > 0:
                result['weibo'] = weibo[0]


        if 'douban' in doc.keys():
            douban = doc['douban']
            if isinstance(douban, list) and len(douban) > 0:
                result['douban'] = douban


        if 'baike' in doc.keys():
            baike = doc['baike']
            if isinstance(baike, dict):
                result['baike'] = baike

        if 'originsourceSiteName' in doc.keys():
            result['originsourceSiteName'] = doc['originsourceSiteName']

        if 'imgUrls' in doc.keys():
            imgs = doc['imgUrls']
            if isinstance(imgs, list) and len(imgs) >0:
                result['imgUrl'] = imgs[-1]



        left_relate = relate["left"]
        mid_relate = relate["middle"]
        bottom_relate = relate["bottom"]
        opinion = relate["opinion"]
        deep_relate = relate["deep_report"]

        allList = [left_relate, mid_relate, bottom_relate, opinion, deep_relate]

        allrelate = []

        for ones in allList:

            for e in ones:

                relate_url = e["url"]
                #title 为空 跳过
                if 'title' in e.keys():
                    if not e['title']:
                        continue

                if relate_url in filterurls:
                    continue

                ct_img = Get_by_url(relate_url)

                e["img"] = ct_img['img']
                # e['content'] = ct_img['content']

                allrelate.append(e)


        for one in docs_relate:
            ls = {}
            url_here = one["url"]
            title_here = one["title"]
            sourceSiteName = one["sourceSiteName"]
            time = one["updateTime"]

            imgUrl = ''

            if "imgUrl" in one.keys():
                imgUrls = one["imgUrl"]
                if isinstance(imgUrls, list) and len(imgUrls) > 0:
                    imgUrl = imgUrls[-1]
                else:
                    continue
            if not imgUrl:
                continue

            # ls = [url_here, title_here, imgUrl, originsourceSiteName]
            ls["title"] = title_here
            ls["url"] = url_here
            ls["img"] = imgUrl
            ls["sourceSitename"] = sourceSiteName


            allrelate.append(ls)

        result["relate"] = allrelate
        result["rc"] = 200

        return result




def Get_by_url(url):

    apiUrl_img = "http://121.41.75.213:8080/extractors_mvc_war/api/getImg?url="
    apiUrl_text = "http://121.41.75.213:8080/extractors_mvc_war/api/getText?url="

    apiUrl_img += url
    apiUrl_text += url

    r_img = requests.get(apiUrl_img)
    r_text = requests.get(apiUrl_text)

    img = (r_img.json())["imgs"]
    text = (r_text.json())["text"]

    result = {"img": img[-1], "content": text}

    return result







