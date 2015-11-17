from __future__ import print_function
import re
import unittest
from collections import defaultdict


import numpy as np
import itertools

def first_pass(transactions, number_of_items):
	index = 1
	hash_names = {}
	counts = np.zeros(number_of_items, dtype = np.int64)

	for transaction in transactions:
		for item in transaction:
			if item not in hash_names:
				hash_names[item] = index
				counts[index - 1] += 1
				index += 1
			else:
				counts[hash_names[item] - 1] += 1

	return hash_names, counts


def between_passes(counts, support):
	return 1 * (counts >= support)


def second_pass(transactions, hash_names, frequent, support):
	counts_pairs = {}

	for transaction in transactions:
		temp = [hash_names[item] for item in transaction
								 if frequent[hash_names[item] - 1] == 1]

		for pair in itertools.combinations(temp, 2):
			if pair in counts_pairs:
				counts_pairs[pair] += 1
			else:
				counts_pairs[pair] = 1

	return counts_pairs


if __name__ == '__main__':
	transactions = [['r', 'z', 'h', 'j', 'p'],
			        ['z', 'y', 'x', 'w', 'v', 'u', 't', 's'],
	                ['z'],
	                ['r', 'x', 'n', 'o', 's'],
	                ['y', 'r', 'x', 'z', 'q', 't', 'p'],
	                ['y', 'z', 'x', 'e', 'q', 's', 't', 'm']]

	support = 2
	number_of_items = 17

	hash_names, counts = first_pass(transactions, number_of_items)
	print(hash_names)
	print(counts)

	frequent = between_passes(counts, support)
	print(frequent)

	counts_pairs = second_pass(transactions, hash_names, frequent, support)
	print(counts_pairs)