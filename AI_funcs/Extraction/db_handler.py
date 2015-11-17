# -*- coding:utf8 -*-
__author__ = 'Weiliang Guo'

import sys
reload(sys)
sys.setdefaultencoding('utf8')
from controller.config import dbConn
import re
import pymongo
import uniout

class Mongodb:
    def __init__(self):
        self.conn = pymongo.MongoClient('h213', 27017)

    def retrieve_channel_items(self):
        db = self.conn['news_ver2']
        cursor_obj = db.ChannelItems.find()
        channels = []
        for c in cursor_obj:
            channels.append(c['channel_des'])
        print(channels)

    def retrieve_news_items(self):
        db = self.conn['news_ver2']
        cursor_obj = db.NewsItems.find().skip(1).limit(3000)
        texts = []
        for cuo in cursor_obj:
            try:
                content = cuo['content']
                channel = cuo['channel']
                obj_id = cuo['_id']
                # print(content)
                # print('***************************************************************')
                # print(channel)
                text = []
                for cu in content:
                    # print('------------------------------------------------------------')
                    for k, v in cu.iteritems():
                        for kk, vv in v.iteritems():
                            if kk == 'txt':
                                text.append(vv)
                                # print(vv)
                text = ''.join(text)
                if text:
                    # print('text True')
                    text = (channel, text)
                    texts.append(text)
                    # print(text)
                    # print('***************************************************************')
                else:
                    continue
            except:
                continue
        print('all texts')
        print(len(texts))
        print(type(texts))
        # print(texts)
        # texts is a list of dictionaries which are 'channel: text' pairs.
        return texts

if __name__ == '__main__':
    mg = Mongodb()
    mg.retrieve_channel_items()
    print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
    mg.retrieve_news_items()