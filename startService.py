#!/usr/bin/python
#-*- coding: utf-8 -*-


__author__ = 'jianghao'


import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.httpclient

import tornado.netutil
import json
from controller import home_get, content_get

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
        options = {}

        options["page"] = int(page)
        options["limit"] = int(limit)
        if timing:
            options["timing"] = timing

        # if updateTime:
            # options["updateTime"] = updateTime
        result = home_get.homeContentFetch(options)

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


class Application(tornado.web.Application):

    def __init__(self):

        handlers = [

            (r"/news/baijia/fetchHome", FetchHomeHandler),
            (r"/news/baijia/fetchContent", FetchContentHandler)

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
