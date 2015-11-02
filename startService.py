#!/usr/bin/python
# -*- coding: utf-8 -*-


__author__ = 'jianghao'

import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.httpclient
import sys
import tornado.netutil
import json
from controller import home_get, content_get, time_get, login_get, im_get, point_post, channel_get, point_get, \
    praise_post, start_page_post, dredge_up_post, elementary_post, tags_get, recommend
from controller import search
from controller.push import push_message
import abstract
from tornado.options import define, options
import tornado.gen
import tornado.concurrent
from AI_funcs.Gist_and_Sim.gist import Gist
import pymongo
from pymongo.read_preferences import ReadPreference
# import redis
# r = redis.Redis('121.40.34.56','6379',db=1)

# define("port", default=9999, help="run on the given port", type=int)
define("host", default="127.0.0.1", help="run on the given host", type=str)

conn = pymongo.MongoReplicaSetClient("h44:27017, h213:27017, h241:27017", replicaSet="myset",
                                     read_preference=ReadPreference.SECONDARY)

class SearchHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def post(self):
        userid = self.get_argument("userid", None)
        deviceid = self.get_argument("deviceid", None)
        keyword = self.get_argument("keyword", None)
        start = self.get_argument("start", None)
         
        result = yield search.search(keyword, start)
        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result)) 

class recommendHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def post(self):
        userId = self.get_argument("userid", None)
        deviceId = self.get_argument("deviceid", None)
        channelId = self.get_argument("channelid", None)
        result = yield recommend.recommend(deviceId, channelId)
        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))


class fetchDetailHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def post(self):
        userId = self.get_argument("userid", None)
        platformType =  self.get_argument("platformtype", None)
        deviceId = self.get_argument("deviceid", None)
        deviceType = self.get_argument("devicetype", None)
        newsId = self.get_argument("newsid", None)
        collection = self.get_argument("collection", None)

        result = yield recommend.fetchDetail(newsId, collection,userId,platformType)
        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))



@tornado.gen.coroutine
def coroutine_fetch():
    result = r.hmget("googleNewsItems", "googleNewsItems")
    raise tornado.gen.Return(result)


class FetchHomeHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        # updateTime = self.get_argument("updateTime", None)
        limit = self.get_argument("limit", 10)
        page = self.get_argument("page", 1)
        timing = self.get_argument("timenews", None)
        timefeedback = self.get_argument("timefeedback", None)
        date = self.get_argument("date", None)
        type = self.get_argument("type", None)
        channelId = self.get_argument("channelId", None)

        options = {}
        options["page"] = int(page)
        options["limit"] = int(limit)

        if timing:
            options["timing"] = timing
        if timefeedback:
            options["timefeedback"] = timefeedback

        if date:
            options["date"] = date
        if type:
            options["type"] = type

        if channelId:
            options["channelId"] = channelId



            # if updateTime:
            # options["updateTime"] = updateTime
        # result = yield home_get.homeContentFetch(options)

        # result = home_get.homeContentFetch(options)
        # result = conn['news_ver2']['resultItem'].find_one()["content"]
        #if "timing" in options.keys():
        #    result_list = yield conn['news_ver2']['resultItem'].find().sort([("createTime", pymongo.DESCENDING)]).limit(1)
        #elif "date" in options.keys():
        #    result_list = yield conn['news_ver2']['resultItemByDate'].find(
        #        {"date": options["date"], "type": options["type"]}).sort([("createTime", pymongo.DESCENDING)]).limit(1)
        result_list = yield feedstream(options)
        for result_elem in result_list:
            result = result_elem["content"]
            break

        # print result
        # result = yield coroutine_fetch()
        # result = result[0]
        # result = eval(result)

        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))
        # self.finish()

#zuoyuan
@tornado.gen.coroutine
def feedstream(options):
    if "timing" in options.keys():
        result_list = conn['news_ver2']['resultItem'].find().sort([("createTime", pymongo.DESCENDING)]).limit(1)
    elif "date" in options.keys():
        result_list = conn['news_ver2']['resultItemByDate'].find({"date": options["date"], "type": options["type"]}).sort([("createTime", pymongo.DESCENDING)]).limit(1)
    raise tornado.gen.Return(result_list)
#zuoyuan

class NewsFetchHomeHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        # updateTime = self.get_argument("updateTime", None)
        limit = self.get_argument("limit", 10)
        page = self.get_argument("page", 1)
        timing = self.get_argument("timenews", None)
        timefeedback = self.get_argument("timefeedback", None)
        date = self.get_argument("date", None)
        type = self.get_argument("type", None)
        channelId = self.get_argument("channelId", None)

        options = {}
        options["page"] = int(page)
        options["limit"] = int(limit)

        if timing:
            options["timing"] = timing
        if timefeedback:
            options["timefeedback"] = timefeedback

        if date:
            options["date"] = date
        if type:
            options["type"] = type

        if channelId:
            options["channelId"] = channelId


            # if updateTime:
            # options["updateTime"] = updateTime
        result = yield home_get.newsHomeContentFetch(options)

        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))


class LoadMoreNewsContentHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def post(self):
        args = self.request.arguments
        type = self.get_argument("type", 0)
        time = self.get_argument("time", None)
        limit = self.get_argument("limit", 10)
        id = self.get_argument("news_id", None)
        channel_id = self.get_argument("channel_id", 0)

        options = {}
        options["limit"] = int(limit)
        options["time"] = time
        options["type"] = int(type)
        options["channel_id"] = channel_id
        options["id"] = id

        if len(args) < 3:
            result = {'response': 201, 'msg': 'Hey Dude ->'}
        else:
            result = yield home_get.LoadMoreNewsContent(options)

        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))


class FetchTimeHandler(tornado.web.RequestHandler):
    def get(self):
        timefeedback = self.get_argument("timefeedback", None)
        options = {}
        if timefeedback:
            options["timefeedback"] = timefeedback
        result = time_get.timeContentFetch(options)

        print result

        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))


class FetchContentHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        self.set_header("Access-Control-Allow-Origin",
                        "*")  # TODO should change to exact domain after test in localhost
        self.set_header("Content-Type", "Application/json")
        args = self.request.uri
        url = args.split("url=")[1]
        url = url.split("&uuid=")[0]
        url = url.split("&filterurls")[0]
        url = url.split("&userId")[0]
        url = url.split("&platformType")[0]
        filter_urls = self.get_arguments("filterurls")
        uuid = self.get_argument("uuid", None)
        result = {}
        userId = self.get_argument("userId", None)
        platformType = self.get_argument("platformType", None)

        if not url:
            result["rc"] = 404
            result["msg"] = "need url"
            self.write(json.dumps(result))
            return

        result = yield content_get.fetchContent(url, filter_urls, userId, platformType)

        self.write(json.dumps(result))


class NewsFetchContentHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        self.set_header("Content-Type", "Application/json")
        url = self.get_argument("url", None)
        filter_urls = self.get_arguments("filterurls")
        userId = self.get_argument("userId", None)
        platformType = self.get_argument("platformType", None)
        deviceType = self.get_argument("deviceType", None)
        news_id = self.get_argument("news_id", None)
        result = {}
        if not url:
            result["rc"] = 404
            result["msg"] = "need url"
            self.write(json.dumps(result))
            return
        result = yield content_get.newsFetchContent(news_id, url, filter_urls, userId, platformType, deviceType)

        self.write(json.dumps(result))

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        self.set_header("Access-Control-Allow-Origin",
                        "*")  # TODO should change to exact domain after test in localhost
        args = self.request.arguments
        filter_urls = self.get_arguments("filterurls")
        userId = self.get_argument("userId", None)
        platformType = self.get_argument("platformType", None)
        deviceType = self.get_argument("deviceType", None)
        news_id = self.get_argument("news_id", None)
        url = self.get_argument("url", None)
        if len(args) < 1:
            result = {'response': 201, 'msg': 'Hey Dude ->'}
        else:
            result = yield content_get.newsFetchContent(news_id, url, filter_urls, userId, platformType, deviceType)

        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))


class NewsFetchContentListHandler(tornado.web.RequestHandler):
    def post(self):
        args = self.request.arguments
        type = self.get_argument("type", 0)
        filter_urls = self.get_arguments("filterurls")
        userId = self.get_argument("userId", None)
        platformType = self.get_argument("platformType", None)
        urls = self.get_argument("url", None)
        deviceType = self.get_argument("deviceType", None)
        urls = urls.split(",")
        result = []
        if len(args) < 1:
            result = {'response': 201, 'msg': 'Hey Dude ->'}
        else:
            for url in urls:
                result.append(
                    content_get.newsFetchContentList(type, url, filter_urls, userId, platformType, deviceType))

        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))

#zuoyuan
class FetchDredgeUpStatusforiOSHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def post(self):
        args = self.request.arguments
        #user_id = self.get_argument("user_id", None)
        uid = self.get_argument("uid", None)
        album = self.get_argument("album", None)
        key = self.get_argument("key", None)
        if len(args) < 1:
            result = {'response': 201, 'msg': 'Hey Dude ->'}
        else:
            result = yield dredge_up_post.dredgeUpStatusforiOS(uid, album, key)
        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))
#zuoyuan


class FetchDredgeUpStatusHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def post(self):
        args = self.request.arguments
        user_id = self.get_argument("user_id", None)
        album_id = self.get_argument("album_id", None)
        is_add = self.get_argument("is_add", 0)
        if len(args) < 1:
            result = {'response': 201, 'msg': 'Hey Dude ->'}
        else:
            result = yield dredge_up_post.dredgeUpStatus(user_id, album_id, is_add)
        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))


class CreateAlbumHandler(tornado.web.RequestHandler):
    def post(self):
        args = self.request.arguments
        user_id = self.get_argument("user_id", None)
        album_id = self.get_argument("album_id", None)
        create_time = self.get_argument("create_time", None)
        album_title = self.get_argument("album_title", None)
        album_des = self.get_argument("album_des", None)
        album_img = self.get_argument("album_img", None)
        album_news_count = self.get_argument("album_news_count", None)
        if len(args) < 1:
            result = {'response': 201, 'msg': 'Hey Dude ->'}
        else:
            result = dredge_up_post.createAlbum(user_id, album_id, album_title, album_des, album_img, album_news_count,
                                                create_time)
        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))


class CreateAlbumListHandler(tornado.web.RequestHandler):
    def post(self):
        args = self.request.arguments
        albums = json.loads(self.get_argument("album", None))
        result = []
        if len(args) < 0:
            result = {'response': 201, 'msg': 'Hey Dude ->'}
        else:
            for album in albums:
                if "user_id" in album.keys():
                    user_id = album['user_id']
                if "album_id" in album.keys():
                    album_id = album['album_id']
                if "create_time" in album.keys():
                    create_time = album['create_time']
                if "album_title" in album.keys():
                    album_title = album['album_title']
                if "album_des" in album.keys():
                    album_des = album['album_des']
                if "album_img" in album.keys():
                    album_img = album['album_img']
                if "album_news_count" in album.keys():
                    album_news_count = album['album_news_count']
                result.append(
                    dredge_up_post.createAlbum(user_id, album_id, album_title, album_des, album_img, album_news_count,
                                               create_time))
        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))


class UpdateAlbumHandler(tornado.web.RequestHandler):
    def post(self):
        args = self.request.arguments
        album_id = self.get_argument("album_id", None)
        album_title = self.get_argument("album_title", None)
        album_des = self.get_argument("album_des", None)
        album_img = self.get_argument("album_img", None)
        album_news_count = self.get_argument("album_news_count", None)
        if len(args) < 1:
            result = {'response': 201, 'msg': 'Hey Dude ->'}
        else:
            result = dredge_up_post.updateAlbum(album_id, album_title, album_des, album_img, album_news_count)
        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))


class RemoveAlbumHandler(tornado.web.RequestHandler):
    def post(self):
        args = self.request.arguments
        album_id = self.get_argument("album_id", None)
        default_album_id = self.get_argument("default_album_id", None)
        if len(args) < 1:
            result = {'response': 201, 'msg': 'Hey Dude ->'}
        else:
            result = dredge_up_post.removeAlbum(album_id, default_album_id)
        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))


class FetchAlbumListHandler(tornado.web.RequestHandler):
    def post(self):
        args = self.request.arguments
        user_id = self.get_argument("user_id", None)
        if len(args) < 1:
            result = {'response': 201, 'msg': 'Hey Dude ->'}
        else:
            result = dredge_up_post.fetchAlbumList(user_id)
        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))


class FetchLoginHandler(tornado.web.RequestHandler):
    def get(self):
        # updateTime = self.get_argument("updateTime", None)
        uuid = self.get_argument("uuid", None)
        userId = self.get_argument("userId", None)
        token = self.get_argument("token", None)
        userIcon = self.get_argument("userIcon", None)
        userGender = self.get_argument("userGender", None)
        userName = self.get_argument("userName", None)
        expiresIn = self.get_argument("expiresIn", -1)
        expiresTime = self.get_argument("expiresTime", -1)
        platformType = self.get_argument("platformType", None)
        deviceType = self.get_argument("deviceType", "android")

        options = {}
        options["uuid"] = uuid
        options["userId"] = userId
        options["token"] = token
        options["userIcon"] = userIcon
        options["userGender"] = userGender
        options["userName"] = userName
        options["expiresIn"] = expiresIn
        options["expiresTime"] = expiresTime
        options["platformType"] = platformType
        options["deviceType"] = deviceType

        result = login_get.loginContentFetch(options)
        print result
        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))


class FetchImHandler(tornado.web.RequestHandler):
    def get(self):
        message = self.get_argument("message", None)
        try:
            dict_obj = json.loads(message)

            options = {}
            options["receiverId"] = dict_obj["receiverId"]
            options["senderId"] = dict_obj["senderId"]
            options["content"] = dict_obj["content"]
            options["msgType"] = dict_obj["msgType"]
            result = push_message.imContentFetch(options)
        except Exception as e:
            print e
            result = {"response": 303}

        print result
        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))


class PointHandler(tornado.web.RequestHandler):
    def get(self):
        sourceUrl = self.get_argument("sourceUrl", None)
        paragraphIndex = self.get_argument("paragraphIndex", None)
        options = {}
        options["sourceUrl"] = sourceUrl
        options["paragraphIndex"] = paragraphIndex
        result = point_get.pointFetch(options)
        print result
        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))

    def post(self):
        args = self.request.arguments
        if len(args) < 8:
            result = {'response': 201, 'msg': 'Hey Dude ->'}
        else:
            if 'userId' not in args.keys():
                args['userId'] = ['']
            if 'platformType' not in args.keys():
                args['platformType'] = ['']
            if 'srcTextTime' not in args.keys():
                args['srcTextTime'] = [int(-1)]

            result = point_post.AddPoint(args['sourceUrl'][0], args['srcText'][0], args['desText'][0],
                                         args['paragraphIndex'][0],
                                         args['type'][0], args['uuid'][0], args['userIcon'][0], args['userName'][0],
                                         args['userId'][0], args['platformType'][0], int(args['srcTextTime'][0]))
        print result

        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))


class FetchImUserHandler(tornado.web.RequestHandler):
    def get(self):
        uuid = self.get_argument("uuid", None)
        jpushId = self.get_argument("jpushId", None)
        userId = self.get_argument("userId", None)
        platformType = self.get_argument("platformType", None)

        options = {}
        options["uuid"] = uuid
        options["jpushId"] = jpushId
        options["userId"] = userId
        options["platformType"] = platformType
        result = im_get.imUserFetch(options)
        print result
        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))


class uploadUmengPushId(tornado.web.RequestHandler):
    def get(self):
        uuid = self.get_argument("uuid", None)
        umengPushId = self.get_argument("umengPushId", None)
        userId = self.get_argument("userId", None)
        platformType = self.get_argument("platformType", None)

        options = {}
        options["uuid"] = uuid
        options["umengPushId"] = umengPushId
        options["userId"] = userId
        options["platformType"] = platformType
        result = im_get.uploadUmengPushId(options)
        print result
        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))


class FetchImContentHandler(tornado.web.RequestHandler):
    def get(self):
        jpushId = self.get_argument("jpushId", None)
        userId = self.get_argument("userId", None)
        platformType = self.get_argument("platformType", None)

        options = {}
        options["jpushId"] = jpushId
        options["userId"] = userId
        options["platformType"] = platformType
        result = im_get.imContentFetch(options)
        print result
        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))


class FetchImListHandler(tornado.web.RequestHandler):
    def get(self):
        jpushId = self.get_argument("jpushId", None)

        options = {}
        options["jpushId"] = jpushId
        result = im_get.imListFetch(options)
        print result
        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))


class FetchChannel(tornado.web.RequestHandler):
    def get(self):
        channelId = self.get_argument("channelId", None)
        page = self.get_argument("page", 1)
        limit = self.get_argument("limit", 50)
        result = channel_get.fetch_channel(int(channelId), int(page), int(limit))
        print result
        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))


class FetchChannelListHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        result = yield im_get.searchChannelList()
        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))


class StartPageHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        result = yield start_page_post.getStartPageContent()
        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))


class FetchElementaryHandler(tornado.web.RequestHandler):
    def post(self):
        result = elementary_post.getElementary()
        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))


class PraiseHandler(tornado.web.RequestHandler):
    def post(self):
        args = self.request.arguments
        if len(args) < 6:
            result = {'response': 201, 'msg': 'Hey Dude ->'}
        else:

            result = praise_post.AddPraise(args['userId'][0], args['platformType'][0], args['uuid'][0],
                                           args['sourceUrl'][0], args['commentId'][0], args['deviceType'][0])
        print result

        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))


class FetchTagsHandler(tornado.web.RequestHandler):
    def get(self):
        # updateTime = self.get_argument("updateTime", None)
        userId = self.get_argument("userId", None)
        token = self.get_argument("token", None)
        platformType = self.get_argument("platformType", None)

        options = {}
        options["userId"] = userId
        options["token"] = token
        options["platformType"] = platformType

        result = tags_get.TagsFetch(options)
        print result
        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))


# Weiliang Guo start
class GistHandler(tornado.web.RequestHandler):
    def post(self):
        article = str(self.get_argument("article"))
        gist_obj = Gist()
        gist = gist_obj.get_gist(article)
        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(gist))


# Weiliang Guo end

# api for caimaotiyu
class caimaotiyuHandler(tornado.web.RequestHandler):
    def get(self):
        docs = conn.news_ver2.caimaotiyu.find()
        result = []
        for doc in docs:
            result.append(doc)
        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/news/baijia/fetchTime", FetchTimeHandler),
            (r"/news/baijia/fetchHome", FetchHomeHandler),
            (r"/news/baijia/newsFetchHome", NewsFetchHomeHandler),
            (r"/news/baijia/fetchContent", FetchContentHandler),
            (r"/news/baijia/newsFetchContent", NewsFetchContentHandler),
            (r"/news/baijia/newsFetchContentList", NewsFetchContentListHandler),
            (r"/news/baijia/loadMoreFetchContent", LoadMoreNewsContentHandler),
            (r"/news/baijia/dredgeUpStatus", FetchDredgeUpStatusHandler),
            (r"/news/baijia/dredgeUpStatusforiOS", FetchDredgeUpStatusforiOSHandler),
            (r"/news/baijia/startPage", StartPageHandler),
            (r"/news/baijia/createAlbum", CreateAlbumHandler),
            (r"/news/baijia/createAlbumList", CreateAlbumListHandler),
            (r"/news/baijia/updateAlbum", UpdateAlbumHandler),
            (r"/news/baijia/removeAlbum", RemoveAlbumHandler),
            (r"/news/baijia/fetchAlbumList", FetchAlbumListHandler),
            (r"/news/baijia/fetchElementary", FetchElementaryHandler),
            (r"/news/baijia/fetchLogin", FetchLoginHandler),
            (r"/news/baijia/fetchIm", FetchImHandler),
            (r"/news/baijia/point", PointHandler),
            (r"/news/baijia/fetchImUser", FetchImUserHandler),
            (r"/news/baijia/fetchImList", FetchImListHandler),
            (r"/news/baijia/fetchChannel", FetchChannel),
            (r"/news/baijia/fetchImContent", FetchImContentHandler),
            (r"/news/baijia/FetchChannelList", FetchChannelListHandler),
            (r"/news/baijia/praise", PraiseHandler),
            (r"/news/baijia/fetchTags", FetchTagsHandler),
            (r"/news/baijia/uploadUmengPushId", uploadUmengPushId),
            (r"/news/baijia/fetchGist", GistHandler),
            (r"/news/baijia/search", SearchHandler),
            (r"/news/baijia/caimaotiyu", caimaotiyuHandler),
            (r"/news/baijia/recommend", recommendHandler),
            (r"/news/baijia/fetchDetail", fetchDetailHandler)

        ]

        settings = {

        }

        tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == "__main__":
    # sched = SchedulerAll()
    # sched.start()
    port = sys.argv[1]
    # port = 9999
    tornado.options.parse_command_line()
    # sockets = tornado.netutil.bind_sockets(options.port)
    # tornado.process.fork_processes(0)
    # server = tornado.httpserver.HTTPServer(Application())
    # server.add_sockets(sockets)
    # tornado.ioloop.IOLoop.instance().start()

    # app = Application()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(port)
    tornado.ioloop.IOLoop.instance().start()
