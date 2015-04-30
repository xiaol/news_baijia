__author__ = 'jianghao'

import requests as r
import time



def get(url):
    time.sleep(3)
    return r.get(url, timeout=50)

def get_tag(url, headers):
    time.sleep(3)
    return r.get(url, headers=headers, timeout=50)





if __name__ == '__main__':
    headers={'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36"}

    # r = get("http://www.baidu.com")
    r = get_tag("http://www.baidu.com",headers=headers)

    print ">>>", r
