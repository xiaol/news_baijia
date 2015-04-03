__author__ = 'jianghao'

import requests as r
import time
def requests(url):
    time.sleep(3)
    return r.get(url)