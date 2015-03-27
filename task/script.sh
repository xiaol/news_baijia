#!/bin/bash

keyword=$1
response_url=$2

cd /Users/jianghao/PycharmProjects/scrapy_news/news_spiders

scrapy crawl zhihu -a keyword=${keyword} -a response_url=${response_url}







