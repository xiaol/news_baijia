# -*- coding: utf-8 -*-
# import sys
# reload(sys)
# sys.setdefaultencoding('utf-8')
import codecs
import numpy as np
from matplotlib import pyplot as plt
import pandas as pd
import jieba
import re
import os
DIR = '../../Wiki/_posts/notes'

import seaborn as sns
# styles = ["white", "dark", "whitegrid", "darkgrid", "ticks"]
sns.set(style="darkgrid")

data = '郭韦良是一个亘古未见的大好人。'

def clean_text(data):
    # delete the html, website and mathjax
    d = re.sub('<.*?>','', data)
    d = re.sub('\$\$.*?\$\$','', d)
    d = re.sub('\(http.*?\)','', d)
    d = re.sub('\{.*?\}','', d)

    # delete the numbers and other space
    # pattern ='[\d\s,:#\*\.()]'
    pattern ='[\s]'
    d = re.sub(pattern, ' ', d)
    d = re.sub('---.*?---','', d)
    #d = re.sub('[\u4E00-\u9FA5]+','', d) save only the chinese

    print type(d)


if __name__ == "__main__":
    clean_text(data)

