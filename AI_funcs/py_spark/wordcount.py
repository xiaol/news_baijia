from __future__ import print_function
import os
import sys
import traceback
import json
from operator import add

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
    print("Successfully imported Spark Modules")

except ImportError as e:
    print("Can not import Spark Modules {}".format(traceback.format_exc()))
    sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: wordcount <file>", file=sys.stderr)
        exit(-1)
    sc = SparkContext(appName="PythonWordCount")
    lines = sc.textFile(sys.argv[1], 1)
    counts = lines.flatMap(lambda x: x.split(' ')) \
                  .map(lambda x: (x, 1)) \
                  .reduceByKey(add)
    output = counts.collect()
    for (word, count) in output:
        print("%s: %i" % (word, count))

    sc.stop()
