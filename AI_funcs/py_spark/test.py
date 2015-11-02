import os
import sys
import traceback


# Path for spark source folder
os.environ['SPARK_HOME'] = "/Users/Gavin/work/spark-1.5.1-bin-hadoop2.6"

# Append pyspark  to Python Path
sys.path.append("/Users/Gavin/work/spark-1.5.1-bin-hadoop2.6/python/")
sys.path.append("/Users/Gavin/work/spark-1.5.1-bin-hadoop2.6/python/lib/py4j-0.8.2.1-src.zip")

# try to import needed models
try:
    from pyspark import SparkContext
    from pyspark import SparkConf
    from pyspark.sql import SQLContext, Row

    print ("Successfully imported Spark Modules")

except ImportError as e:
    print ("Can not import Spark Modules {}".format(traceback.format_exc()))
    sys.exit(1)

# config spark env
conf = SparkConf().setAppName("myApp").setMaster("local")
sc = SparkContext(conf=conf)
sqlContext = SQLContext(sc)


# cogroup
def do_cogroup():
    x = sc.parallelize([('C', 4), ('B', (3, 3)), ('A', 2), ('A', (1, 1))])
    y = sc.parallelize([('A', 8), ('B', 7), ('A', 6), ('D', (5, 5))])
    z = x.cogroup(y)
    print(x.collect())
    print(y.collect())
    for key, val in list(z.collect()):
        print(key, [list(i) for i in val])


# groupByKey()
def do_group_by_key():
    example = sc.parallelize([(0, u'D'), (0, u'D'), (1, u'E'), (2, u'F')])
    gbk = example.groupByKey().collect()
    for nnn in gbk:
        print(nnn)
        for xx in nnn[1]:
            print(xx)


# reduceByKey() with custom parallelism
def do_reduce_by_key():
    data = [("a", 3), ("b", 4), ("a", 1)]
    depa = sc.parallelize(data).reduceByKey(lambda x, y: x + y)  # Default parallelism
    cupa = sc.parallelize(data).reduceByKey(lambda x, y: x + y, 10)  # Custom parallelism
    print(depa.collect())

    print(cupa.collect())


def do_combine_by_key():
    """
    Using combineByKey
    Aggregating data is a fairly straight-forward task, but what if you are working with
    a distributed data set, one that does not fit in local memory?

    In this post I am going to make use of key-value pairs and Apache-Spark's combineByKey
    method to compute the average-by-key. Aggregating-by-key may seem like a trivial task,
    but it happens to play a major role in the implementation of algorithms such as KMeans,
    Naive Bayes, and TF-IDF. More importantly, implementing algorithms in a distributed framework
    such as Spark is an invaluable skill to have.
    """
    data = sc.parallelize([(0, 2.), (0, 4.), (1, 0.), (1, 10.), (1, 20.)])
    """
    In order to aggregate an RDD's elements in parallel, Spark's combineByKey method requires
    three functions:

    createCombiner
    mergeValue
    mergeCombiner
    The first required argument in the combineByKey method is a function to be used as the very
    first aggregation step for each key. The argument of this function corresponds to the value
    in a key-value pair. If we want to compute the sum and count using combineByKey, then we can
    create this "combiner" to be a tuple in the form of (sum, count). The very first step in this
    aggregation is then (value, 1), where value is the first RDD value that combineByKey comes
    across and 1 initializes the count.
    """
    create_combiner = lambda value: (value, 1)
    """
    The next required function tells combineByKey what to do when a combiner is given a new value.
    The arguments to this function are a combiner and a new value. The structure of the combiner is
    defined above as a tuple in the form of (sum, count) so we merge the new value by adding it to
    the first element of the tuple while incrementing 1 to the second element of the tuple.
    """
    merge_value = lambda x, value: (x[0] + value, x[1] + 1)
    """
    The final required function tells combineByKey how to merge two combiners. In this example with
    tuples as combiners in the form of (sum, count), all we need to do is add the first and last
    elements together.
    """
    merge_combiner = lambda x, y: (x[0] + y[0], x[1] + y[1])

    sum_count = data.combineByKey(create_combiner, merge_value, merge_combiner)
    """
    Compute the Average
    Ultimately the goal is to compute the average-by-key. The result from combineByKey is an RDD with
    elements in the form (label, (sum, count)), so the average-by-key can easily be obtained by using
    the map method, mapping (sum, count) to sum / count.

    Note: I do not use sum as variable name in the code because it is a built-in function in Python.
    """
    average_by_key = sum_count.map(lambda (label, (value_sum, count)): (label, value_sum / count))
    print(average_by_key.collectAsMap())


# Creating a pair RDD using the first word as the key
def pair_rdd_1st_w_as_k():
    lines = sc.textFile("README.md")  # Create an RDD called lines
    pairs = lines.map(lambda x: (x.split(" ")[0], x))
    result = pairs.filter(lambda key_value: len(key_value[1]) < 20)
    print(result.collect())


def do_aggregate():
    """
    aggregate(zeroValue, seqOp, combOp)

    Aggregate lets you take an RDD and generate a single value that is of a different
    type than what was stored in the original RDD.

    It does this with three parameters. A zeroValue (or initial value) in the format of
    the result. A seqOp function that given the resulting type and an individual element
    in the RDD will merge the RDD element into the resulting object.

    The combOb merges two resulting objects together.

    Consider an example. We want to take a list of records about people and then we want
    to sum up their ages and count them. So for this example the type in the RDD will be
    a Dictionary in the format of {name: NAME, age:AGE, gender:GENDER}. The result type
    will be a tuple that looks like so (Sum of Ages, Count)

    Lets first generate a peopleRDD with 5 people
    """
    people = []
    people.append({'name': 'Bob', 'age': 45, 'gender': 'M'})
    people.append({'name': 'Gloria', 'age': 43, 'gender': 'F'})
    people.append({'name': 'Albert', 'age': 28, 'gender': 'M'})
    people.append({'name': 'Laura', 'age': 33, 'gender': 'F'})
    people.append({'name': 'Simone', 'age': 18, 'gender': 'T'})
    people_rdd = sc.parallelize(people)
    print(len(people_rdd.collect()))
    """
    Now we need to create the seqOp. This takes an object of the rdd type and merge it
    into a record of the result type. Or another way to say this is add the age to the
    first element of the resulting tuple and add 1 for the second element of the tuple
    """
    seqOp = (lambda x, y: (x[0] + y['age'], x[1] + 1))
    """
    Now we write an operation to merge two resulting tuple.
    """
    combOp = (lambda x, y: (x[0] + y[0], x[1] + y[1]))
    """
    Run the function
    """
    agg_result = people_rdd.aggregate((0, 0), seqOp, combOp)
    print(agg_result)
    """
    And here is the result. So why is this convoluted? The combOp seems unecessary but
    in the map reduce world of spark you need that seperate operation. Realize that
    these functions are going to be parallelized. peopleRDD is partitioned up.
    And dependending on its source and method of converting the data to an RDD each
    row could be on its own partition.

    So lets backup and define a few things

    partition - A partition is how the RDD is split up. If our RDD was 100,000 records
    we could have as many as 100,000 partitions or only 1 partition depending on how
    we created the RDD.

    task - A small job that operates on a single partition. A single task can run on only
    one machine at a time and can operate on only one partiton at a time.

    For the aggregate function the seqOp will run once for every record in a partition.
    This will result in a resulting object for each partition. The combOp will be used
    to merge all the resulting objects together.
    """


def do_reduce():
    nums = sc.parallelize([1, 2, 3, 4])
    summation = nums.reduce(lambda x, y: x + y)
    print(summation)


def do_map():
    nums = sc.parallelize([1, 2, 3, 4])
    squared = nums.map(lambda x: x * x).collect()
    for num in squared:
        print(num)


def do_flat_map():
    lines = sc.parallelize(["hello world", "hi"])
    words = lines.flatMap(lambda line: line.split(" "))
    print(words.first())  # returns "hello"


# join
def do_join():
    """
    The simple join operator is an inner join.1 Only keys that are present in both pair RDDs
    are output. When there are multiple values for the same key in one of the inputs, the
    resulting pair RDD will have an entry for every possible pair of values with that key
    from the two input RDDs.
    """
    x = sc.parallelize([('C', 4), ('B', 3), ('A', 2), ('A', 1)])
    y = sc.parallelize([('A', 8), ('B', 7), ('A', 6), ('D', 5)])
    z = x.join(y)
    print(x.collect())
    print(y.collect())
    print(z.collect())


def do_left_outer_join():
    # leftOuterJoin
    x = sc.parallelize([('C', 4), ('B', 3), ('A', 2), ('A', 1)])
    y = sc.parallelize([('A', 8), ('B', 7), ('A', 6), ('D', 5)])
    z = x.leftOuterJoin(y)
    print(x.collect())
    print(y.collect())
    print(z.collect())


def do_right_outer_join():
    # rightOuterJoin
    x = sc.parallelize([('C', 4), ('B', 3), ('A', 2), ('A', 1)])
    y = sc.parallelize([('A', 8), ('B', 7), ('A', 6), ('D', 5)])
    z = x.rightOuterJoin(y)
    print(x.collect())
    print(y.collect())
    print(z.collect())


def do_sort_by_key():
    rdd = sc.parallelize([('C', 4), ('B', 3), ('A', 2), ('A', 1), ('D', 1), ('A', 3), ('A', 1)])
    sk = rdd.sortByKey(ascending=True, numPartitions=None, keyfunc=lambda x: str(x))
    print(sk.collect())


# countByKey()  Count the number of elements for each key.
def do_count_by_key():
    rdd = sc.parallelize([(1, 2), (3, 4), (3, 6)])
    cbk = rdd.countByKey()
    print(cbk)


#collectAsMap()  Collect the result as a map to provide easy lookup.
def do_collect_as_map():
    rdd = sc.parallelize([(1, 2), (3, 4), (3, 6)])
    cam = rdd.collectAsMap()
    print(cam)


#lookup(key)    Return all values associated with theprovided key.
def do_lookup():
    rdd = sc.parallelize([(1, 2), (3, 4), (3, 6)])
    lu = rdd.lookup(3)
    print(lu)


# partitionBy
def do_partition_by():
    rdd = sc.parallelize([(0, 1), (1, 2), (2, 3)], 2)
    prdd = rdd.partitionBy(numPartitions=3, partitionFunc=lambda x: x)  # only key is passed to paritionFunc
    print(rdd.glom().collect())
    print(prdd.glom().collect())


if __name__ == "__main__":
    print('################################################')
    do_reduce_by_key()
    print('################################################')
    do_partition_by()
    print('################################################')
    do_lookup()
    print('################################################')
    do_collect_as_map()
    print('################################################')
    do_count_by_key()
    print('################################################')
    do_sort_by_key()
    print('################################################')
    do_right_outer_join()
    print('################################################')
    do_left_outer_join()
    print('################################################')
    do_join()
    print('################################################')
    do_cogroup()
    print('################################################')