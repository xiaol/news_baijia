# -*- coding:utf8 -*-
from __future__ import print_function
__author__ = 'Weiliang Guo'

from collections import defaultdict
s = [('yellow', 1), ('blue', 2), ('yellow', 3), ('blue', 4), ('red', 1)]

d = defaultdict(list)
for k, v in s:
    d[k].append(v)
print(list(d.items()))

print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
s = 'mississippi'
d = defaultdict(int)
for k in s:
    d[k] += 1
print(list(d.items()))



"""Suppose you are given a list of words and you are asked to compute frequencies."""
wordlist = ['a', 'a', 'b', 'c', 'd']
frequencies = defaultdict(int)
for word in wordlist:
    frequencies[word] += 1
print(frequencies)


"""The chain() function takes several iterators as arguments and returns a single
 iterator that produces the contents of all of them as though they came from a single sequence."""
from itertools import chain, combinations

for i in chain([1, 2, 3], ['a', 'b', 'c']):
    print(i)

"""combinations(iterable, r)"""
print('combination example:')
combi = combinations([1, 2, 3, 4, 5], 2)
for cb in combi:
    print(cb)
    print('sutraction calculation: ' + str(cb[0] - cb[1]))

"""enumerate(sequence, start=0)    argument start is optional, default is 0"""
mylist = ["a", "b", "c", "d"]
enlist = [(i, j) for i, j in enumerate(mylist, start=1)]
print(enlist)


"""
Though sets can't contain mutable objects, sets are mutable.
Frozensets are like sets except that they are immutable.
"""
cities = set(["Frankfurt", "Basel","Freiburg"])
cities.add("Strasbourg")
print(cities)

decities = frozenset(["Frankfurt", "Basel","Freiburg"])
try:
    decities.add("Strasbourg")
except:
    print("'frozenset' object has no attribute 'add'")

M = ['a', 'b', 'c']
N = ['d', 'e', 'f']
dlc = [(x, y) for x in M for y in N]
print(dlc)


"""
s为字符串，rm为要删除的字符序列

s.strip(rm)        删除s字符串中开头、结尾处，位于 rm删除序列的字符

s.lstrip(rm)       删除s字符串中开头处，位于 rm删除序列的字符

s.rstrip(rm)      删除s字符串中结尾处，位于 rm删除序列的字符

当rm为空时，默认删除空白符（包括'\n', '\r',  '\t',  ' ')
"""
ab = '        123'
print(ab.strip())
cd = '\t\t123'
print(cd.strip())
ef = '123\r\n'
print(ef.strip())