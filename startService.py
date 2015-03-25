#!/usr/bin/python
#-*- coding: utf-8 -*-


__author__ = 'jianghao'


import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.httpclient

import tornado.netutil
import json
from controller import home_get
from apscheduler.schedulers.tornado import TornadoScheduler
from task import weibo_run



from tornado.options import define, options
define("port", default=9999, help="run on the given port", type=int)
define("host", default="127.0.0.1", help="run on the given host", type=str)



class FetchHomeHandler(tornado.web.RequestHandler):
    def get(self):

        updateTime = self.get_argument("updateTime", None)
        options = {}
        if updateTime:
            options["updateTime"] = updateTime
        result = home_get.homeContentFetch(options)

        print result

        self.set_header("Content-Type", "Application/json")
        self.write(json.dumps(result))

class Application(tornado.web.Application):

    def __init__(self):

        handlers = [

            (r"/news/baijia/fetchHome", FetchHomeHandler),

        ]

        settings = {

        }

        tornado.web.Application.__init__(self, handlers, **settings)


# def SchedulerAll():
#     from apscheduler.triggers.cron import CronTrigger
#     trigger_c = CronTrigger(second='00', minute='00/30', hour='*')
#
#     #weibo
#     scheduler = TornadoScheduler()
#     scheduler.add_job(weibo_run.weiboTaskRun, trigger_c)
#
#     # weibo_run.weiboTaskRun()
#
#     return scheduler


if __name__ == "__main__":


    # sched = SchedulerAll()
    # sched.start()

    tornado.options.parse_command_line()
    sockets = tornado.netutil.bind_sockets(options.port)
    tornado.process.fork_processes(0)
    server = tornado.httpserver.HTTPServer(Application())
    server.add_sockets(sockets)
    tornado.ioloop.IOLoop.instance().start()
