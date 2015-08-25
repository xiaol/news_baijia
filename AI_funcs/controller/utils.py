#coding=utf-8

import datetime

def get_start_end_time(oneday=False,halfday=False):

    now = datetime.datetime.now()
    yesterday = now + datetime.timedelta(days=-1)
    yesterday_year = yesterday.year
    yesterday_month = yesterday.month
    yesterday_day = yesterday.day

    today_year = now.year
    today_month = now.month
    today_day = now.day

    tomorrow = now + datetime.timedelta(days=1)
    tomorrow_year = tomorrow.year
    tomorrow_month = tomorrow.month
    tomorrow_day = tomorrow.day

    hour = now.hour
    start_time = ''
    end_time = ''

    if oneday:
        start_time = datetime.datetime(yesterday_year, yesterday_month, yesterday_day, 0, 0)
        end_time = now

        return start_time, end_time

    if halfday:


        if hour in range(0,6):    #取昨天6点-昨天18点 更新时间为今天早上6点
            start_time = datetime.datetime(yesterday_year, yesterday_month, yesterday_day, 6, 0)
            end_time = datetime.datetime(yesterday_year, yesterday_month, yesterday_day, 18, 0)
            update_time = datetime.datetime(today_year, today_month, today_day, 6, 0)
            update_type = 0  #0代表白天
            upate_frequency = int((update_time - end_time).total_seconds()*1000)


        elif hour in range(6,18): #取昨天18点~今天6点 更新时间为今天18点
            start_time = datetime.datetime(yesterday_year, yesterday_month, yesterday_day, 18, 0)
            end_time = datetime.datetime(today_year, today_month, today_day, 6, 0)
            update_time = datetime.datetime(today_year, today_month, today_day, 18, 0)
            update_type = 1 #1代表黑夜
            upate_frequency = int((update_time - end_time).total_seconds()*1000)

        elif hour in range(18,24): #取今天6-今天18点 更新时间为明天6点
            start_time = datetime.datetime(today_year, today_month, today_day, 6, 0)
            end_time = datetime.datetime(today_year, today_month, today_day, 18, 0)
            update_time = datetime.datetime(tomorrow_year, tomorrow_month, tomorrow_day, 6, 0)
            update_type = 0
            upate_frequency = int((update_time - end_time).total_seconds()*1000)


        return start_time, end_time, update_time, update_type, upate_frequency

    if hour in range(0, 8):  # 取昨天14点~~~20点
        start_time = datetime.datetime(yesterday_year, yesterday_month, yesterday_day, 14, 0)
        end_time = datetime.datetime(yesterday_year, yesterday_month, yesterday_day, 20, 0)

    elif hour in range(8, 14): #取昨天20天~~~今天8点
        start_time = datetime.datetime(yesterday_year, yesterday_month, yesterday_day, 20, 0)
        end_time = datetime.datetime(today_year, today_month, today_day, 8, 0)

    elif hour in range(14, 20): #取今天8点~~~14点
        start_time = datetime.datetime(today_year, today_month, today_day, 8, 0)
        end_time = datetime.datetime(today_year, today_month, today_day, 14, 0)

    elif hour in range(20, 24): #取今天14点~~~20点
        start_time = datetime.datetime(today_year, today_month, today_day, 14, 0)
        end_time = datetime.datetime(today_year, today_month, today_day, 20, 0)

    return start_time, end_time


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False