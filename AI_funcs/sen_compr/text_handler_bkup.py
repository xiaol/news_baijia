
# -*- coding:utf8 -*-
from __future__ import print_function
__author__ = 'Gavin'

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import requests
import re

class SentenceCompressor:
    def __init__(self, api_url="http://60.28.29.37:8080/SentenceCompressor?sentence="):
        self.api_url = api_url

    # If you want to match a certain part of a string using a regex,
    # just add a new regex-string condition pair into this method body.

    @staticmethod
    def normalize_orders(matchobj):
        if matchobj.group() == "%":
            return "百分号"
        elif matchobj.group() == '\[':
            return '('
        elif matchobj.group() == ']':
            return ')'
        elif matchobj.group() == "-":
            # return "_"
            return "_"
        elif matchobj.group() == '·':
            return '_'
        # elif matchobj.group() == " ":
        #     return ","
        elif matchobj.group() == r"[,|，].*称[,|，]|“|”| |‘|’|《|》":
            return ""

    #Collect all the regular expressions to be used.  | stands for bitwise OR.
    def regex_collect(self):
        rg = r"[,|，].*称[,|，]|“|”| |‘|’|《|》|%|\[|]|-|·"
        return rg

    # text is the string to be pre-processed, regex is the regular expression(s).
    def text_preprocess(self, raw_sentence):
        regex = self.regex_collect()
        text = raw_sentence
        pre_processed_txt = re.sub(regex, SentenceCompressor.normalize_orders, text)
        return pre_processed_txt

    #Get last text segment of a sentence as last comma encountered
    def get_last_sen_seg(self, sen=''):
        # last_sen_seg = sen.split('，')[-1]
        last_sen_seg = re.split(",|，", sen)[-1]
        return last_sen_seg

    def get_compression_result(self, raw_sentence):
        refined_text = self.text_preprocess(raw_sentence)
        get_last_sen_seg = self.get_last_sen_seg(refined_text)
        sentence_ready_to_compress = get_last_sen_seg
        if len(refined_text) <= 12:
            return refined_text
        compr_result = requests.get(self.api_url + sentence_ready_to_compress)
        compr_result = compr_result.json()
        return compr_result


if __name__ == '__main__':
    a_sample_sentence_to_compress = """值得关注的是，7月24日，张晓军在介绍2015年上半年稽查执法工作时，就提及根据国务院统一部署，证监会全面开展“两个加强、两个遏制”专项检查，根据检查发现的证券公司融资融券业务及场外利用HOMS系统开展股票配资业务中存在的违规问题与风险隐患，证监会及时加强风险控制与监管执法力度，并组织力量进场核查，监督整改，并根据核查掌握的情况，对有关涉案主体正式立案查处"""
    sencom = SentenceCompressor()
    sencom = sencom.get_compression_result(raw_sentence=a_sample_sentence_to_compress)
    result = sencom["result"]
    sentence = sencom["sentence"]

    print("The original sentence is: " + sentence)
    print("The compressed result is: " + result)



