#!/bin/bash

source /root/text_news_spiders/venv/bin/activate

url=$1
topic=$2

echo $url  $topic

cd /Users/jianghao/PycharmProjects/scrapy_news/news_spiders

scrapy crawl news.baidu.com -a url=${url} -a topic=${topic}







