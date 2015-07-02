#!/usr/bin/python
# -*- coding: utf-8 -*-


__author__ = 'jianghao'

import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.httpclient

import tornado.netutil
import json
from controller import home_get, content_get, time_get, login_get, im_get, point_post, channel_get, point_get, \
    praise_post
from controller.push import push_message

import abstract

from tornado.options import define, options

define("port", default=9999, help="run on the given port", type=int)
define("host", default="127.0.0.1", help="run on the given host", type=str)


class FetchHomeHandler(tornado.web.RequestHandler):
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
        result = home_get.homeContentFetch(options)

        print result

        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))


class NewsFetchHomeHandler(tornado.web.RequestHandler):
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
        result = home_get.newsHomeContentFetch(options)
        print result

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
    def get(self):
        self.set_header("Content-Type", "Application/json")
        url = self.get_argument("url", None)
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

        result = content_get.fetchContent(url, filter_urls, userId, platformType)

        self.write(json.dumps(result))


class NewsFetchContentHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header("Content-Type", "Application/json")
        url = self.get_argument("url", None)
        filter_urls = self.get_arguments("filterurls")
        uuid = self.get_argument("uuid", None)
        result = {}
        if not url:
            result["rc"] = 404
            result["msg"] = "need url"
            self.write(json.dumps(result))
            return

        result = content_get.newsFetchContent(url, filter_urls, uuid)

        self.write(json.dumps(result))
    def post(self):
        args = self.request.arguments
        filter_urls = self.get_arguments("filterurls")
        uuid = self.get_argument("uuid", None)
        if len(args) < 1:
            result = {'response': 201, 'msg': 'Hey Dude ->'}
        else:
            result =content_get.newsFetchContent(args['url'][0],filter_urls, uuid)

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
    def get(self):
        result = im_get.searchChannelList()
        print result
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


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/news/baijia/fetchTime", FetchTimeHandler),
            (r"/news/baijia/fetchHome", FetchHomeHandler),
            (r"/news/baijia/newsFetchHome", NewsFetchHomeHandler),
            (r"/news/baijia/fetchContent", FetchContentHandler),
            (r"/news/baijia/newsFetchContent", NewsFetchContentHandler),
            (r"/news/baijia/fetchLogin", FetchLoginHandler),
            (r"/news/baijia/fetchIm", FetchImHandler),
            (r"/news/baijia/point", PointHandler),
            (r"/news/baijia/fetchImUser", FetchImUserHandler),
            (r"/news/baijia/fetchImList", FetchImListHandler),
            (r"/news/baijia/fetchChannel", FetchChannel),
            (r"/news/baijia/fetchImContent", FetchImContentHandler),
            (r"/news/baijia/FetchChannelList", FetchChannelListHandler),
            (r"/news/baijia/praise", PraiseHandler)

        ]

        settings = {

        }

        tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == "__main__":
    # sched = SchedulerAll()
    # sched.start()

    tornado.options.parse_command_line()
    tornado.options.parse_command_line()
    # sockets = tornado.netutil.bind_sockets(options.port)
    # tornado.process.fork_processes(0)
    # server = tornado.httpserver.HTTPServer(Application())
    # server.add_sockets(sockets)
    # tornado.ioloop.IOLoop.instance().start()

    # app = Application()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
