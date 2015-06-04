# -*- coding: utf-8 -*-
"""
    Project: news_baijia
    Purpose: Get the weibo comments by url.
    Version: N/A
    Author:  ZG
    Date:    15/6/2
"""

import re
import json
import time
import pymongo
import requests
from collections import defaultdict
from pymongo.read_preferences import ReadPreference


class Comments(object):

    def __init__(self, url):
        self.url = url
        self.api = 'http://m.weibo.cn/single/rcList?format=cards' \
                   '&id=ReplaceId&type=comment&hot=1&page=1'

    @staticmethod
    def check_url(url):
        """
        The weibo url must be seems like 'http://m.weibo.cn/11223232/ASD334aS',
        The last block 'ASD334aS' is we need.
        :param url: weibo url
        :return: weibo id encode by code62
        """
        if not url or not url.startswith('http://m.weibo.cn/'):
            return None
        url = url.split('/')[-1]
        if not url:
            return None
        url = url.replace('?', '').strip()
        return url

    @staticmethod
    def req(url):
        """
        :param url: weibo comments api within weibo id
        :return: weibo comments dumps by json
        """
        timeout = 30
        try:
            r = requests.get(url, timeout=timeout)
            if r.status_code == 200:
                return r.text
        except IOError:
            return None

    @classmethod
    def format_dates(cls, dates):
        """
        :param dates: origin date get from weibo comment
        :return: formated date seems like 'YYYY-MM-DD HH:MM:SS'
        """
        # 2秒钟前
        if u'\u79d2\u949f\u524d' in dates:
            rel = int(dates.replace(u'\u79d2\u949f\u524d', '').strip())
            return cls.reletime(rel)
        # 2分钟前
        if u'\u5206\u949f\u524d' in dates:
            rel = int(dates.replace(u'\u5206\u949f\u524d', '').strip()) * 60
            return cls.reletime(rel)
        # 今天 12:30
        if u'\u4eca\u5929' in dates:
            t = dates.replace(u'\u4eca\u5929', '').strip() + ':00'
            d = time.strftime("%Y-%m-%d", time.localtime())
            return ' '.join([d, t])
        # 6月1日18:39
        if u'\u6708' in dates and u'\u65e5' in dates:
            year = str(time.localtime()[0])
            month = dates.split(u'\u6708')[0]
            month = ''.join(['0', month]) if int(month) < 10 else month
            day = dates.split(u'\u6708')[-1].split(u'\u65e5')[0]
            day = ''.join(['0', day]) if int(day) < 10 else day
            t = dates.split(u'\u65e5')[-1] + ':00'
            return ' '.join(['-'.join([year, month, day]), t])
        # 06-02 14:39
        if dates.count(':') == 1 and dates.count('-') == 1:
            dates = ''.join([str(time.localtime()[0]), '-', dates, ':00'])
            return dates

    @staticmethod
    def reletime(rel):
        return time.strftime("%Y-%m-%d %X", time.localtime(time.time() - rel))

    @staticmethod
    def format_message(message):
        """
        clean the message with <i ...>,<a ...>..
        :param message: comment message
        :return: cleaned comment message
        """
        re_i = re.compile('<[\s\S]+?>', re.I)
        message = re_i.sub('', message)
        return message

    @classmethod
    def format_comments(cls, comments, comment_id):
        """
        :param comments: comments get from weibo API
        :return: formated comments as same as the data struct in mongodb["news_ver2"]["commentItems"]._"comments":
        """
        comments_result = []
        for comment in comments:
            cm = defaultdict(dict)
            cm['1'] = defaultdict(str)
            created_at = comment.get('created_at')
            cm['1']['created_at'] = cls.format_dates(created_at) if created_at else None
            cm['1']['up'] = str(comment.get('like_counts'))
            user = comment.get('user')
            cm['1']['author_name'] = user.get('screen_name') if user else None

            # just for weibo
            cm['1']['type'] = 'weibo'
            author_id = user.get('id') if user else None
            cm['1']['author_id'] = str(author_id) if author_id else None
            cm['1']['author_img_url'] = user.get('profile_image_url') if user else None
            cm['1']['weibo_id'] = comment_id

            cm['1']['down'] = '0'
            cm['1']['post_id'] = '1'
            message = comment.get('text')
            cm['1']['message'] = cls.format_message(message) if message else None
            if cm['1']['author_name'] and cm['1']['message']:
                cm['1'] = dict(cm['1'])
                comments_result.append(dict(cm))
        return comments_result

    def get_comments_by_weibo_url(self):
        url = self.check_url(self.url)
        if not url:
            return None
        comment_id = convert_url_to_id(url)
        comment_url = self.api.replace('ReplaceId', comment_id)
        # print comment_url
        comments = self.req(comment_url)
        try:
            comments = json.loads(comments)
            comments = [c['card_group'] for c in comments if c.get('card_group')]
            comments = comments[0]
            comments = self.format_comments(comments, comment_id)
            return comments
        except TypeError:
            return None
        except IndexError:
            return None


def convert_url_to_id(url):
    """
    Convert the url to id, the url is encode by code62.
    :param url:
    :return: id(str)
    """
    url = str(url)[::-1]
    size = len(url) / 4 if len(url) % 4 == 0 else len(url) / 4 + 1
    result = []
    for i in range(size):
        s = url[i * 4: (i + 1) * 4][::-1]
        s = str(base62_decode(str(s)))
        s_len = len(s)
        if i < size - 1 and s_len < 7:
            s = (7 - s_len) * '0' + s
        result.append(s)
    result.reverse()
    return ''.join(result)


ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def base62_decode(string, alphabet=ALPHABET):
    """
    Convert Str of code62 to code10.
    :param string:
    :param alphabet:
    :return:
    """
    base = len(alphabet)
    strlen = len(string)
    num = 0

    idx = 0
    for char in string:
        power = (strlen - (idx + 1))
        num += alphabet.index(char) * (base ** power)
        idx += 1

    return num


def update_mongo_by_releturl(relateUrl, comments):
    try:
        conn = pymongo.MongoReplicaSetClient("121.41.49.44:27017, 121.41.75.213:27017, 121.41.112.241:27017",
                                             replicaSet="myset", read_preference=ReadPreference.SECONDARY)

        news = conn["news_ver2"]["commentItems"]
        comment = news.find_one({"relateUrl": relateUrl})
        # print 'comment: ', comment
        if comment:
            old_comments = comment.get('comments')
            if not old_comments:
                # news.update({"relateUrl": relateUrl}, {"$set": {"comments": comments}})
                # print 'No old comments'
                comment['comments'] = comments
            if old_comments:
                # print 'old comments', type(old_comments)
                # new_comments = old_comments + comments
                # news.update({"relateUrl": relateUrl}, {"$set": {"comments": new_comments}})
                comment['comments'] = comments + old_comments
            news.save(comment)
        print 'Update comments success.'
    except Exception, e:
        print 'Update comments of %s faield with err: %s' % (relateUrl, e)


def get_comments_by_weibo_url(relate_url, weibo_url):
    """
    Process only one url of weibo
    :param relate_url: url of news
    :param weibo_url: url of weibo
    :return: update the mongo by relateUrl with comments
    """
    com = Comments(weibo_url)
    comments = com.get_comments_by_weibo_url()
    if comments:
        update_mongo_by_releturl(relate_url, comments)


def get_comments_by_weibo_ready(relate_url, weibo_ready):
    """
    :param relate_url:  url of news
    :param weibo_ready: a list of weibo[dict]
    :return: update the mongo by relateUrl with comments
    """
    if not weibo_ready or not isinstance(weibo_ready, list):
        return
    comments_result = []
    for weibo in weibo_ready:
        weibo_url = weibo.get('url')
        if not weibo_url:
            continue
        # print weibo_url
        com = Comments(weibo_url)
        comments = com.get_comments_by_weibo_url()
        if comments:
            # print comments
            comments_result += comments

    if comments_result:
        update_mongo_by_releturl(relate_url, comments_result)
    else:
        print 'No comments get.'
    print 'weibo comments proess sucess.'


if __name__ == '__main__':
    # Usage
    relateUrl = 'http://finance.sina.com.cn/roll/20150602/230722330541.shtml'
    weibo_ready = [{'reposts_count': 378, 'sourceSitename': 'weibo',
                    'img': u'http://ww2.sinaimg.cn/thumb180/4694a95djw1esbws5fqjij2179169jxf.jpg', 'title': u'\u300a\u516b\u5343\u91cc\u8def\u300b\u662f\u6211\u7ee7\u300a\u90a3\u7b11\u5bb9\u662f\u590f\u5929\u7684\u300b\u4e4b\u540e\u5b8c\u6210\u7684\u97f3\u4e50\u6e38\u8bb0\u3002\u5341\u4e94\u8fb9\u57ce\u5c18\u4e0e\u571f\uff0c\u516b\u5343\u91cc\u8def\u4e91\u548c\u98ce\u3002\u65c5\u7a0b\u6d93\u6ef4\u7ec6\u4e8b\uff0c\u4e0d\u5fcd\u5fd8\u5374\uff0c\u4e00\u8def\u5207\u9aa8\u8bb0\u5fc6\uff0c\u600e\u80fd\u8f9c\u8d1f\uff01 \u4e16\u754c\u90a3\u4e48\u5927\uff0c\u968f\u6211\u8db3\u8ff9\uff0c\u8d70\u4e00\u6b21\u7edd\u65e0\u4ec5\u6709\u7684\u65c5\u7a0b\u3002\u4eac\u4e1c\uff1a\u7f51\u9875\u94fe\u63a5\u5f53\u5f53\uff1a\u7f51\u9875\u94fe\u63a5 \u4e9a\u9a6c\u900a\uff1a\u7f51\u9875\u94fe\u63a5 \u81e7\u5929\u6714\u52a9\u9635\u90ed\u5fd7\u51ef\u65b0\u4e66\u53d1\u5e03\u4f1a \u76db\u8d5e\u5e74\u8f7b\u4eba\u8ffd\u6c42\u68a6\u60f3\u7684\u6fc0\u60c5 150520', 'url': u'http://m.weibo.cn/1641537045/CiREBwSmr?', 'profileImageUrl': u'http://tp2.sinaimg.cn/1184147805/180/5665291864/1', 'like_count': 34, 'comments_count': 152, 'user': u'\u90ed\u5fd7\u51ef', 'imgs': [u'http://ww2.sinaimg.cn/thumb180/4694a95djw1esbws5fqjij2179169jxf.jpg', u'http://ww3.sinaimg.cn/thumb180/4694a95djw1esbws8msidj21e00xcn69.jpg', u'http://ww4.sinaimg.cn/thumb180/4694a95djw1esbwscds9lj21e00xcakr.jpg', u'http://ww1.sinaimg.cn/thumb180/4694a95djw1esbwsem7hyj20zk0q20wn.jpg', u'http://ww3.sinaimg.cn/thumb180/4694a95djw1esbwtqojqfj20zk0no77e.jpg', u'http://ww4.sinaimg.cn/thumb180/4694a95djw1esbwsitjzlj21kw11x494.jpg', u'http://ww1.sinaimg.cn/thumb180/4694a95djw1esbwsmub4oj20yv1e0jxx.jpg', u'http://ww3.sinaimg.cn/thumb180/4694a95djw1esbwsvo5qmj20ku2bc4ie.jpg', u'http://ww2.sinaimg.cn/thumb180/4694a95djw1esbwto7ljej217r8n3kjn.jpg']}, {'reposts_count': 519, 'sourceSitename': 'weibo', 'img': u'http://ww2.sinaimg.cn/wap180/63987180jw1espshxjqnvj21i5254n7i.jpg', 'title': u'\u3010\u91cd\u78c5\u65b0\u4e66\u3011\u5728\u53d8\u6001\u8005\u770b\u6765\uff0c\u6740\u622e\u5c31\u662f\u4e00\u79cd\u62ef\u6551\uff01@\u5341\u5b97\u7f6a\u8718\u86db \u6700\u65b0\u4f5c\u54c1\u300a#\u5341\u5b97\u7f6a5#\u300b\u60ca\u609a\u6765\u88ad\uff01\u516c\u5b89\u5385\u7edd\u5bc6\u6863\u6848\u5168\u9762\u66dd\u5149\u3002\u5f53\u5f53\u7f51\u9875\u94fe\u63a5\u4e9a\u9a6c\u900a\u7f51\u9875\u94fe\u63a5\u4eac\u4e1c\u7f51\u9875\u94fe\u63a5\u535a\u5e93\u9884\u552e \u5341\u5b97\u7f6a5(\u4e2d\u56fd\u5341\u5927\u6050\u6016\u51f6\u6740\u6848)\u8718\u86db\u4f5c\u54c1 \u5341\u5b97\u7f6a\u7cfb\u5217 \u4e03\u5b97\u7f6a 2015\u6700\u65b0\u7bc7 \u5bf9\u4e8e\u53d8\u6001\u8005\u6765\u8bf4\uff0c\u6740\u622e\u662f\u4e00\u79cd\u62ef\u6551\uff01 \u535a\u5e93\u7f51\u6587\u8f69\u9884\u552e \u5341\u5b97\u7f6a5\uff1a\u4e2d\u56fd\u5341\u5927\u6050\u6016\u51f6\u6740\u6848/\u8718\u86db \u65b0\u534e\u6b63\u7248\u4e66\u7c4d \u53d1\u8d27\u65f6\u95f4\u7ea62015.6\u4e0b\u65ec', 'url': u'http://m.weibo.cn/1641537045/CkGPHzcFw?', 'profileImageUrl': u'http://tp1.sinaimg.cn/1670934912/180/5596330115/0', 'like_count': 44, 'comments_count': 34, 'user': u'\u535a\u96c6\u5929\u5377', 'imgs': [u'http://ww2.sinaimg.cn/wap180/63987180jw1espshxjqnvj21i5254n7i.jpg']}, {'reposts_count': 115, 'sourceSitename': 'weibo', 'img': u'http://ww4.sinaimg.cn/wap180/624f7f62gw1esqwpy5w91j20zk19o15a.jpg', 'title': u'#\u8bfb\u5ba2\u65b0\u4e66\u901f\u9012#\u300a\u54f2\u5b66\u5bb6\u4eec\u90fd\u5e72\u4e86\u4e9b\u4ec0\u4e48\u300b\uff0c\u8f70\u52a8\u8c46\u74e3\u7684\u5947\u8469\u4e4b\u4e66\uff0c\u8fde\u7eed\u4e09\u5e74\u8749\u8054\u8c46\u74e3\u7535\u5b50\u9605\u8bfb\u699c\u7b2c\u4e00\u7684\u795e\u4f5c\uff01\u7528\u7a77\u51f6\u6781\u6076\u7684\u5410\u69fd\u548c\u559c\u95fb\u4e50\u89c1\u7684\u516b\u5366\uff0c\u5f7b\u5e95\u74e6\u89e3\u4f60\u5bf9\u54f2\u5b66\u53f2\u7684\u6210\u89c1\uff01\u5f53\u5f53\uff1a\u7f51\u9875\u94fe\u63a5 \u4e9a\u9a6c\u900a\uff1a\u7f51\u9875\u94fe\u63a5 \u4eac\u4e1c\uff1a\u7f51\u9875\u94fe\u63a5 \u968f\u624b\u8f6c\u53d1\uff0c\u968f\u673a\u9001\u4e661\u672c\uff01', 'url': u'http://m.weibo.cn/1641537045/CkPX2xUXE?', 'profileImageUrl': u'http://tp3.sinaimg.cn/1649377122/180/40041377088/1', 'like_count': 11, 'comments_count': 36, 'user': u'\u8bfb\u5ba2\u56fe\u4e66', 'imgs': [u'http://ww4.sinaimg.cn/wap180/624f7f62gw1esqwpy5w91j20zk19o15a.jpg']}, {'reposts_count': 0, 'sourceSitename': 'weibo', 'img': '', 'title': u'IT \u4e89\u5206\u593a\u79d2 - \u4eac\u4e1c \u7f51\u9875\u94fe\u63a5', 'url': u'http://m.weibo.cn/1641537045/CkQOljESj?', 'profileImageUrl': u'http://tp1.sinaimg.cn/1736624640/180/5718493284/1', 'like_count': 0, 'comments_count': 0, 'user': u'\u6797\u53c8\u6797\u53c8\u6797', 'imgs': []}, {'reposts_count': 0, 'sourceSitename': 'weibo', 'img': '', 'title': u'#\u7231\u8033\u76ee\u667a\u80fd\u6444\u50cf\u673a#\u4eac\u4e1c618\u5927\u4fc3\u7b2c\u4e00\u6ce2\u5f3a\u52bf\u6765\u88ad\uff01[\u5a01\u6b66]\u5373\u523b\u8d77\uff0c\u4eac\u4e1c\u8d2d\u4e70\u201c\u7231\u8033\u76ee\u667a\u80fd\u6444\u50cf\u673a\u201d\u4e0b\u5355\u7acb\u51cf40\u5143\uff01[\u9177]720P\u9ad8\u6e05\u89c6\u9891&amp;\u53cc\u5411\u8bed\u97f3\u901a\u8bdd\uff0c\u8ba9\u60a8\u65f6\u523b\u966a\u4f34\u5bb6\u4eba\uff1b\u7ea2\u5916\u591c\u89c6\u529f\u80fd&amp;\u767e\u5ea6\u4e91\u5b58\u50a8\uff0c\u7ed9\u60a824\u5c0f\u65f6\u7684\u5b89\u5fc3\uff01\u7ed9\u529b\u652f\u6301~@\u80a5\u9c7c84 @Levana-ww @\u60f3\u7761\u89c9\u4e86\u65e0\u540d ', 'url': u'http://m.weibo.cn/1641537045/CkQOa7f66?', 'profileImageUrl': u'http://tp4.sinaimg.cn/2346585743/180/5643121206/0', 'like_count': 0, 'comments_count': 0, 'user': u'kun_0822', 'imgs': []}, {'reposts_count': 0, 'sourceSitename': 'weibo', 'img': '', 'title': u'teeeeeeest#\u6211\u521a\u5728\u4eac\u4e1c\u53d1\u73b0\u4e00\u4e2a\u5f88\u7ed9\u529b\u7684\u3010\u9884\u552e-\u795e\u79d8\u4ed3\u5e93 - \u4eac\u4e1c\u3011\u9080\u4f60\u4e00\u8d77\u6765\u53c2\u4e0e\u3002 \u7f51\u9875\u94fe\u63a5', 'url': u'http://m.weibo.cn/1641537045/CkQNZrO87?', 'profileImageUrl': u'http://tp4.sinaimg.cn/2669170651/180/5711779596/0', 'like_count': 0, 'comments_count': 0, 'user': u'\u5c0f\u777f\u7eb8', 'imgs': []}, {'reposts_count': 0, 'sourceSitename': 'weibo', 'img': u'http://ww1.sinaimg.cn/wap180/e5b35419jw1esr0irn93oj202s02sa9u.jpg', 'title': u'\u6211\u5728@\u4eac\u4e1c \u53d1\u73b0\u4e86\u4e00\u4e2a\u975e\u5e38\u4e0d\u9519\u7684\u5546\u54c1\uff1a \u848b\u52cb\u8bf4\u7ea2\u697c\u68a6\uff08\u4fee\u8ba2\u7248  \u5957\u88c5\u51688\u518c \u9644\u5149\u76d8\uff09\u3000\u4eac\u4e1c\u4ef7\uff1a\uffe5 237.5\u3002 \u611f\u89c9\u4e0d\u9519\uff0c\u5206\u4eab\u4e00\u4e0b\u7f51\u9875\u94fe\u63a5', 'url': u'http://m.weibo.cn/1641537045/CkQNS5wMw?', 'profileImageUrl': u'http://tp2.sinaimg.cn/3853734937/180/40062623767/0', 'like_count': 0, 'comments_count': 0, 'user': u'\u968f\u98ce\u7684\u601d\u5ff57', 'imgs': [u'http://ww1.sinaimg.cn/wap180/e5b35419jw1esr0irn93oj202s02sa9u.jpg']}, {'reposts_count': 0, 'sourceSitename': 'weibo', 'img': '', 'title': u'\u4eac\u4e1c\u652f\u4ed8\u771f\u7684\u597d\u9ebb\u70e6[\u6012][\u6012][\u6012]', 'url': u'http://m.weibo.cn/1641537045/CkQNRuwkA?', 'profileImageUrl': u'http://tp1.sinaimg.cn/1839872604/180/5724474491/0', 'like_count': 0, 'comments_count': 0, 'user': u'\u5927\u5c11\u7237\u5feb\u5230\u6211\u7897\u91cc\u6765', 'imgs': []}]
    # get_comments_by_weibo_url('relateUrl', 'the url of weibo')
    get_comments_by_weibo_ready(relateUrl, weibo_ready)
