# -*- coding: utf-8 -*-
from __future__ import print_function
__author__ = 'Weiliang Guo'
import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.httpclient
import sys
import tornado.netutil
import json
from tornado.options import define, options
import tornado.gen
import tornado.concurrent
from AI_funcs.Gist_and_Sim.gist_test import Gist

# define("port", default=9999, help="run on the given port", type=int)
define("port", default="8000", help="run on the given host", type=int)


class GistHandler(tornado.web.RequestHandler):
    def post(self):
        article = str(self.get_argument("article"))
        gist_obj = Gist()
        gist = gist_obj.get_gist(article)
        self.write(gist)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/news/baijia/fetchGist", GistHandler),
        ]
        tornado.web.Application.__init__(self, handlers)

if __name__ == "__main__":
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()