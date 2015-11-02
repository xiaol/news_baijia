#-*- coding: utf-8 -*-
__author__ = 'Weiliang Guo'
import uniout
from AI_funcs.cwn2.cwn import synset
import jieba
import matplotlib
import matplotlib.pyplot as pyplot
import os
import codecs
stopwords = os.path.join(os.path.dirname(__file__), 'stopword.data')

"""
s=synset('中')

print ' '.join(s.synonyms)
print ' '.join(s.antonyms)
print ' '.join(s.hyponyms)
print ' '.join(s.hypernyms)

from urllib import urlopen
textPage = urlopen("http://www.pythonscraping.com/pages/warandpeace/chapter1-ru.txt")
print(textPage.read())
"""


class Preprocessor:
    def __init__(self, stop_words_file=stopwords):
        self.stop_words_file = stop_words_file
        self.stop_tokens = "，。！？：；“”\"/\\`!#%^&*()_+-={}[]|;:'‘’<>?,.～·—「；：《》（）、― ―".decode('utf-8')
        stop_words = set()
        if type(self.stop_words_file) is str:
            for word in codecs.open(self.stop_words_file, 'r', 'utf-8', 'ignore'):
                stop_words.add(word.strip())
        self.stop_words = list(stop_words)

    #texts is a list of strings
    def bag_of_words(self, texts=['你真的会是一个好人吗？', '你会不会抢我的面包？']):
        bow = set()
        for text in texts:
            text_cut_gen = jieba.cut(text)
            for w in text_cut_gen:
                if w not in self.stop_tokens:
                    if w not in self.stop_words:
                        bow.add(w)
        print(bow)
        return bow







if __name__ == "__main__":
    prep = Preprocessor()
    prep.bag_of_words()

