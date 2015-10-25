# -*- coding:utf8 -*-
from __future__ import print_function
__author__ = 'Gavin'

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import requests
import uniout
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
        pre_processed_txt = re.sub(regex, SentenceCompressor.normalize_orders, raw_sentence)
        rs = pre_processed_txt.replace('：“', '').replace('，“', '')

        return rs

    #Get last text segment of a sentence as last comma encountered
    # def get_last_sen_seg(self, sen=''):
    #
    #     print(last_sen_seg)
    #     return last_sen_seg

    def get_compression_result(self, raw_sentence):
        # raw_sentence = raw_sentence.decode('utf-8')
        # refined_text = self.text_preprocess(raw_sentence)
        raw_sentence = raw_sentence.replace('、', '和').replace('+', '加').replace('“', '').replace('”', '')\
            .replace("‘", "").replace("’", '').replace('%', '').replace('-', '_')

        if len(raw_sentence) <= 12:
            return raw_sentence

        sen_seg = re.split(",|，", raw_sentence)
        len_sen_seg = len(sen_seg)
        last_sen_seg = sen_seg[-1]

        # We use a cycle to ensure the sentence to have more than 6 characters, one chinese character equal 3 ascii charaters.
        reverse_idx = 2
        while(len(last_sen_seg) <=9 and len_sen_seg >= reverse_idx):
            tmp_seg = sen_seg[-reverse_idx] 
            tmp_seg += last_sen_seg
            last_sen_seg = tmp_seg
            print (last_sen_seg)
            print ('length of last sen seg : ' + str(len(last_sen_seg)))
            reverse_idx += 1

        sentence_ready_to_compress = last_sen_seg
        compr_result = requests.get(self.api_url + sentence_ready_to_compress)
        compr_result = compr_result.json()
        if reverse_idx > 2:   
            print ('last_sen_seg' + last_sen_seg)
            print ('length of last_sen_seg ' + str(len(last_sen_seg)))
            print (100 *'-')
            print ('_Result_' +  compr_result['result'] + '\t' + compr_result['sentence'])
            print (100 *'^')
        return compr_result


if __name__ == '__main__':
    #a_sample_sentence_to_compress = '收到各方好友和媒体的祝福，在此表示感谢。'
    a_sample_sentence_to_compress = '收到各方好友和媒体的祝福，在，此，感，谢。'
    sencom = SentenceCompressor()
    sencom = sencom.get_compression_result(raw_sentence=a_sample_sentence_to_compress)
    result = sencom["result"]
    sentence = sencom["sentence"]

    print("The original sentence is: " + sentence)
    print("The compressed result is: " + result)
