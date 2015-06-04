#coding=utf-8
from PIL import Image

from config import dbConn
import requests
from home_get import del_dup_relatedoc

import jieba
from gensim import corpora, models, similarities

DBStore = dbConn.GetDateStore()

def fetchContent(url, filterurls, updateTime=None):

    conn = DBStore._connect_news

    doc = conn["news_ver2"]["googleNewsItem"].find_one({"sourceUrl": url})

    if not doc:
        return

    if updateTime is None:
        updateTime = ''

    docs_relate = conn["news"]["AreaItems"].find({"relateUrl": url}).sort([("updateTime",-1)]).limit(10)

    doc_comment = conn["news_ver2"]["commentItems"].find_one({"relateUrl": url})

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

    if doc_comment:
        if doc_comment["comments"] is not None:
            if 'weibo' not in doc.keys():
                result['weibo'] = []
            comments_list = doc_comment["comments"]
            for comments_elem in comments_list:
                comments_elem_dict={}
                dict_len = len(comments_elem)
                comment_result = comments_elem[str(dict_len)]
                comments_elem_dict["user"] = comment_result["author_name"]
                comments_elem_dict["title"] = comment_result["message"]
                comments_elem_dict["sourceSitename"] = "weibo"
                comments_elem_dict["img"] = ""
                comments_elem_dict["url"] = ""
                comments_elem_dict["profileImageUrl"] = ""
                comments_elem_dict["isCommentFlag"] = 1
                comments_elem_dict["up"] = comment_result["up"]
                comments_elem_dict["down"] = comment_result["down"]
                result['weibo'].append(comments_elem_dict)



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

    if "imgWall" in doc.keys():
        result["imgWall"] = doc["imgWall"]


    result["updateTime"] = doc["updateTime"]
    result["title"] = doc["title"]

    result["relate"] = allrelate
    result["rc"] = 200

    if doc_comment:
        if doc_comment["comments"] is not None:
            points = project_comments_to_paragraph(doc, doc_comment["comments"])

    pointsCursor = conn["news_ver2"]["pointItem"].find({"sourceUrl": url}).sort([("type", -1)])
    points = get_points(pointsCursor)
    result["point"] = points

    return result


def get_points(points):
    result_points = []
    for point in points:
        point.pop('_id', None)
        createTime = point.pop('createTime', None)
        point['createTime_str'] = createTime.strftime("%Y-%m-%d %H:%M:%S")
        result_points.append(point)

    return result_points


def project_comments_to_paragraph(doc, comments):
    points = []
    textblocks = doc['content'].split('\n')
    for comments_elem in comments:
        comments_elem_dict={}
        dict_len = len(comments_elem)
        comment_result = comments_elem[str(dict_len)]
        for textblock in textblocks:
            pass
        comments_elem_dict["user"] = comment_result["author_name"]
        comments_elem_dict["title"] = comment_result["message"]
        comments_elem_dict["sourceSitename"] = "weibo"
        comments_elem_dict["img"] = ""
        comments_elem_dict["url"] = ""
        comments_elem_dict["profileImageUrl"] = ""
        comments_elem_dict["isCommentFlag"] = 1
        comments_elem_dict["up"] = comment_result["up"]
        comments_elem_dict["down"] = comment_result["down"]

    return points


def cal_sim(textList):

    dictionary = corpora.Dictionary(textList)
    corpus = [dictionary.doc2bow(text) for text in textList]
    tfidf = models.TfidfModel(corpus) # step 1 -- initialize a model
    corpus_tfidf = tfidf[corpus]
    lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=2) # initialize an LSI transformation
    index = similarities.MatrixSimilarity(lsi[corpus]) # transform corpus to LSI space and index it
    sims_list =[]
    for x in range(len(textList)):
        vec_lsi = lsi[corpus[x]]
        sims = index[vec_lsi]
        sims_list.append(list(enumerate(sims)))
    r = {}
    w = []
    for sl in sims_list:
        for v,k in sl:
            r[v] = k
        w.append(r)
    dl = [dict(t) for t in sims_list]
    # for m in dl:
    #     if min()
    mdl = []
    # min_val = min(u.iteritems())
    # min_val_d = {k:v for k, v in u.iteritems() if v == min_val}

    for x in dl:
        min_v = min(x.itervalues())
        mdlo = {k:v for k,v in x.iteritems() if v == min_v}
        # mdl.append(min_v)
        mdl.append(mdlo)
    smdl = sorted(mdl, key = lambda k:k)
    # fr = sorted(dl)

    print smdl
    print sims_list



def Get_Relate_docs(doc, docs_relate, filterurls):

    allrelate = []

    if "reorganize" in doc.keys() and doc["reorganize"]:
        allrelate.extend(doc["reorganize"])

    if "relate" in doc.keys() and doc["relate"]:
        relate = doc["relate"]
        if "reorganize" in doc.keys() and doc["reorganize"]:
            relate = del_dup_relatedoc(relate, doc["reorganize"])
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
            elif isinstance(imgUrls, unicode):
                imgUrl = imgUrls.encode('utf-8')


        # if not imgUrl:
        #     continue

        ls["title"] = title_here
        ls["url"] = url_here
        ls["img"] = imgUrl
        ls["sourceSitename"] = sourceSiteName
        ls["updateTime"] = updatetime
        ls['height'] = 75
        ls['width'] = 121

        allrelate.append(ls)

    return allrelate



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
    textList = []
    cal_sim(textList)
    print (ImgMeetCondition("http://img6.cutv.com/forum/201406/04/150731hffegglg1es9bufa.jpg"))