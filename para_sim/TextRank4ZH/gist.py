#-*- encoding:utf-8 -*-
"""
Created on May 30, 2015
@author: Gavin
"""

import sys
import codecs
from textrank4zh import TextRank4Keyword, TextRank4Sentence
reload(sys)
sys.setdefaultencoding('utf-8')
import jieba
from gensim import corpora, models, similarities
import os

class Gist:

    def __init__(self, stop_words_file='stopword.data'):
            # self.stop_words_file=stop_words_file
            self._curpath=os.path.normpath( os.path.join( os.getcwd(), os.path.dirname(__file__) ))
            self.stop_words_file=findTheFilePath(self._curpath,'../stopword.data')

            self.tr4w = TextRank4Keyword(self.stop_words_file)  # 导入停止词

    def get_keyword(self, text):
            self.tr4w = TextRank4Keyword(self.stop_words_file)  # Import stopwords
            #Use word class filtering，decapitalization of text，window is 2.
            self.tr4w.train(text=text, speech_tag_filter=True, lower=True, window=2)
            # 20 keywords The min length of each word is 1.
            self.wresult = ' '.join(self.tr4w.get_keywords(20, word_min_len=1))
            return self.wresult

    def get_keyphrase(self):
            #Use 20 keywords for contructing phrase, the phrase occurrence in original text is at least 2.
            self.presult = ' '.join(self.tr4w.get_keyphrases(keywords_num=20, min_occur_num= 2))
            self.tr4s = TextRank4Sentence(self.stop_words_file)
            return self.presult

    def get_gist(self, text_dict = {}):
        self.gresult = {}
        for key, value in text_dict.iteritems():
            # self.tr4w = TextRank4Keyword(self.stop_words_file)  # 导入停止词
            #使用词性过滤，文本小写，窗口为2
            self.tr4w.train(text=value, speech_tag_filter=True, lower=True, window=2)
            # 20个关键词且每个的长度最小为1
            self.wresult = ' '.join(self.tr4w.get_keywords(20, word_min_len=1))
            # 20个关键词去构造短语，短语在原文本中出现次数最少为2
            self.presult = ' '.join(self.tr4w.get_keyphrases(keywords_num=20, min_occur_num= 2))
            self.tr4s = TextRank4Sentence(self.stop_words_file)
            # 使用词性过滤，文本小写，使用words_all_filters生成句子之间的相似性
            self.tr4s.train(text=value, speech_tag_filter=True, lower=True, source = 'all_filters')
            self.gresult.update({key: (' '.join(self.tr4s.get_key_sentences(num=1)))})
            print key+":"+(self.gresult[key])

        return self.gresult


    def get_gist_str(self, text):
        self.tr4s = TextRank4Sentence(self.stop_words_file)
         # 使用词性过滤，文本小写，使用words_all_filters生成句子之间的相似性
        self.tr4s.train(text=text, speech_tag_filter=True, lower=True, source = 'all_filters')
        return ' '.join(self.tr4s.get_key_sentences(num=1))

def findTheFilePath(curpath,speciFile):
    # parentPathIndex=curpath.rfind('/')
    # parentPath=curpath[:parentPathIndex+1]
    speciFilePathIndex=speciFile.find('/')
    speciFilePath=speciFile[speciFilePathIndex+1:]
    finalPath=os.path.join(curpath,speciFilePath)
    return finalPath




    #query is a string, textList is a list of strings.
    #If a query only compares itself against itself or only one another document, the result is always 1.
def cal_sim(query, textList):

    textList = [list(jieba.cut(text)) for text in textList]

    dictionary = corpora.Dictionary(textList)
    corpus = [dictionary.doc2bow(text) for text in textList]
    lsi = models.LsiModel(corpus, id2word=dictionary, num_topics=2) # initialize an LSI transformation
    query_bow = dictionary.doc2bow(list(jieba.cut(query)))


    query_lsi = lsi[query_bow]
    index = similarities.MatrixSimilarity(lsi[corpus]) # transform corpus to LSI space and index it
    sims = index[query_lsi]
    print sims
    return sims

if __name__ == "__main__":
    # a = Gist().get_gist(codecs.open('/Users/Gavin/work/news_baijia_AI/para_sim/TextRank4ZH/text/01.txt', 'r', 'utf-8').read())
    # b = Gist().get_gist(codecs.open('/Users/Gavin/work/news_baijia_AI/para_sim/TextRank4ZH/text/02.txt', 'r', 'utf-8').read())
    # c = Gist().get_gist(codecs.open('/Users/Gavin/work/news_baijia_AI/para_sim/TextRank4ZH/text/05.txt', 'r', 'utf-8').read())
    #
    # x = '上个周末，吉林农业科技学院经济管理学院赵同学，本来是因为得到了一张长春市的演出邀请券，从吉林市到长春市玩，不想在重庆路逛街的途中竟看到了一个正在行窃的小偷，并用手机拍下了小偷行窃的全过程。 '
    # y = '这小偷还挺有职业道德，只偷钱，又把钱包放回去了，钱包里都是各种卡啊身份证啥的，补办起来很麻烦，很体贴的小偷，赞一个。'
    # z = '这小偷还挺有职业道德，只偷钱，又把钱包放回去了，钱包里都是各种卡啊身份证啥的，补办起来很麻烦。'
    # textList = []
    # textList.append(x)
    # textList.append(x)
    # textList.append(y)
    # textList.append(z)
    # cal_sim(x, textList)
    # ldh = "刘德华 ，MH，JP（英语：Andy Lau Tak-wah，1961年9月27日－），香港著名演员兼歌手，1990年代获封香港乐坛“四大天王”之一，[7]也是吉尼斯世界纪录大全中获奖最多的香港歌手[8]；电影方面他获得三次香港电影金像奖最佳男主角和两次金马奖最佳男主角，至今参演超过140部电影[9]。刘德华是天幕公司和映艺集团的创建者，作为投资人已参与制作了20多部华语电影。1999年，刘德华获得“香港十大杰出青年”的荣誉，2000年11月则顺利荣登“世界十大杰出青年”[11]，成为获此殊荣的少数几位香港艺人。2006年7月7日，香港演艺学院因他“是香港最受尊重和喜爱的演艺名人之一，对香港电影及音乐贡献良多。其严谨专业的工作态度，足以成为年轻人的典范”，为了“表彰他在表演艺术方面的成就”而授予刘德华荣誉院士称号，[12]他也因此成为少数几位获此荣誉的香港艺人之一[13]。刘德华笃信佛教，法号“慧果”，热心公益，时常参与慈善活动。2008年，刘德华获香港特别行政区政府委任为太平绅士[14]。2010年4月23日，刘德华获任中国残疾人福利基金会理事并担任副理事长[15]。2013年12月8日，他又当选香港残疾人奥委会暨伤残人士体育协会副会长[16]。2010年5月2日，刘德华获颁第十二届“世界杰出华人奖”同时获颁授加拿大纽奔驰域蓝仕桥大学荣誉博士学位[17]。"
    # zxy = "张学友（英语：Jacky Cheung Hok Yau，1961年7月10日－），生于香港，祖籍天津[4]，是一位在亚洲地区和华人社会具有影响力的实力派歌手和著名电影演员，香港乐坛“四大天王”之一[5][6][7]，大中华区以至亚洲的乐坛巨星，在华语地区享有“歌神”美誉[8][9][10]。1990年代中为张学友事业巅峰时期，当年（1995年）他的年唱片销量曾名列世界第二位，仅排在美国传奇歌手迈克尔·杰克逊之后，[11][12]高于第三位的麦当娜，[13]因他的唱片高销量而进入了环球唱片美国总公司在2000年选出的1990年代巨星名人堂。[14]当时他亦曾被美国《时代周刊杂志》列入亚洲最有影响力的50位人物之一。截至2000年，他的唱片全球累计总销量已突破60,000,000张[15][16]，并在香港坐拥超过70首冠军歌曲；于乐坛影响力甚大。张学友擅长演绎多种音乐风格，近年尝试R&B乐风和爵士乐，甚至以歌剧唱法来诠释乐曲，同样受到乐迷认同.电影演出方面，张学友目前为止作为主角共拍摄近60部电影，其饰演的人物不少给观众以及电影专业人士留下深刻印像，他在喜剧、剧情片以及文艺片方面颇有造诣，多次获香港电影金像奖以及台湾电影金马奖的最佳男主角和最佳男配角提名，并在1989年获得香港电影金像奖的最佳男配角奖以及1990年的台湾电影金马奖的最佳男配角奖[17]。2002年更是凭借电影《男人四十》一举摘得印度国际电影节的影帝称号.除演艺事业外，张学友热心公益慈善。1998年当选香港十大杰出青年，1999年当选世界十大杰出青年。2003至2009年担任香港演艺人协会副会长。"
    # text_dict = {"刘德华": ldh, "张学友": zxy}


    u = """安徽一考点疑听力设备故障 学生拒绝交卷
新京报快讯 今日(6月8日)下午，安徽省芜湖市田家炳中学考点高考英语听力播放设备疑出现故障，无法正常播音，大量家长围堵校门要求校方给出解决方案。今日晚间，芜湖市政府应急办工作人员称市主要领导已赶赴现场，相关调查程序将连夜启动。

高考考点疑听力设备故障

一名不愿具名的考生告诉新京报记者，今日下午其在参加最后一科听力考试时，播放设备出现故障，对外不断发出“吱吱”的声音，只有几个对话音节能够听清，“我听力很好，但是这次完全是靠蒙写完的。”

芜湖市一中的一名考生表示，从试听开始，喇叭内的噪音就一直很重，自己努力分辨还是没能听清。据他回忆，考场内不止一名学生向监考老师表达了重听要求，但是没有得到确切答复。

据路人李先生反映，其在下午6时左右路过田家炳中学，中学附近道路上堵满了学生家长，银湖路和长江路交通停滞，“不少学生和家长一边哭一边试图讨要说法。”

据应试学生介绍，今日下午的英语考试为安徽省2015年高考的最后一门科目。听力于下午3点准时开始，播放时长约20分钟，田家炳中学此次设有30多个考场，千余考生受到影响。

据了解，在去年高考期间，6月8日下午15时许，芜湖市南瑞实验中学高考考点英语考试听力测试时，高考英语听力磁带曾突发故障，磁带断裂无法进行英语听力部分考试，考场内近千名考生受到影响。

应急办：相关调查程序将连夜启动


据一名学生家长反映，截至今晚22时许，仍有近千学生和家长聚集在田家炳中学校内讨要说法，此前曾有相关领导邀请家长代表入内对话，称将请专家来鉴定是否存在听力设备故障。

多名目击者称，现仍有两个班级考生不愿交卷退出考场，在教室内静坐等待有关部门具体答复。

今日晚间，芜湖市政府应急办工作人员通报称，芜湖市委、市政府接报后，主要领导和分管领导第一时间赶赴现场，听取考生和家长的反映，积极与家长对话，做好维稳相关工作;安徽省教育厅的相关负责同志接报后亦赶赴芜湖，决定连夜启动调查程序，采取相关切实措施，维护考生权益。

据上述工作人员称，目前政府方面已安排了晚餐和茶水供应，来稳定家长和考生情绪，并积极开展教育说服工作，目前校内情况稳定。"""

    str=Gist().get_gist_str(u)
    print str

    v = """河北沧州肃宁县发生特大枪击案致4死5伤
【河北肃宁发生特大枪击案已致4死5伤 两干警围捕时牺牲】据通报，今日凌晨，付佐乡一村民刘双瑞手持双管猎枪对其住所周边村民进行枪击。据@燕赵都市报 截至目前，已造成4死5伤，死者中，两人为村民，两人为公安干警。刘双瑞被警方当场击毙。据称，刘长期患有精神分裂症。

燕赵都市网沧州电 6月9日凌晨，肃宁县发生特大枪击案，目前燕赵都市报记者获得最新消息，案件已造成4死5伤，包括肃宁县公安局政委在内的两名干警牺牲。

据肃宁县付佐乡政府通报称，6月9日凌晨，付佐乡西石宝村村民刘双瑞手持双管猎枪对其住所周边村民进行枪击。事件发生后，付佐乡第一时间启动突发事件处理机制，积极采取措施，及时通知周边各村做好防备，控制事态发展。早5点，县委副书记李国钧、县委常委政法委书记张占山，在付佐乡紧急组织有关部门召开会议，部署相关工作。一方面，全力抢救受伤人员；另一方面，紧急联系外援严格控制犯罪嫌疑人。截至6月9日6时，案件共造成三死五伤。目前，犯罪嫌疑人正在全力围捕。


通报称，犯罪嫌疑人刘双瑞，男，55岁，长期患有精神分裂症。三名死者分别为：刘新愿，男，40多岁，村民务农；刘广春，男，70多岁，村民务农；袁帅，男，30多岁，公安干警。五名伤者分别为：李素霞(刘广春之妻)，女，70多岁，村民务农，重伤；刘玉民(刘新愿之哥)，男，50多岁，村民务农，重伤；刘金山，男，50多岁，村民务农，轻伤；王涛，男，43岁，公安干警，轻伤；李金维，男，42岁，公安干警，重伤。其中，刘金山、刘玉民、李素霞、李金维送往北京301医院治疗，王涛送往沧州市中心医院治疗。

上午10时30分，燕赵都市报记者得到最新消息，肃宁县公安局政委薛永清在围捕犯罪嫌疑人过程中牺牲，目前案件共造成4死5伤。"""

    w = """美军2艘两栖舰进入中国南海东海(图)

6月5日，美国海军两艘两栖攻击舰LHD6“好人理查德”号与LHD2“埃塞克斯”号，分别进入中国东海海域与香港水域。其中，黄蜂级两栖攻击舰“埃塞克斯”号将停靠香港休整。“好人理查德”号与两栖船坞登陆舰“阿什兰”号（LSD48）则在东海海域航行，执行第7舰队巡航任务。
"""

    m = """长江沉船现场清理完成 专家将登船调查沉船原因
记者从“东方之星”客船翻沉事件前方指挥部获悉，6月8日上午，现场搜寻人员又搜寻到2名遇难者遗体，遇难人数升至434人，加上生还者14人，目前失踪人员还剩8人。目前，对“东方之星”失踪人员搜寻工作仍在持续进行。专家将登船对事件原因进行调查。

6月8日上午，“东方之星”客船现场搜寻人员又搜寻到2具遇难者遗体。截止到昨天上午11时，共搜寻到434具遇难者遗体。湖北省军区某舟桥旅对“东方之星”船体进行了全面的清理工作，截至6月8日，已经清理遗物1500余件，杂物200余吨。

昨天，工作人员还将“东方之星”号客轮边缘拉起警戒线，准备对船体进行封存。由长江航务管理局、荆州市政府、重庆市政府及船方代表等组成验收组，对“东方之星”号客轮现场清理工作完成情况进行验收，验收完毕后，对船体进行封存。

昨天下午，联合验收组经过两个小时的全面细致检查后确认清理完毕，各方代表分别在验收清单上签字。至此，“东方之星”现场排查清理工作全部完成。

据了解，此前获救的“东方之星”号船长、轮机长已被控制并展开讯问。相关专家还将在船上搜寻工作完成后登船调查。专家将登船分别对船舱整体结构、气象条件以及周边水域水文条件进行调查，解答事发前是否有天气预警，为何有船选择抛锚而“东方之星”却选择续航等疑问。

昨天上午10时20分左右，生还者江庚、陈书涵从监利县人民医院出院，这是“东方之星”客船翻沉事件第一批经治疗康复后出院的生还者。

目前，上海96名遇难者的家属全部抵达湖北监利县，已有20名遇难者和其家属DNA比对成功，家属已经确认，并认领了遇难者的随身遗物。"""

    n = """长江倾覆客轮幸存者:曾于汶川地震幸运逃生
“没想到暴风雨的夜里巡查渔船救起一个人。”昨日，监利县三洲镇复兴村5组村民王盛才说。

57岁的王盛才家离长江不到300米，距沉船水域20余公里之遥。

1日，跟平常一样，天一黑，王盛才便早早睡下。

2日凌晨4时许，王盛才醒来发现，客厅有不少积水，屋外下着大雨。想到自家的机动木船停靠在江边，他拿着强光电筒出门，来到江边，发现木船已不见踪影。江边风太大，王盛才准备掉头回家，这时隐约听见“救命”声。

王盛才拿着电筒循声扫去，发现一身穿花衬衣、颈挎救生圈的男子瘫在岸边。“船翻了。”男子冻得发抖。王盛才赶紧把男子带回家，一边让家人找衣服，一边报警。

由于信号不好，王盛才的儿子和闻讯赶来的村支书袁华清连打了十几次，终于拨通了荆州市公安局指挥中心报警电话。


这名男子叫余正伟，重庆人，与妻子刚刚承包下“东方之星”游轮上的小卖部，一共随船跑了三趟。

据余正伟讲，1日21时许，他在舱内听到外面风雨交加，急匆匆赶到甲板上去收衣服，不料刚刚走上甲板，船舶突然大角度倾斜，他整个人被甩了出去。幸运的是，情急之下，他抓到了一个救生圈。落水后，余正伟紧紧地抱住救生圈。经过长达7小时的漂流后才被发现。“我和妻子都是汶川地震的幸存者，我是又逃过一劫。”余正伟对王盛才说。

记者了解到，目前余正伟已离开监利返回重庆，两名家属则留守在监利等待其妻消息。"""

    text_dict = {"听力设备故障": u, "枪案":v,"美舰找事":w,"沉船":m,"幸存者":n}
    a = Gist().get_gist(text_dict)














