#coding=utf-8

from config import dbConn
from weibo import weibo_relate_docs_get, user_info_get
import json
import datetime,time
import operator
from home_get import get_start_end_time,get_time_type_date_freq

DBStore = dbConn.GetDateStore()

def timeContentFetch(options):


    if 'timefeedback' in options.keys():
        timefeedback=options['timefeedback']
    else:
        timefeedback = None

    conn = DBStore._connect_news
    timefeedback_dict = {}

    if not timefeedback:

        return timefeedback_dict

    else:
        # start_time, end_time = get_start_end_time()
        start_time, end_time, update_time, update_type, upate_frequency = get_start_end_time(halfday=True)

    if timefeedback:
        request_time, next_update_time, next_update_type\
            , history_date, next_update_freq = get_time_type_date_freq(update_time, update_type, upate_frequency)

        timefeedback_dict = {}
        timefeedback_dict['request_time'] = request_time
        timefeedback_dict['next_update_time'] = next_update_time
        timefeedback_dict['next_update_type'] = next_update_type
        timefeedback_dict['history_date'] = history_date
        timefeedback_dict['next_update_freq'] = next_update_freq

        return timefeedback_dict
