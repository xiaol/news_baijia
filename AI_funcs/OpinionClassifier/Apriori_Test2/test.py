# -*- coding:utf8 -*-
from __future__ import print_function
__author__ = 'Weiliang Guo'
import jieba
from AI_funcs.OpinionClassifier.Apriori_Test2.appp import apriori
import re

if __name__ == '__main__':
    article1 = """
    　　央广网天津8月14日消息（记者刘云龙 贾国强）8月14日上午10时，8·12危险品仓库爆炸事故新闻发布会召开，通报事故处置进展等情况。天津市公安消防局局长周天，卫计委主任王建存，安监局副局长高怀友，天津市委宣传部副部长龚建生，南开大学环境科学与工程学院教授冯银厂等参加今日发布会。
　　天津市委宣传部副部长龚建生表示，事故组得到最新消息，早晨7点05分，在事故现场救出一名生还的消防官兵。截止今早9点，现场已经搜救出32人。
　　天津市卫计委主任王建存表示，目前已经收治伤员701人，重伤70人。
　　天津市公安消防局局长周天说，爆炸发生时，第一批消防官兵正在现场检测情况，增援消防官兵刚刚到达现场，由于处于爆炸核心区，消防官兵伤亡比较严重。
　　南开大学环境科学与工程学院教授冯银厂在发布会上表示，在爆炸期间，下风向位置几个检测点甲苯浓度较高。目前情况好些，但是下方向位置偶尔反复。记者问是不是空气质量安全？冯银厂表示，现在的空气质量对天津老百姓来说是安全的。
    """
    article2 = """
    央广网天津8月14日消息 据中国之声《央广新闻》报道，8月12日晚11：20左右，天津港国际物流中心区域内瑞海公司所属危险品仓库发生爆炸。
    """

    article1 = article1.replace(" ", "")

    sentences = re.split(r'\.|。', article1)
    for se in sentences:
        print('~~~~~~~~~~~~~~~~~~~~~~~')
        print(se)
    seg_art = []
    for sen in sentences:
        sentence = [w for w in jieba.cut(sen)]
        seg_art.append(sentence)
    ap = apriori(seg_art, 0.25)
    print(ap)
    # for k, v in ap.iteritems():
    #     print(k, v)
