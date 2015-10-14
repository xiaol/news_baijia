# coding=utf-8
#from PIL import Image
import Image
from config import dbConn
from home_get import del_dup_relatedoc
import jieba
import gensim
from sklearn.svm import SVC
from math import sqrt
import numpy as np
import math
import bson
import tornado

DBStore = dbConn.GetDateStore()

@tornado.gen.coroutine
def fetchContent(url, filterurls, userId, platformType, updateTime=None):
    conn = DBStore._connect_news

    doc = conn["news_ver2"]["googleNewsItem"].find_one({"sourceUrl": url})

    if not doc:
        return

    if updateTime is None:
        updateTime = ''

    docs_relate = conn["news"]["AreaItems"].find({"relateUrl": url}).sort([("updateTime", -1)]).limit(10)

    doc_comment = conn["news_ver2"]["commentItems"].find_one({"relateUrl": url})

    result = {}

    allrelate = Get_Relate_docs(doc, docs_relate, filterurls)
    for relate_elem in allrelate:
        if "text" in relate_elem.keys():
            del relate_elem["text"]

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

    # if doc_comment:
    #     if doc_comment["comments"] is not None:
    #         if 'weibo' not in doc.keys():
    #             result['weibo'] = []
    #         comments_list = doc_comment["comments"]
    #         for comments_elem in comments_list:
    #             comments_elem_dict = {}
    #             dict_len = len(comments_elem)
    #             comment_result = comments_elem[str(dict_len)]
    #             comments_elem_dict["user"] = comment_result["author_name"]
    #             comments_elem_dict["title"] = comment_result["message"]
    #             comments_elem_dict["sourceSitename"] = "weibo"
    #             comments_elem_dict["img"] = ""
    #             comments_elem_dict["url"] = ""
    #             comments_elem_dict["profileImageUrl"] = ""
    #             comments_elem_dict["isCommentFlag"] = 1
    #             comments_elem_dict["up"] = comment_result["up"]
    #             comments_elem_dict["down"] = comment_result["down"]
    #             result['weibo'].append(comments_elem_dict)

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
        if isinstance(imgs, list) and len(imgs) > 0:
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

    result_points = []

    praise = conn['news_ver2']['praiseItem'].find({'sourceUrl': url})  # ({'uuid': uuid, 'commentId': commentId})
    praise_list = []
    for praise_elem in praise:
        praise_list.append(praise_elem)

    pointsCursor = conn["news_ver2"]["pointItem"].find({"sourceUrl": url}).sort([("type", -1)])
    points_fromdb = get_points(pointsCursor, praise_list, userId, platformType)

    if doc_comment and 'content' in doc:
        if doc_comment["comments"]:
            for doc_comment_elem in doc_comment["comments"]:
                dict_len = len(doc_comment_elem)
                comment_result = doc_comment_elem[str(dict_len)]
                if 'comment_id' in comment_result.keys():
                    # praise_num = praise.find({'commentId': comment_result["comment_id"]}).count()
                    praise_num = count_praise({'commentId': comment_result["comment_id"]}, praise_list)
                    up = int(comment_result['up'])
                    comment_result['up'] = up + praise_num
                if userId and platformType and 'comment_id' in comment_result.keys():
                    isPraiseFlag = count_praise(
                        {'userId': userId, 'platformType': platformType, 'commentId': comment_result["comment_id"]},
                        praise_list)
                    if isPraiseFlag:
                        comment_result['isPraiseFlag'] = 1
                    else:
                        comment_result['isPraiseFlag'] = 0
                else:
                    comment_result['isPraiseFlag'] = 0

            points = project_comments_to_paragraph(doc, doc_comment["comments"])
            result_points.extend(points)
    points_fromdb.extend(result_points)

    paragraph_comment_count = {}
    flag = False
    for point_ele in points_fromdb:
        if point_ele['paragraphIndex'] in paragraph_comment_count:
            paragraph_comment_count[point_ele['paragraphIndex']] += 1
        else:
            paragraph_comment_count[point_ele['paragraphIndex']] = 1
    for point_ele in points_fromdb:
        point_ele['comments_count'] = paragraph_comment_count[point_ele['paragraphIndex']]

        # ariesy 2015-6-17 提取语音弹幕
        if (flag == False and "speech_paragraph" == point_ele["type"] or "speech_doc" == point_ele["type"]):
            flag = True
            result["isdoc"] = True
            result["docUrl"] = point_ele["srcText"]
            result["docTime"] = point_ele["srcTextTime"]
            result["docUserIcon"] = point_ele["userIcon"]
    result["point"] = points_fromdb
    if (flag == False):
        result["isdoc"] = False

    if "relate_opinion" in doc.keys():
        if "common_opinion" in doc["relate_opinion"].keys():
            del doc["relate_opinion"]["common_opinion"]
        result["relate_opinion"] = doc["relate_opinion"]

    if "sourceSiteName" in doc.keys():
        sourceSitename = doc["sourceSiteName"]
        result["category"] = sourceSitename[2:4]

    #return result
    raise tornado.gen.Return(result)

def get_points(points, praise_list, userId, platformType):
    result_points = []
    for point in points:
        point.pop('_id', None)

        if 'commentId' in point.keys():
            praise_num = count_praise({'commentId': point["commentId"]}, praise_list)
            point['up'] = praise_num
        else:
            point['up'] = 0
        if userId and platformType and 'commentId' in point.keys():
            isPraiseFlag = count_praise(
                {'userId': userId, 'platformType': platformType, 'commentId': point["commentId"]}, praise_list)
            if isPraiseFlag:
                point['isPraiseFlag'] = 1
            else:
                point['isPraiseFlag'] = 0
        else:
            point['isPraiseFlag'] = 0

        if 'commentId' not in point:
            point['commentId'] = ''
        createTime = point.pop('createTime', None)
        point['createTime_str'] = createTime.strftime("%Y-%m-%d %H:%M:%S")
        point['createTime'] = createTime.strftime("%Y-%m-%d %H:%M:%S")
        result_points.append(point)

    return result_points

@tornado.gen.coroutine
def newsFetchContent(news_id, url, filterurls, userId, platformType, deviceType, updateTime=None):
    conn = DBStore._connect_news
    if news_id:
        # id = bson.objectid.ObjectId(news_id)
        doc = conn["news_ver2"]["testForReactiveMongoV1"].find_one({"_id": news_id})
    else:
        doc = conn["news_ver2"]["NewsItems"].find_one({"source_url": url})

    if not doc:
        result = {'response': '未找到相关内容'}
        return result

    if "_id" in doc.keys():
        doc.pop('_id')

    if updateTime is None:
        updateTime = ''

    if news_id:
        docs_relate = []
        doc_comment = []
        allrelate = []
        if "aggre_items" in doc.keys():
            aggre_items = doc["aggre_items"]
            for aggre in aggre_items:
                ls = {}
                for (k,v) in aggre.items():
                    ls["title"] = v
                    ls["url"] = k
                    ls["sourceSitename"] = v
                    ls['height'] = 75
                    ls['width'] = 121
                    allrelate.append(ls)
    else:
        docs_relate = conn["news"]["AreaItems"].find({"relateUrl": url}).sort([("updateTime", -1)]).limit(10)
        doc_comment = conn["news_ver2"]["commentItems"].find_one({"relateUrl": url})
        allrelate = Get_Relate_docs(doc, docs_relate, filterurls)
    result = getContentJson()

    result['imgUrl'] = getImg(doc)
    # result['abs'] = getText(doc)

    if "abs" in doc.keys():
        result["abs"] = doc["abs"]

    if allrelate:
        for relate_elem in allrelate:
            if "text" in relate_elem.keys():
                del relate_elem["text"]

    if "title" in doc.keys():
        result["title"] = doc["title"]

    if 'content' in doc.keys():
        if deviceType == 'IOS':
            contentlist = []
            docs = doc['content']
            i = 0
            for doc in docs:
                for key in doc.keys():
                    if doc[key].keys()[0] == 'img_info' and contentlist[-1].keys()[1] == 'img':
                        contentlist[-1]['img_info'] = doc[key].values()[0]
                        contentlist[-1]['index'] = i - 1
                        i = i + 1
                    else:
                        contentDoc = doc[key]
                        contentDoc['index'] = i
                        contentlist.append(contentDoc)
                        i = i + 1
            result['content'] = contentlist
        else:
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
        if isinstance(imgs, list) and len(imgs) > 0:
            result['imgUrl'] = imgs[-1]

    if "root_class" in doc.keys():
        result["root_class"] = doc["root_class"]

    if "sourceSitename" in doc.keys():
        category = doc["sourceSitename"]
        result["category"] = category[2:4]

    if "imgWall" in doc.keys():
        result["imgWall"] = doc["imgWall"]

    if "update_time" in doc.keys():
        result["updateTime"] = doc["update_time"]

    if doc_comment:
        if doc_comment["comments"] is not None:
            if 'weibo' not in doc.keys():
                result['weibo'] = []
            comments_list = doc_comment["comments"]
            for comments_elem in comments_list:
                comments_elem_dict = {}
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

    result["relate"] = allrelate
    result["rc"] = 200

    result_points = []

    praise = conn['news_ver2']['praiseItem'].find({'sourceUrl': url})  # ({'uuid': uuid, 'commentId': commentId})
    praise_list = []
    for praise_elem in praise:
        praise_list.append(praise_elem)

    if doc_comment and 'content' in doc:
        if doc_comment["comments"]:
            for doc_comment_elem in doc_comment["comments"]:
                dict_len = len(doc_comment_elem)
                comment_result = doc_comment_elem[str(dict_len)]
                if 'comment_id' in comment_result.keys():
                    # praise_num = praise.find({'commentId': comment_result["comment_id"]}).count()
                    praise_num = count_praise({'commentId': comment_result["comment_id"]}, praise_list)
                    up = int(comment_result['up'])
                    comment_result['up'] = up + praise_num
                if userId and platformType and 'comment_id' in comment_result.keys():
                    isPraiseFlag = count_praise(
                        {'userId': userId, 'platformType': platformType, 'commentId': comment_result["comment_id"]},
                        praise_list)
                    if isPraiseFlag:
                        comment_result['isPraiseFlag'] = 1
                    else:
                        comment_result['isPraiseFlag'] = 0
                else:
                    comment_result['isPraiseFlag'] = 0

            points = project_comments_to_paragraph(doc, doc_comment["comments"])
            result_points.extend(points)

    pointsCursor = conn["news_ver2"]["pointItem"].find({"sourceUrl": url}).sort([("type", -1)])
    points_fromdb = get_points(pointsCursor, praise_list, userId, platformType)
    result_points.extend(points_fromdb)

    paragraph_comment_count = {}
    flag = False
    for point_ele in result_points:
        if point_ele['paragraphIndex'] in paragraph_comment_count:
            paragraph_comment_count[point_ele['paragraphIndex']] += 1
        else:
            paragraph_comment_count[point_ele['paragraphIndex']] = 1
    for point_ele in result_points:
        point_ele['comments_count'] = paragraph_comment_count[point_ele['paragraphIndex']]

        # ariesy 2015-6-17 提取语音弹幕
        if (flag == False and "speech_paragraph" == point_ele["type"] or "speech_doc" == point_ele["type"]):
            flag = True
            result["isdoc"] = True
            result["docUrl"] = point_ele["srcText"]
            result["docTime"] = point_ele["srcTextTime"]
            result["docUserIcon"] = point_ele["userIcon"]
    result["point"] = result_points
    if (flag == False):
        result["isdoc"] = False

    if "relate_opinion" in doc.keys():
        if "common_opinion" in doc["relate_opinion"].keys():
            del doc["relate_opinion"]["common_opinion"]
        result["relate_opinion"] = doc["relate_opinion"]

    #return result
    raise tornado.gen.Return(result)

def getImg(doc):
    if "content" in doc.keys():
        for _doc in doc['content']:
            for k, item_doc in _doc.iteritems():
                if "img" in item_doc.keys():
                    return item_doc['img']


def getText(doc):
    if "content" in doc.keys():
        for _doc in doc['content']:
            for k, item_doc in _doc.iteritems():
                if "txt" in item_doc.keys():
                    return item_doc['txt']


def newsFetchContentList(type, url, filterurls, userId, platformType, deviceType, updateTime=None):
    if int(type) == 0:
        return fetchContent(url, filterurls, userId, platformType, updateTime)
    else:
        return newsFetchContent(url, filterurls, userId, platformType, updateTime, deviceType)


def project_comments_to_paragraph(doc, comments):
    points = []
    textblocks = []
    for content in doc['content'].split('\n'):
        textblocks.append({'content': content})
    if len(textblocks) == 1:
        for comments_elem in comments:
            dict_len = len(comments_elem)
            comment_result = comments_elem[str(dict_len)]
            userName = comment_result['author_name'].replace('网易', '')
            if 'author_img_url' in comment_result:
                userIcon = comment_result['author_img_url']
            else:
                userIcon = ""

            if 'comment_id' not in comment_result:
                comment_result["comment_id"] = ""

            point = {'sourceUrl': doc['sourceUrl'], 'srcText': comment_result["message"], 'desText': "",
                     'paragraphIndex': 0, 'type': "text_paragraph", 'uuid': "", 'userIcon': userIcon,
                     'userName': userName, 'createTime': comment_result["created_at"],
                     "up": comment_result["up"], "down": comment_result["down"], "comments_count": len(comments),
                     "commentId": comment_result["comment_id"], "isPraiseFlag": comment_result["isPraiseFlag"]}
            points.append(point)
        return points

    textblock_dict = {}
    paragraphIndex = 0
    for textblock in textblocks:
        if not textblock['content']:
            continue
        textblock_dict[str(paragraphIndex) + '_p'] = textblock['content']
        paragraphIndex += 1

    comments_dict = {}
    comments_index = 0
    for comments_elem in comments:
        dict_len = len(comments_elem)
        comment_result = comments_elem[str(dict_len)]
        comments_dict[str(comments_index) + '_c'] = comment_result["message"]
        comments_index += 1

    sims = doc_classify(textblock_dict, comments_dict)

    if not sims:
        for comments_elem in comments:
            dict_len = len(comments_elem)
            comment_result = comments_elem[str(dict_len)]
            userName = comment_result['author_name'].replace('网易', '')
            if 'author_img_url' in comment_result:
                userIcon = comment_result['author_img_url']
            else:
                userIcon = ""

            if 'comment_id' not in comment_result:
                comment_result["comment_id"] = ""

            point = {'sourceUrl': doc['sourceUrl'], 'srcText': comment_result["message"], 'desText': "",
                     'paragraphIndex': 0, 'type': "text_doc", 'uuid': "", 'userIcon': userIcon,
                     'userName': userName, 'createTime': comment_result["created_at"],
                     "up": comment_result["up"], "down": comment_result["down"], "comments_count": 1,
                     "commentId": comment_result["comment_id"], "isPraiseFlag": comment_result["isPraiseFlag"]}
            points.append(point)
    else:
        comments_index = 0
        for comments_elem in comments:
            dict_len = len(comments_elem)
            comment_result = comments_elem[str(dict_len)]
            userName = comment_result['author_name'].replace('网易', '')
            if 'author_img_url' in comment_result:
                userIcon = comment_result['author_img_url']
            else:
                userIcon = ""
            if 'comment_id' not in comment_result:
                comment_result["comment_id"] = ""

            point = {'sourceUrl': doc['sourceUrl'], 'srcText': comment_result["message"], 'desText': "",
                     'paragraphIndex': int(sims[str(comments_index) + '_c'].split('_')[0]), 'type': "text_paragraph",
                     'uuid': "", 'userIcon': userIcon,
                     'userName': userName, 'createTime': comment_result["created_at"],
                     "up": comment_result["up"], "down": comment_result["down"], "comments_count": 1,
                     "commentId": comment_result["comment_id"], "isPraiseFlag": comment_result["isPraiseFlag"]}
            points.append(point)
            comments_index += 1

    return points


def vec2dense(vec, num_terms):
    '''Convert from sparse gensim format to dense list of numbers'''
    return list(gensim.matutils.corpus2dense([vec], num_terms=num_terms).T[0])


# training_data can be a a dictionary of different paragraphs,data_to_classify can be a
# a dictionary of different commnents to be classified to those paragraphs.
def doc_classify(training_data, data_to_classify):
    # Load in corpus, remove newlines, make strings lower-case
    if len(training_data) == 1 or not training_data:
        message = "The number of classes has to be greater than one; got 1 or 0."
        print message
        return
    docs = {}
    docs.update(training_data)
    docs.update(data_to_classify)
    names = docs.keys()

    preprocessed_docs = {}
    for name in names:
        preprocessed_docs[name] = list(jieba.cut(docs[name]))

    # Build the dictionary and filter out rare terms
    # Perform Chinese words segmentation.
    dct = gensim.corpora.Dictionary(preprocessed_docs.values())
    unfiltered = dct.token2id.keys()
    dct.filter_extremes(no_below=2)
    filtered = dct.token2id.keys()
    filtered_out = set(unfiltered) - set(filtered)


    # Build Bag of Words Vectors out of preprocessed corpus
    bow_docs = {}
    for name in names:
        sparse = dct.doc2bow(preprocessed_docs[name])
        bow_docs[name] = sparse
        dense = vec2dense(sparse, num_terms=len(dct))

    # Dimensionality reduction using LSI. Go from 6D to 2D.
    print "\n---LSI Model---"

    lsi_docs = {}
    num_topics = 2
    lsi_model = gensim.models.LsiModel(bow_docs.values(),
                                       num_topics=num_topics)
    for name in names:
        vec = bow_docs[name]
        sparse = lsi_model[vec]
        dense = vec2dense(sparse, num_topics)
        lsi_docs[name] = sparse

    # Normalize LSI vectors by setting each vector to unit length
    print "\n---Unit Vectorization---"

    unit_vecs = {}

    for name in names:

        vec = vec2dense(lsi_docs[name], num_topics)
        norm = sqrt(sum(num ** 2 for num in vec))
        with np.errstate(invalid='ignore'):
            unit_vec = [num / norm for num in vec]
        if math.isnan(unit_vec[0]) | math.isnan(unit_vec[1]):
            unit_vec = [0.0, 0.0]

        unit_vecs[name] = unit_vec
    # Take cosine distances between docs and show best matches
    print "\n---Document Similarities---"

    index = gensim.similarities.MatrixSimilarity(lsi_docs.values())
    for i, name in enumerate(names):

        vec = lsi_docs[name]
        sims = index[vec]
        sims = sorted(enumerate(sims), key=lambda item: -item[1])

        # Similarities are a list of tuples of the form (doc #, score)
        # In order to extract the doc # we take first value in the tuple
        # Doc # is stored in tuple as numpy format, must cast to int

        if int(sims[0][0]) != i:
            match = int(sims[0][0])
        else:
            match = int(sims[1][0])

        match = names[match]

    print "\n---Classification---"

    train = [unit_vecs[key] for key in training_data.keys()]

    labels = [(num + 1) for num in range(len(training_data.keys()))]
    label_to_name = dict(zip(labels, training_data.keys()))
    classifier = SVC()
    classifier.fit(train, labels)
    result = {}
    for name in names:

        vec = unit_vecs[name]
        label = classifier.predict([vec])[0]
        cls = label_to_name[label]
        if name in data_to_classify.keys():
            result[name] = cls
    return result


def Get_Relate_docs(doc, docs_relate, filterurls):
    allrelate = []

    # if "reorganize" in doc.keys() and doc["reorganize"]:
    #     allrelate.extend(doc["reorganize"])

    # if "relate" in doc.keys() and doc["relate"]:
    #     relate = doc["relate"]
    #     if "reorganize" in doc.keys() and doc["reorganize"]:
    #         relate = del_dup_relatedoc(relate, doc["reorganize"])
    #     left_relate = relate["left"]
    #     mid_relate = relate["middle"]
    #     bottom_relate = relate["bottom"]
    #     opinion = relate["opinion"]
    #     deep_relate = relate["deep_report"]
    #
    #     allList = [left_relate, mid_relate, bottom_relate, opinion, deep_relate]
    #
    #     for ones in allList:
    #
    #         for e in ones:
    #
    #             relate_url = e["url"]
    #             # title 为空 跳过
    #             if 'title' in e.keys():
    #                 if not e['title']:
    #                     continue
    #
    #             if relate_url in filterurls:
    #                 continue
    #
    #             # ct_img = Get_by_url(relate_url)
    #             # #
    #             # e["img"] = ct_img['img']
    #             if not "img" in e.keys():
    #                 e["img"] = ""
    #
    #             allrelate.append(e)

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


def getContentJson():
    return {"abs": "", "baike": [], "content": "", "docTime": "", "docUrl": "", "docUserIcon": "", "douban": [],
            "imgUrl": "", "imgWall": [], "zhihu": [], "ne": {}, "originsourceSiteName": "", "point": [], "relate": [],
            "root_class": "", "title": "", "updateTime": "", "weibo": [], "isdoc": False}


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


def count_praise(find_condition_dict, praise_list):
    parse_num = 0
    for prase_elem in praise_list:
        names = find_condition_dict.keys()
        same_num = 0
        for name in names:
            if find_condition_dict[name] == prase_elem[name]:
                same_num = same_num + 1
        if same_num == len(names):
            parse_num = parse_num + 1

    return parse_num


if __name__ == '__main__':
    # print(Get_by_url("http://xinmin.news365.com.cn/tyxw/201503/t20150323_1779650.html"))
    # print(Get_by_url("http://www.jfdaily.com/guonei/new/201503/t20150323_1348362.html"))
    # print(Get_by_url("http://sports.sina.com.cn/l/s/2015-03-24/10287553303.shtml"))
    # print(ImgMeetCondition("http://xinmin.news365.com.cn/images/index_3.jpg"))
    textList = []
    print (ImgMeetCondition("http://img6.cutv.com/forum/201406/04/150731hffegglg1es9bufa.jpg"))
