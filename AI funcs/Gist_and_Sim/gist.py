#-*- encoding:utf-8 -*-
"""
Created on May 30, 2015
@author: Gavin
"""

import codecs
from TextRank4ZH.textrank4zh import TextRank4Keyword, TextRank4Sentence
import sys

reload(sys)
sys.setdefaultencoding('utf-8')
import jieba
from gensim import corpora, models, similarities

class Gist:

    def __init__(self, stop_words_file='TextRank4ZH/stopword.data'):
            self.stop_words_file=stop_words_file
            self.tr4w = TextRank4Keyword(self.stop_words_file)  # 导入停止词

    def get_keyword(self, text):
            self.tr4w = TextRank4Keyword(self.stop_words_file)  # Import stopwords
            #Use word class filtering，decapitalization of text，window is 2.
            self.tr4w.train(text=text, speech_tag_filter=True, lower=True, window=2)
            # 20 keywords The min length of each word is 1.
            self.wresult = ' '.join(self.tr4w.get_keywords(20, word_min_len=1))
            print self.wresult
            return self.wresult

    def get_keyphrase(self, text):
            self.tr4w = TextRank4Keyword(self.stop_words_file)  # Import stopwords
            #Use word class filtering，decapitalization of text，window is 2.
            self.tr4w.train(text=text, speech_tag_filter=True, lower=True, window=2)
            #Use 20 keywords for contructing phrase, the phrase occurrence in original text is at least 2.
            self.presult = ' '.join(self.tr4w.get_keyphrases(keywords_num=20, min_occur_num= 2))
            print self.presult
            return self.presult

    def get_gist(self, text_dict = {}):
        self.gresult = {}
        for key, value in text_dict.iteritems():
            # # self.tr4w = TextRank4Keyword(self.stop_words_file)  # 导入停止词
            # #使用词性过滤，文本小写，窗口为2
            # self.tr4w.train(text=value, speech_tag_filter=True, lower=True, window=2)
            # # 20个关键词且每个的长度最小为1
            # self.wresult = ' '.join(self.tr4w.get_keywords(20, word_min_len=1))
            # # 20个关键词去构造短语，短语在原文本中出现次数最少为2
            # self.presult = ' '.join(self.tr4w.get_keyphrases(keywords_num=20, min_occur_num= 2))
            self.tr4s = TextRank4Sentence(self.stop_words_file)
            # 使用词性过滤，文本小写，使用words_all_filters生成句子之间的相似性
            self.tr4s.train(text=value, speech_tag_filter=True, lower=True, source = 'all_filters')
            self.gresult.update({key: (' '.join(self.tr4s.get_key_sentences(num=1)))})
            print key+":"+(self.gresult[key])

        return self.gresult

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











