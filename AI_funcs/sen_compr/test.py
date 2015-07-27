#encoding=utf8

__author__ = 'Gavin'


import os
# import jnius_config
# os.environ['CLASSPATH'] = "/Users/Gavin/work/news_baijia/AI_funcs/sen_compr/tika-app-1.9.jar"
os.environ['CLASSPATH'] = "/Users/Gavin/work/news_baijia/AI_funcs/sen_compr/MainPartExtractor.jar"
# jnius_config.add_classpath('.', '/Users/Gavin/work/news_baijia/AI_funcs/sen_compr/MainPartExtractor.jar')

# # jnius_config.add_options('-Xrs', '-Xmx4096')
# # coding=utf-8
# from PIL import Image
#


from jnius import autoclass


System = autoclass('java.lang.System')
System.out.println('Hello World')
## Import the Java classes we are going to need
# Tika = autoclass('org.apache.tika.Tika')


extractor = autoclass('Extractors.Extractors')
print dir(extractor)
test_str = u"小狗喜欢他的父亲和母亲"
extractor.setModel('sen_compr/chinesePCFG.ser', 'sen_compr/userwords.txt')
result = extractor.trunkhankey(test_str, 'sen_compr/deprules.txt', False)
print result

