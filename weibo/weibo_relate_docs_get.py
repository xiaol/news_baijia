#coding=utf-8
# import urllib
import requests
import json
import time
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
def search_relate_docs(topic, page):

    time.sleep(10)
    print topic

    api_url = "http://14.17.120.252:9091/getInfoByText"

    param = {"text": topic, "page": str(page)}
    r = requests.post(api_url, data=json.dumps(param))

    return r.text



if __name__ == '__main__':
    print search_relate_docs("柴静","1")

