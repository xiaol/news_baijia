"""A simple Spark app in Python"""
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


# we take the raw data in CSV format and convert it into a set of records of the form (user, product, price)
data = sc.textFile("data/UserPurchaseHistory.csv").\
    map(lambda line: line.split(",")).map(lambda record: (record[0], record[1], record[2]))
# let's count the number of purchases
numPurchases = data.count()
# let's count how many unique users made purchases
uniqueUsers = data.map(lambda record: record[0]).distinct().count()
# let's sum up our total revenue
totalRevenue = data.map(lambda record: float(record[2])).sum()
# let's find our most popular product
products = data.map(lambda record: (record[1], 1.0)).reduceByKey(lambda a, b: a + b).collect()
mostPopular = sorted(products, key=lambda x: x[1], reverse=True)[0]

# Finally, print everything out
print "Total purchases: %d" % numPurchases
print "Unique users: %d" % uniqueUsers
print "Total revenue: %2.2f" % totalRevenue
print "Most popular product: %s with %d purchases" % (mostPopular[0], mostPopular[1])

# stop the SparkContext
sc.stop()
