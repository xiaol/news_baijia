#coding=utf-8
# import urllib
import requests
import json
import time
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
def search_relate_docs(topic, page):

    # time.sleep(4)
    print topic

    # api_url = "http://14.17.120.252:9091/getInfoByText"
    api_url = "http://14.17.120.252:9091/getTextByApi"
    param = {"text": topic, "page": str(page)}
    r = requests.post(api_url, data=json.dumps(param), timeout=8)

    return r.text

if __name__ == '__main__':
    print search_relate_docs("柴静","1")

