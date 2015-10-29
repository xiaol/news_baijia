__author__ = 'jianghao'

import pymongo
from pymongo.read_preferences import ReadPreference

try:
    from controller.config.getConfig import getcfg
except:
    from config.getConfig import getcfg

class GetDateStore(object):
    def __init__(self):

        if not hasattr(GetDateStore, "db_news"):
            GetDateStore.create_news()
        self._connect_news = GetDateStore.db_news



    @staticmethod
    def create_news():

        db_replset = getcfg("db-replset", "hosts_ports")
        set_name = getcfg("db-replset", "set_name")
        GetDateStore.db_news = pymongo.MongoReplicaSetClient(db_replset, replicaSet=set_name,
                                                             read_preference=ReadPreference.SECONDARY)

    def get_news_db(self):
        return self._connect_news
