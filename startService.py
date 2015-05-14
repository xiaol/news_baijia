#!/usr/bin/python
#-*- coding: utf-8 -*-


__author__ = 'jianghao'


import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.httpclient

import tornado.netutil
import json
from controller import home_get, content_get, time_get, login_get, im_get

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
        timefeedback=self.get_argument("timefeedback",None)
        date = self.get_argument("date",None)
        type = self.get_argument("type",None)


        options = {}

        options["page"] = int(page)
        options["limit"] = int(limit)


        if timing:
            options["timing"] = timing
        if timefeedback:
            options["timefeedback"]=timefeedback

        if date:
            options["date"] = date
        if type:
            options["type"] = type


        # if updateTime:
            # options["updateTime"] = updateTime
        result = home_get.homeContentFetch(options)

        print result

        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))


class FetchTimeHandler(tornado.web.RequestHandler):

    def get(self):
        timefeedback=self.get_argument("timefeedback",None)
        options = {}
        if timefeedback:
            options["timefeedback"]=timefeedback
        result = time_get.timeContentFetch(options)

        print result

        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))





class FetchContentHandler(tornado.web.RequestHandler):

    def get(self):

        self.set_header("Content-Type", "Application/json")
        url = self.get_argument("url", None)
        filter_urls = self.get_arguments("filterurls", None)

        result = {}

        if not url:
            result["rc"] = 404
            result["msg"] = "need url"
            self.write(json.dumps(result))
            return

        result = content_get.fetchContent(url, filter_urls)

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
        expiresIn = self.get_argument("expiresIn", None)
        expiresTime = self.get_argument("expiresTime", None)
        platformType = self.get_argument("platformType", None)

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

        result = login_get.loginContentFetch(options)
        print result
        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))


class FetchImHandler(tornado.web.RequestHandler):
    def get(self):
        # updateTime = self.get_argument("updateTime", None)
        userId = self.get_argument("userId", None)
        commType = self.get_argument("commType", None)
        message = self.get_argument("message", None)

        options = {}
        options["userId"] = userId
        options["commType"] = commType
        options["message"] = message

        result = im_get.imContentFetch(options)
        print result

class PointHandler(tornado.web.RequestHandler):

    def get(self):
        result = {}
        print result

        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))

    def post(self):
        result = {}
        print result


        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))





class Application(tornado.web.Application):

    def __init__(self):

        handlers = [
            (r"/news/baijia/fetchTime", FetchTimeHandler),
            (r"/news/baijia/fetchHome", FetchHomeHandler),
            (r"/news/baijia/fetchContent", FetchContentHandler),
            (r"/news/baijia/fetchLogin", FetchLoginHandler),
            (r"/news/baijia/fetchIm", FetchImHandler),
            (r"/news/baijia/point", PointHandler)




        ]

        settings = {

        }

        tornado.web.Application.__init__(self, handlers, **settings)



if __name__ == "__main__":


    # sched = SchedulerAll()
    # sched.start()
  
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
