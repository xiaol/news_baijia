#coding=utf-8
import math

__author__ = 'galois'

from analyzer import jieba
import operator
import re

jieba.initialize()
jieba.load_stopdict()

SENTENCE_SEP=re.compile(ur'[。\n!.！]')

def abstract(doc,use_tf=True):
  tf_map={}
  wordItertor=jieba.cut_with_stop(doc)
  for word in wordItertor:
      if word in tf_map:
          tf_map[word]+=1
      else:
          tf_map[word]=1
  if use_tf:
      sorted_word=sorted(tf_map.items(),key=operator.itemgetter(1),reverse=True)

      # for elem in sorted_word:
      #   print "key is %s and the value  is %d \n" %(elem[0],elem[1])
  keyWords=sorted_word[0:10]
  sentences=extractSentenceBlock(doc)
  sentence_score_pairs=[]
  for sentence in sentences:
      sentence_pair=[]
      sentence_pair.append(sentence)
      sentence_pair.append(scoreSentence(keyWords,sentence))
      sentence_score_pairs.append(sentence_pair)
  sorted_sentence=sorted(sentence_score_pairs,key=operator.itemgetter(1),reverse=True)
  for sort_sentence_pair in sorted_sentence:
      print "sentence is %s and the score is %f\n" %(sort_sentence_pair[0],sort_sentence_pair[1])

  return sorted_sentence[0][0]


def extractSentenceBlock(doc):
    result=[]
    doc_array=re.split(SENTENCE_SEP,doc.encode('utf8').decode("utf8"))
    for elem in doc_array:
        result.append(elem.strip())
    return result


def scoreSentence(keywords,sentence):
    # sentence="放眼积分榜，切尔西少赛一场位列榜首，曼城5分之差暂居次席，再往后的阿森纳、曼联、利物浦、南安普顿以及热刺则呈现出犬牙交错之势，排名第7的热刺少赛1场只比排名第三的阿森纳少7分"
    wordItertor=jieba.cut_with_stop(sentence)
    score=0.0
    count=0
    scale=0.5
    length_para=0.00002
    sen_length=0
    for word in wordItertor:
        sen_length=sen_length+1
        for keyWord in keywords:
            if word==keyWord[0]:
                score+=scale*keyWord[1]
                count+=1
                break
    score+=count*count
    score/=(math.log(sen_length+1)+1)
    score+=length_para*sen_length
    return score






if __name__=='__main__':
    test_str='''负心汉陈世美的弃妻求荣事迹，让后人在愤慨之余也不忘反省自己，一度成为了教育花心男人的反面教材。然而，时间交替却没能改变这一乱象，湖南衡阳的刘倩就和秦香莲有着相似的遭遇，数年前刘倩外出打工供丈夫李伟考研读研，随后又省吃俭用供丈夫的两个弟弟读完大学，本以为夫唱妇随的美好生活就要来临，却不想李伟的态度来了个一百八十度的大转弯。百思不得其解的刘倩经过多方打听，才在结婚24年后得知，丈夫在外早已有了小三和私生女，绝对比陈世美还要冷血无情。
妻子供丈夫读研，丈夫用背叛报答
妻子供丈夫读研被背叛
刘倩和李伟本是一对恩爱夫妻，因为李伟家境贫寒且又工作不顺，所以萌生了读研究生的想法，刘倩得知后自然是全力支持，外出打工供李伟考研读研。丈夫研究生毕业后，刘倩又将刘伟的两个弟弟供至大学毕业，绝对是好妻子的典范。随着生活水平的提高和家庭收入的增长，日子一天天越来越好，但让刘倩没有想到的是，曾经温柔体贴的丈夫却变得冷漠起来，不但经常夜不归宿，还对刘倩拳脚相加，让人心寒不已。经过调查打听，结婚24年的刘倩竟发现，刘伟早已在外金屋藏娇，并生下了一个私生女，见到事情败露，刘伟干脆一不做二不休，将名下财产悄悄转移。
古有陈世美考取功名杀妻灭口，今有丈夫读完研究生找小三，时间虽然穿越古今，人性的阴暗面却有着惊人的巧合。妻子任劳任怨供丈夫读书考试，丈夫功成名就后本应不忘糟糠之妻，奈何人都有喜新厌旧的劣根性，将过往的恩情忘的一干二净。俗话说“没有爱情还有亲情”，念在妻子独自供三个人读书的恩情上，也应该对她予以回报和感激，若是感情不和大可协商离婚，实在没有必要发展婚外情诞下私生女。妻子在丈夫一穷二白时不离不弃，丈夫却在功成名就时用背叛报答，这真是现实版“蛇与渔夫”的故事。
妻子供丈夫读研被背叛
而更为讽刺的是，丈夫给妻子戴了顶“红帽子”不说，还妄图转移财产让妻子净身出户，如此一来，真是没了道义也没了良知。虽说感情不能作为一种交易，但妻子毕竟将最好的年华都奉献给了自己，无论如何也要让她后半生衣食无忧，男子这种先不仁后不义的做法，将夫妻间仅存的一点情分也毁的干干净净。在邓高远看来，遇到这种事情，千万不能一哭二闹三上吊，而是要拿起法律武器来为自己讨个公道，重婚罪、恶意转移财产都可以作为起诉对方的罪名。
好女人背后有个花心男人，野花总比家花香
妻子供丈夫读研被背叛
如果以前是“成功男人背后都有个好女人”，那现在就是“好女人背后都有个花心男人”，这些在外人眼中贤惠能干的妻子，都无一例外的遭到了丈夫的无情背叛。除了用“家家都有本难念的经”来解释外，头条前瞻的邓高远更倾向于“被惯坏了”这一说话，无数例子都可以证明，付出多少与感知程度会随着时间增长而成反比，付出的一方深陷“救世主”身份不可自拔，而被爱的一方则被这种感情束缚的喘不过气来，久而久之，就会变成习惯性的索取和心理上的麻木。
维持感情并不是靠一方的努力就可以完成的，而是双向施力的互相平衡，男方出轨定然有其违背道德之处，但女方也需要痛定思痛好好反思。当然，邓高远最有感触的就是，结婚前一定要看清楚对方的真面目，不要等到耗费了大半青春，才发现所谓的“好男人”竟是生活在谎言中的寄生虫。
'''
    test_str2 = u'''亚投行创始成员国的资格确认截止于2015年3月31日。伴随着亚投行创始成员国申请截止日期的临近，英国、法国、德国、意大利等发达国家申请加入亚投行。3月20日，瑞士正式申请作为创始成员国加入亚投行 '''


    print abstract(test_str2)



