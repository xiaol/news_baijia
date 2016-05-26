# coding=utf-8
__author__ = 'yangjiwen'
from pyltp import Segmentor, Postagger, Parser, NamedEntityRecognizer, SementicRoleLabeller

segmentor = Segmentor()
segmentor.load("/root/pyltp/ltp_data/cws.model")
# segmentor.load("/Users/yangjiwen/Documents/resume/pyltp/ltp_data/cws.model")

postagger = Postagger()
postagger.load("/root/pyltp/ltp_data/pos.model")
# postagger.load("/Users/yangjiwen/Documents/resume/pyltp/ltp_data/pos.model")

recognizer = NamedEntityRecognizer()
recognizer.load("/root/pyltp/ltp_data/ner.model")
# recognizer.load("/Users/yangjiwen/Documents/resume/pyltp/ltp_data/ner.model")

def ltp_model(txt):
    sentence = txt.encode("utf-8")
    words = segmentor.segment(sentence)
    # print "\n".join(words)
    num =len(words)
    # print "num,%s" %num
    postags = postagger.postag(words)
    netags = recognizer.recognize(words, postags)
    result = {}
    result["person"] = []
    for i in range(num):
        # print "%s  %s  " % (netags[i], words[i]),
        if netags[i].find("Nh") >= 0:
            result["person"].append(words[i])
    return result

if __name__ == '__main__':
    print "hello"
    # str1 =
    str1 = "周杰伦是个好孩子"
    print ltp_model(str1)