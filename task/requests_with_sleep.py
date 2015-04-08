__author__ = 'jianghao'

import requests as r
import time
def get(url):
    time.sleep(3)
    return r.get(url, timeout=30)

if __name__ == '__main__':

    r = get("http://www.baidu.com")

    print ">>>", r