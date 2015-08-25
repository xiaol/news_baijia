# -*- coding:utf8 -*-
__author__ = 'Weiliang Guo'

import sys
reload(sys)
sys.setdefaultencoding('utf8')
from itertools import chain, combinations
from collections import defaultdict
import json


def subsets(arr):
    """ Returns non empty subsets of arr"""
    return chain(*[combinations(arr, i + 1) for i, a in enumerate(arr)])


def returnItemsWithMinSupport(itemSet, transactionList, minSupport, freqSet):
        """calculates the support for items in the itemSet and returns a subset
       of the itemSet each of whose elements satisfies the minimum support"""
        _itemSet = set()
        localSet = defaultdict(int)

        for item in itemSet:
                for transaction in transactionList:
                        if item.issubset(transaction):
                                freqSet[item] += 1
                                localSet[item] += 1

        for item, count in localSet.items():
                support = float(count)/len(transactionList)

                if support >= minSupport:
                        _itemSet.add(item)

        return _itemSet


def joinSet(itemSet, length):
        """Join a set with itself and returns the n-element itemsets"""
        return set([i.union(j) for i in itemSet for j in itemSet if len(i.union(j)) == length])


def getItemSetTransactionList(data_iterator):
    transactionList = list()
    itemSet = set()
    for record in data_iterator:
        transaction = frozenset(record)
        transactionList.append(transaction)
        for item in transaction:
            itemSet.add(frozenset([item]))              # Generate 1-itemSets
    return itemSet, transactionList


def runApriori(data_iter, minSupport, minConfidence):
    """
    run the apriori algorithm. data_iter is a record iterator
    Return both:
     - items (tuple, support)
     - rules ((pretuple, posttuple), confidence)
    """
    itemSet, transactionList = getItemSetTransactionList(data_iter)

    freqSet = defaultdict(int)
    largeSet = dict()
    # Global dictionary which stores (key=n-itemSets,value=support)
    # which satisfy minSupport

    assocRules = dict()
    # Dictionary which stores Association Rules

    oneCSet = returnItemsWithMinSupport(itemSet,
                                        transactionList,
                                        minSupport,
                                        freqSet)

    currentLSet = oneCSet
    k = 2
    while(currentLSet != set([])):
        largeSet[k-1] = currentLSet
        currentLSet = joinSet(currentLSet, k)
        currentCSet = returnItemsWithMinSupport(currentLSet,
                                                transactionList,
                                                minSupport,
                                                freqSet)
        currentLSet = currentCSet
        k = k + 1

    def getSupport(item):
            """local function which Returns the support of an item"""
            return float(freqSet[item])/len(transactionList)

    toRetItems = []
    for key, value in largeSet.items():
        toRetItems.extend([(list(item), getSupport(item))
                           for item in value])

    toRetRules = []
    for key, value in largeSet.items()[1:]:
        for item in value:
            _subsets = map(frozenset, [x for x in subsets(item)])
            for element in _subsets:
                remain = item.difference(element)
                if len(remain) > 0:
                    confidence = getSupport(item)/getSupport(element)
                    if confidence >= minConfidence:
                        toRetRules.append(((list(element), list(remain)),
                                           confidence))
    return toRetItems, toRetRules


def printResults(items, rules):
    """prints the generated itemsets sorted by support and the confidence rules sorted by confidence"""
    for item, support in sorted(items, key=lambda (item, support): support):
        item = json.dumps(item, ensure_ascii=False)
        print "item: %s , %.3f" % (item, support)


    print "\n------------------------ RULES:"
    for rule, confidence in sorted(rules, key=lambda (rule, confidence): confidence):
        pre, post = rule
        pre = json.dumps(pre, ensure_ascii=False)
        post = json.dumps(post, ensure_ascii=False)
        print "Rule: %s ==> %s , %.3f" % (pre, post, confidence)


def dataFromFile():
    fname = [[u'\u5f3a\u53f0\u98ce', u'\u82cf\u8fea\u7f57', u'\u65f6', u'\u53f0\u6e7e', u'\u82b1\u83b2', u'\u5c0f\u65f6', u'\u901f\u5ea6', u'\u897f\u504f', u'\u53f0\u6e7e\u5c9b', u'\u798f\u5efa\u7701', u'\u664b\u6c5f', u'\u798f\u6e05', u'\u4e00\u5e26', u'\u798f\u5efa\u7701', u'\u4e25\u91cd\u5a01\u80c1', u'ezfrcfcxlr'], [u'\u798f\u5efa\u7701', u'\u65f6', u'\u53f0\u98ce', u'qfzwmgfijs'], [u'\u798f\u5efa\u7701', u'\u5385', u'\u6d88\u606f', u'\u98ce\u60c5', u'\u96e8\u60c5', u'\u798f\u5efa\u7701', u'\u9ad8\u901f\u516c\u8def', u'\u90e8\u5206', u'\u8def\u6bb5', u'\u7981\u6b62\u901a\u884c', u'dpsdfgndly'], [u'\u5e73\u6f6d', u'\u6d77\u5ce1', u'\u5927\u6865', u'\u98ce\u6d6a', u'\u4eca\u5929\u4e0a\u5348', u'\u5c9b', u'\u53cc\u5411', u'gprsvhtsbe'], [u'\u6c88\u6d77', u'\u9ad8\u901f\u516c\u8def', u'\u6db5\u6c5f', u'\u4ed9\u6e38', u'\u8386\u7530', u'\u8d27\u8f66', u'\u5ba2\u8f66', u'\u9ad8\u901f\u516c\u8def', u'\u5c0f\u6c7d\u8f66', u'cvvxdnrtsy'], [u'\u65f6\u95f4', u'\u98ce\u60c5', u'\u96e8\u60c5', u'lvozhxpibw'], [u'\u95fd\u53f0', u'\u5ba2\u8fd0', u'\u5168\u9762', u'\u53a6\u95e8', u'\u5e73\u6f6d', u'\u53f0\u6e7e', u'\u672c\u5c9b', u'\u6d77\u5ce1', u'\u4e3d\u5a1c', u'\u4e2d\u8fdc', u'\u661f', u'\u5ba2', u'\u8239', u'\u56de\u6e2f', u'\u53a6\u95e8', u'\u91d1\u95e8', u'\u6cc9\u5dde', u'\u91d1\u95e8', u'\u9a6c\u7956', u'\u6761', u'\u5c0f\u4e09\u901a', u'\u5ba2\u8fd0', u'\u822a\u7ebf', u'\u5168\u90e8', u'\u9646\u5c9b', u'\u5ba2\u8fd0', u'ehjjdtqmch'], [u'\u8bb0\u8005', u'\u798f\u5dde', u'\u673a\u573a', u'\u53f0\u98ce', u'\u82cf\u8fea\u7f57', u'\u798f\u5dde', u'\u673a\u573a', u'\u98ce\u529b', u'\u9635\u98ce', u'\u798f\u5dde', u'\u673a\u573a', u'\u5f3a\u964d\u96e8', u'jweqczoflj'], [u'\u798f\u5dde', u'\u822a\u7a7a', u'\u53a6\u95e8\u822a\u7a7a', u'\u4e1c\u65b9\u822a\u7a7a', u'\u6df1\u5733', u'\u822a\u7a7a', u'\u4e2d\u56fd', u'\u56fd\u9645\u822a\u7a7a', u'\u822a\u7a7a', u'\u4e0a\u6d77', u'\u822a\u7a7a', u'\u56db\u5ddd', u'\u822a\u7a7a', u'\u6210\u90fd', u'\u822a\u7a7a', u'\u897f\u85cf', u'\u822a\u7a7a', u'\u822a\u7a7a', u'\u5929\u6d25', u'\u822a\u7a7a', u'\u5409\u7965', u'\u822a\u7a7a', u'\u822a\u7a7a', u'\u822a\u7a7a', u'\u822a\u7a7a', u'\u9999\u6e2f', u'\u822a\u7a7a', u'\u534e\u4fe1', u'\u822a\u7a7a', u'\u7acb\u8363', u'\u822a\u7a7a', u'\u822a\u7a7a', u'\u822a\u7a7a\u516c\u53f8', u'\u798f\u5dde', u'\u673a\u573a', u'\u8fdb\u51fa\u6e2f', u'\u822a\u73ed', u'pbswixmjus'], [u'\u8bb0\u8005', u'\u845b\u671d\u5174', u'hptdfpukmk']]
    fname2 = [[u'\u4e2d\u65b0\u7f51', u'\u53f0\u6e7e', u'\u4e1c\u68ee', u'\u65b0\u95fb', u'\u5468\u6770\u4f26', u'\u5973', u'\u793e\u4ea4', u'\u7f51\u7ad9', u'\u7238\u7238', u'\u5973\u513f', u'\u7167\u7247', u'\u7236\u7231', u'ytiwgqsqpi'], [u'\u7167\u7247', u'\u5468\u6770\u4f26', u'\u5973\u513f', u'\u73b0\u8eab', u'\u5c0f\u59d1\u5a18', u'\u5a74\u513f', u'\u7238\u7238', u'crogvlbwro'], [u'\u5468\u6770\u4f26', u'\u5730\u7528', u'\u53cc\u624b', u'\u5b69\u5b50', u'\u8116\u5b50', u'\u4e0b\u534a\u8eab', u'\u7236\u7231', u'wkytcpidyn'], [u'\u5468\u6770\u4f26', u'\u4eba\u751f', u'\u7238\u7238', u'\u611f\u89c9', u'\u5927\u5bb6', u'\u7236\u4eb2\u8282', u'psbsnlneau'], [u'\u7167\u7247', u'rbjxsrgrkv'], [u'\u7f51\u53cb', u'\u5468\u6770\u4f26', u'\u8863\u670d', u'\u5b57\u6837', u'\u6b4c\u8ff7', u'\u7238\u7238', u'daolduvrvd'], [u'xsjizkefex']]

    for line in fname2:
        record = frozenset(line)
        yield record


if __name__ == "__main__":

    items, rules = runApriori(dataFromFile(), 0.01, 0.6)

    printResults(items, rules)
