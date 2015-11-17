#!/usr/bin/env python
# -*- coding: utf-8 -*- 

# 作業系統
import os
import sys

# 字碼轉換
import codecs

# 科學運算
import numpy as np
import numpy.linalg as LA

# 文字處理
import nltk
from nltk.corpus import stopwords

# 移除中文停詞
def removeChineseStopWords(textFile):
    newTextFile = textFile

    chineseFilter1 = [u'，', u'。', u'、', u'；', u'：', u'？', u'「', u'」']

    for chin in chineseFilter1:
        newTextFile = newTextFile.replace(chin, ' ')
    
    return newTextFile
    
# 讀取中文檔案
def getTokensFromFile(textFileName):
    textFileHandle = codecs.open(textFileName, 'rU','utf8')

    textContent = textFileHandle.read()
    
    for word in stopwords.words('english'):
        textContent = textContent.replace(word, ' ')
        
    textTokens = nltk.word_tokenize(removeChineseStopWords(textContent))
    
    textFileHandle.close()

    return textTokens

# 字詞頻度表
def getTokenFreqList(textTokens):
    tokenFrequency = nltk.FreqDist(textTokens)

    # 刪除單一字
    for word in tokenFrequency:
        if len(word) == 1:
            tokenFrequency.pop(word)
    
    # 刪除數字
    for word in tokenFrequency:
        try:
            val = float(word)
            tokenFrequency.pop(word)
        except:
            pass
    
    # 刪除廢詞
    chineseFilter = [u'可能', u'不過', u'如果', u'恐怕', u'其實', u'進入', u'雖然', u'這麼',
                     u'處於', u'因為', u'一定']

    for word in tokenFrequency:
        if word in chineseFilter:
            tokenFrequency.pop(word)
    
    return tokenFrequency

# 輸出字詞頻度表
def OutputDocWordFreq(wordFrequency):
    for word in wordFrequency:
        print '"%s",%d' % (word, wordFrequency[word])

# 計算 2 向量間距離
def getDocDistance(a, b):
    if LA.norm(a)==0 or LA.norm(b)==0:
        return -1
    
    return round(np.inner(a, b) / (LA.norm(a) * LA.norm(b)), 4)
    
# 計算文件相似度    
def getDocSimilarity(wordFrequencyPair, minTimes=1):
    dict1 = {}
    for key in wordFrequencyPair[0].keys():
        if wordFrequencyPair[0].get(key, 0) >= minTimes:
            dict1[key] = wordFrequencyPair[0].get(key, 0)

    dict2 = {}
    for key in wordFrequencyPair[1].keys():
        if wordFrequencyPair[1].get(key, 0) >= minTimes:
            dict2[key] = wordFrequencyPair[1].get(key, 0)

    for key in dict2.keys():
        if dict1.get(key, 0) == 0:
            dict1[key] = 0
        
    for key in dict1.keys():
        if dict2.get(key, 0) == 0:
            dict2[key] = 0
        
    v1 = []
    for w in sorted(dict1.keys()):
        v1.append(dict1.get(w))
        print "(1)", w, dict1.get(w)

    v2 = []    
    for w in sorted(dict2.keys()):
        v2.append(dict2.get(w))
        print "(2)", w, dict2.get(w)

    result = 0
    
    try:
        result = getDocDistance(v1, v2)
    except(RuntimeError, TypeError, NameError):
        pass
        
    return result

# 主程式
if __name__=="__main__":
    if len(sys.argv) < 2:
        print(u'需要輸入 2 份文件')
        exit()
    
    trainFileName = sys.argv[1]
    trainTokens = getTokensFromFile(trainFileName)
    trainTokenFrequency = getTokenFreqList(trainTokens)
    
    testFileName = sys.argv[2]
    testTokens = getTokensFromFile(testFileName)
    testTokenFrequency = getTokenFreqList(testTokens)
    
    wordFrequencyPair = [trainTokenFrequency, testTokenFrequency]
    print getDocSimilarity(wordFrequencyPair, 1)