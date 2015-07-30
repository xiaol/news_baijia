
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
    a_sample_sentence_to_compress = '凌德权认为,通过中越双方对阮富仲访华的一系列精心安排可以看出,两国领导人都十分珍视中越传统友谊,并有强烈的共同意愿,推动两国全面战略合作伙伴关系长期稳定健康发展'
    sencom = SentenceCompressor()
    sencom = sencom.get_compression_result(raw_sentence=a_sample_sentence_to_compress)
    result = sencom["result"]
    sentence = sencom["sentence"]

    print("The original sentence is: " + sentence)
    print("The compressed result is: " + result)


