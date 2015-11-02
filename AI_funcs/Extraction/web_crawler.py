# -*- coding:utf8 -*-
__author__ = 'Weiliang Guo'
import uniout
from urllib2 import urlopen
from urllib import urlencode
from urllib2 import HTTPError
from bs4 import BeautifulSoup
import re
import simplejson as json
from page import get_page
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import pymongo
from bson.objectid import ObjectId

class BaiduBaijiaZhengming:

    def __init__(self):
        pass

    def get_topic_urls(self):
        url_domain = "http://baijia.baidu.com/ajax/topiclist?"
        topic_url_domain = "http://baijia.baidu.com/?"
        page = 1
        topic_urls = []
        while True:
            print('*******params*******')
            params = urlencode({"firstid": "xf73b7pF", "pagesize": "6", "page": page})
            print('*******url*******')
            url = url_domain + params
            # html = urlopen(url, timeout=5)
            html = get_page(url)
            json_html = json.loads(html)
            jlis = json_html.get("data").get("list")
            if jlis:
                for li in jlis:
                    for kk, vv in li.iteritems():
                        if kk == 'ID':
                            topic_url_params = urlencode({"tn": "topic", "topicid": vv})
                            topic_url = topic_url_domain + topic_url_params
                            # print(topic_url)
                            topic_urls.append(topic_url)
                # print(page)
                page += 1

            else:
                break
        return topic_urls
    #bs_obj is BeautifulSoup object
    def get_title(self, bs_obj):
        #get title
        topic_title_raw = bs_obj.title.get_text()
        topic_title_raw = topic_title_raw.encode('utf-8')
        topic_title = topic_title_raw.replace("--百度百家", "")
        return topic_title

    def create_bs_obj(self, url='http://baijia.baidu.com/?tn=topic&topicid=hc20ad4F'):
        # html = urlopen(url, timeout=5)
        html = get_page(url)
        try:
            bs_obj = BeautifulSoup(html)
        except HTTPError as e:
            return None
        return bs_obj

    def get_special_content(self, topic_url='http://baijia.baidu.com/?tn=topic&topicid=hc20ad4F'):
        bs_obj = self.create_bs_obj(topic_url)

        #get special title
        special_title = self.get_title(bs_obj)

        #get support label
        sl = bs_obj.find('div', {'class': 'support'}).get_text()

        #get oppose label
        ol = bs_obj.find('div', {'class': 'oppose'}).get_text()

        result = {}

        #support article urls
        support_article_urls = set()
        raw_suppurls = bs_obj.find("ul", {"id": "article1"}).findAll("a", href=re.compile("/article/"))
        for rs in raw_suppurls:
            if 'href' in rs.attrs:
                href = rs.attrs['href']
                support_article_urls.add(href)
        support_article_urls = list(support_article_urls)

        #oppose article urls
        oppose_article_urls = set()
        raw_oppurls = bs_obj.find("ul", {"id": "article2"}).findAll("a", href=re.compile("/article/"))
        for ro in raw_oppurls:
            if 'href' in ro.attrs:
                href = ro.attrs['href']
                oppose_article_urls.add(href)
        oppose_article_urls = list(oppose_article_urls)
        result['special title'] = special_title
        result['support label'] = sl
        result['support_article_urls'] = support_article_urls
        result['oppose label'] = ol
        result['oppose_article_urls'] = oppose_article_urls
        return result

    def get_article(self, article_url='http://zhuyi.baijia.baidu.com/article/2403'):
        bs_obj = self.create_bs_obj(article_url)
        #get article title
        article_title = self.get_title(bs_obj)
        # print(article_title)
        text_raw = bs_obj.find_all("div", {"class": "article-detail"})
        # print(type(text_raw))
        text = ''
        for tr in text_raw:
            # print('----------')
            text = ''.join(tr.findAll(text=True)).strip()
        if text:
            article_url = article_url.replace('.', '_')
            article = {'article_title': article_title, 'text': text, 'article_url': article_url}
        else:
            print('var text is empty')
            print(article_url)
            # article_url = article_url.replace('.', '_')
            article = {'article_title': article_title, 'text': text, 'article_url': article_url}

        return article

    def generate_final_result(self):
        special_urls = self.get_topic_urls()

        #store final specials
        specials = []
        special_count = 0
        for su in special_urls:
            try:
                sc = self.get_special_content(su)
            except:
                continue

            if sc:
                if sc['special title'] and sc['support_article_urls'] and sc['oppose_article_urls']\
                        and sc['support label'] and sc['oppose label']:

                    #store support articles with urls, titles  and support labels
                    saud = {'support label': sc['support label']}
                    support_articles = []
                    for sau in sc['support_article_urls']:
                        try:
                            sat = self.get_article(sau)
                        except:
                            continue
                        support_articles.append(sat)
                    saud['support articles'] = support_articles
                    # print(saud)

                    #store oppose articles with urls, titles  and oppose labels
                    oaud = {'oppose label': sc['oppose label']}
                    oppose_articles = []
                    for oau in sc['oppose_article_urls']:
                        try:
                            oat = self.get_article(oau)
                        except:
                            continue
                        oppose_articles.append(oat)
                    oaud['oppose articles'] = oppose_articles
                    # print(oaud)
                    special = {'special title': sc['special title'], 'support': saud, 'oppose': oaud, 'special url': su}
                    print('*******special*******')
                    # print(special)

                    special_count += 1
                    print(special_count)
                    specials.append(special)
        # print(specials)
        print('specials')
        return specials


class Mongodb:
    def __init__(self):
        conn = pymongo.MongoClient('h213', 27017)
        self.db = conn['AI_funcs']

    def generate_zhengming(self):
        zhengming = BaiduBaijiaZhengming()
        #get db 'AI_funcs'
        docs = zhengming.generate_final_result()
        for doc in docs:
            doc_inserted = self.db.baidu_baijia_zhengming.insert_one(doc)
            doc_id = doc_inserted.inserted_id
            print(doc_id)

    def retrieve_zhengming(self):
        cursor_obj = self.db.baidu_baijia_zhengming.find()
        neg = open("negative.txt", "w+r")
        pos = open("positive.txt", "w+r")
        for c in cursor_obj:
            oli = c['oppose']['oppose articles']
            for o in oli:
                oat = o['article_title']
                if oat not in neg:
                    neg.write(oat + '\n')
                    print(oat)
            sli = c['support']['support articles']
            for s in sli:
                sat = s['article_title']
                if sat not in pos:
                    pos.write(sat + '\n')
                    print(sat)


if __name__ == '__main__':
    mb = Mongodb()
    mb.retrieve_zhengming()


