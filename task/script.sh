#!/bin/bash

source /root/text_news_spiders/venv/bin/activate

url=$1
topic=$2

echo $url  $topic

cd /root/workspace/news_spiders

scrapy crawl www.baidu.com -a url=${url} -a topic=${topic}







