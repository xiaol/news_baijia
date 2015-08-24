# -*- coding:utf8 -*-
from __future__ import print_function
__author__ = 'Weiliang Guo'
from OpinionClassifier import Feature
from collections import defaultdict

class Apriori:
    def __init__(self, f=Feature(), min_support=0.01, min_conf=0.60):
        self.min_support = min_support
        self.min_conf = min_conf
        self.articles_with_pos = f.get_pos()
        event_counts = {}
        for event_id, event_docs in self.articles_with_pos.iteritems():
            n_count = 0
            for news_id, news_article in event_docs.iteritems():
                for sentence in news_article:
                    n_count += len(sentence)
            event_counts[event_id] = n_count
        self.event_n_counts = event_counts


    def get_support(self, frq_x_y, n_of_all_sens):
        support = float(frq_x_y)/n_of_all_sens
        return support

    def get_n_of_all_sens(self, noun_list):
        n_of_all_sens = defaultdict(int)
        for k in noun_list:
            n_of_all_sens[k] += 1
        n_of_all_sens = list(n_of_all_sens.items())

    def get_data_ready(self):
# One SID coppresonds to nouns of one sentence   i.e. SID_01 = [n1, n2, n3,...]
#sorted_docs = {eventId_01:{article_id_01: [[n1, n2, n3,...], SID_02, SID_03, ...],
# article_id_02: article_02}, eventId_02:{...},...}
        pass


if __name__ == '__main__':
    apriori = Apriori()