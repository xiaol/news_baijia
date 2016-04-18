# coding=utf-8
__author__ = 'yangjiwen'
import re
import jieba
import sys
from analyzer import jieba

def duplicate_docs_check(domain_events):
    events = []
    for event in domain_events:
        if "sentence"  not in event.keys():
            text = event["text"]
            paragraph_list = text.split('\n')
            sentence_dict = {}
            sentence_cut_dict = {}
            paragraph_dict = {}
            i = 0
            for paragraph_elem in paragraph_list:
                if len(paragraph_elem)<=4:
                    continue
                sentence_dict[str(i)], sentence_cut_dict[str(i)] = extractSentenceBlock(paragraph_elem)
                paragraph_dict[str(i)] = paragraph_elem
                i = i + 1
            event["sentence"] = sentence_dict
            event["sentence_cut"] = sentence_cut_dict
            event["paragraph"] = paragraph_dict
        events.append(event)
    duplicate_result = {}

    for event in [events[0]]:
        main_event = event
        url = main_event["_id"]
        result = {}
        for event_elem in events:
            if url == event_elem["_id"]:
                continue
            duplicate_result, result = compare_doc_is_duplicate(main_event, event_elem, duplicate_result, result)
    return duplicate_result

    #     common_opinion, self_opinion = extract_opinion(main_event,duplicate_result)
    #     event["self_opinion"] = self_opinion
    #     event["common_opinion"] = common_opinion
    #
    #     duplicate_result_by_paragraph = compute_match_ratio_sentence_to_paragraph(result)
    #     min_match_ratio, one_paragraph_by_article, total_paragraph_by_article = extract_opinon_by_match_ratio(main_event, duplicate_result_by_paragraph)
    #     if min_match_ratio<0.39:
    #         event["self_opinion"] = one_paragraph_by_article
    #     else:
    #         event["self_opinion"] = ''
    #     # f = open("/Users/yangjiwen/Documents/yangjw/duplicate_case.txt","a")
    #     # if "eventId" in main_event.keys():
    #     #     f.write("event_id:"+str(main_event["eventId"]).encode('utf-8')+'\n\n'
    #     #             "新闻url:"+str(main_event["_id"]).encode('utf-8')+'\n\n'
    #     #             "独家观点:"+str(main_event["self_opinion"]).encode('utf-8')+'\n\n'
    #     #             # "共同观点:"+str(common_opinion).encode('utf-8')+'\n\n'
    #     #             "----------------------------------------------------"
    #     #             )
    #     #     f.close()
    # for event in events:
    #     main_event = event
    #     url = main_event["_id"]
    #     result_total = []
    #     result = {}
    #     result["url"] = url
    #     result["self_opinion"] = []
    #     result["common_opinion"] = []
    #     for event_elem in events:
    #         if url == event_elem["_id"]:
    #             continue
    #         else:
    #             if len(event_elem["self_opinion"])>=5:
    #                 print "self_opinion:%s" % event_elem["self_opinion"].encode('utf-8')
    #                 print "url:%s" % event_elem["_id"]
    #                 result["self_opinion"].append({"self_opinion": event_elem["self_opinion"].encode('utf-8'), "url": event_elem["_id"]})
    #             if len(event_elem["common_opinion"])>5:
    #                 print "common_opinion:%s"%event_elem["common_opinion"].encode('utf-8')
    #                 print "url:%s" % event_elem["_id"]
    #                 result["common_opinion"].append({"common_opinion": event_elem["common_opinion"].encode('utf-8'), "url": event_elem["_id"]})
    #     result_total.append(result)
    # return result_total

def extract_opinion(main_event, result):
    sentence = main_event["sentence"]
    common_opinion=''
    self_opinion = ''
    for paragraph_key in sorted(sentence.keys()):
        self_opinion_flag = False
        common_opinion_flag = False
        paragraph_value = sentence[paragraph_key]
        if paragraph_key in result.keys():
            for sentence_key in sorted(paragraph_value.keys()):
                sentence_value = paragraph_value[sentence_key]
                if sentence_key in result[paragraph_key].keys():
                    print type(sentence_value)
                    common_opinion=common_opinion + sentence_value + u'。'
                    common_opinion_flag = True
                else:
                    self_opinion = self_opinion + sentence_value + u'。'
                    self_opinion_flag = True

        else:
            for sentence_key in sorted(paragraph_value.keys()):
                sentence_value = paragraph_value[sentence_key]
                self_opinion = self_opinion + sentence_value + u'。'
                self_opinion_flag = True
        if  self_opinion_flag:
            self_opinion = self_opinion + '\n'
        if  common_opinion_flag:
            common_opinion = common_opinion + '\n'

    return  common_opinion, self_opinion

def extract_opinon_by_match_ratio(main_event, duplicate_result_by_paragraph):
    total_paragraph_by_article = {}
    one_paragraph_by_article = ''
    paragraph = main_event["paragraph"]
    min_match_ratio = 1
    min_paragraph_key = '0'
    for paragraph_key, paragraph_value in paragraph.items():
        total_paragraph_by_article[paragraph_key] = {}
        total_paragraph_by_article[paragraph_key]["content"] = paragraph[paragraph_key]
        if paragraph_key in duplicate_result_by_paragraph.keys():
            total_paragraph_by_article[paragraph_key]["match_ratio"] = duplicate_result_by_paragraph[paragraph_key]
        else:
            total_paragraph_by_article[paragraph_key]["match_ratio"] = 1
        if  total_paragraph_by_article[paragraph_key]["match_ratio"] < min_match_ratio and is_normal_info(paragraph[paragraph_key]):
            min_match_ratio = total_paragraph_by_article[paragraph_key]["match_ratio"]
            min_paragraph_key = paragraph_key
            # print "min_paragraph_key_change"

    one_paragraph_by_article = paragraph[min_paragraph_key]


    return min_match_ratio,one_paragraph_by_article, total_paragraph_by_article

def compute_match_ratio_sentence_to_paragraph(result):
    duplicate_result_by_paragraph = {}

    for paragraph_key, paragraph_value in result.items():
        avg_match_ratio_by_paragraph = 1
        sum_match_ratio_by_paragraph = 0
        sentence_num = len(paragraph_value)
        for sentence_key, sentence_value in paragraph_value.items():
            top_match_ratio_by_sentence = 0
            for sentence_value_elem in sentence_value:
                if  sentence_value_elem["match_ratio"] > top_match_ratio_by_sentence:
                    top_match_ratio_by_sentence = sentence_value_elem["match_ratio"]
            sum_match_ratio_by_paragraph = sum_match_ratio_by_paragraph + top_match_ratio_by_sentence
        if sentence_num > 0:
            avg_match_ratio_by_paragraph = sum_match_ratio_by_paragraph*1.0/sentence_num

        duplicate_result_by_paragraph[paragraph_key] = avg_match_ratio_by_paragraph
    return duplicate_result_by_paragraph


def compare_doc_is_duplicate(main_event, event_elem, duplicate_result, result):
    sentence_cut = main_event["sentence_cut"]
    paragraph = event_elem["paragraph"]
    url = main_event["_id"]
    for paragraph_key, paragraph_value in sentence_cut.items():
        for sentence_key, sentence_value in paragraph_value.items():
            top_match_ratio = 0.0
            top_match_paragraph_id = "-1"
            keyword_num = len(sentence_value)
            # if keyword_num <=5:
            #     continue
            for compare_paragraph_key, compare_paragraph_value in paragraph.items():
                match_num = 0
                for sentence_keyword in sentence_value:
                    compare_result = compare_paragraph_value.find(sentence_keyword)
                    if compare_result >= 0:
                        match_num = match_num + 1
                if keyword_num < 2:
                    match_ratio = 0
                else:
                    match_ratio = match_num / (keyword_num * 1.0)
                if match_ratio > top_match_ratio:
                    top_match_ratio = match_ratio
                    top_match_paragraph_id = compare_paragraph_key
            if top_match_ratio > 0.8:
                # f = open("/Users/yangjiwen/Documents/yangjw/duplicate_case.txt","a")
                # f.write("mainurl:"+str(main_event["_id"]).encode('utf-8')
                #             +"main_paragraph_id:"+str(paragraph_key).encode('utf-8')
                #             +"main_sentence_id:"+str(sentence_key).encode('utf-8')
                #             +"sentence_content:"+str(main_event["sentence"][paragraph_key][sentence_key]).encode('utf-8')
                #             +"sentence_cut_content:"+str(','.join(sentence_value)).encode('utf-8')
                #             +"relateurl:"+str(url).encode('utf-8')
                #             +"realte_paragraph_id:"+str(top_match_paragraph_id).encode('utf-8')
                #             +"match_ratio:"+str(top_match_ratio).encode('utf-8')
                #             +"relate_paragraph_content"+str(paragraph[top_match_paragraph_id]).encode('utf-8')
                #             )


                # f.write("*"+str(main_event["_id"]).encode('utf-8')
                #             +"*"+str(paragraph_key).encode('utf-8')
                #             +"*"+str(sentence_key).encode('utf-8')
                #             +"*"+str(main_event["sentence"][paragraph_key][sentence_key]).encode('utf-8')
                #             +"*"+str(','.join(sentence_value)).encode('utf-8')
                #             +"*"+str(url).encode('utf-8')
                #             +"*"+str(top_match_paragraph_id).encode('utf-8')
                #             +"*"+str(top_match_ratio).encode('utf-8')
                #             +"*"+str(paragraph[top_match_paragraph_id]).encode('utf-8')
                #             )
                #
                #
                # f.write('\n')
                # f.close()
                if paragraph_key not in duplicate_result.keys():
                    duplicate_result[paragraph_key] = {}
                if sentence_key not in duplicate_result[paragraph_key].keys():
                    duplicate_result[paragraph_key][sentence_key] = {}
                    if "text" not in duplicate_result[paragraph_key][sentence_key].keys():
                        duplicate_result[paragraph_key][sentence_key]["text"] = main_event["sentence"][paragraph_key][sentence_key]
                    if "relate" not in duplicate_result[paragraph_key][sentence_key].keys():
                        duplicate_result[paragraph_key][sentence_key]["relate"] = [{"_id": event_elem["_id"], "paragraph_id": top_match_paragraph_id, "match_ratio": top_match_ratio, "text": event_elem["paragraph"][top_match_paragraph_id]}]
                    else:
                        duplicate_result[paragraph_key][sentence_key]["relate"].append({"_id": event_elem["_id"], "paragraph_id": top_match_paragraph_id, "match_ratio": top_match_ratio, "text": event_elem["paragraph"][top_match_paragraph_id]})

            if paragraph_key not in result.keys():
                result[paragraph_key] = {}
            if sentence_key not in result[paragraph_key].keys():
                result[paragraph_key][sentence_key] = {}
                result[paragraph_key][sentence_key]["text"] = ""
                if "relate" not in result[paragraph_key][sentence_key].keys():
                    result[paragraph_key][sentence_key]["relate"] = [{"url": url, "paragraph_id": top_match_paragraph_id, "match_ratio": top_match_ratio}]
                else:
                    result[paragraph_key][sentence_key]["relate"].append({"url": url, "paragraph_id": top_match_paragraph_id, "match_ratio": top_match_ratio})
    return duplicate_result, result


def extractSentenceBlock(doc):
    SENTENCE_SEP = re.compile(ur'[。\n!！]')
    result = {}
    result_cut = {}
    doc_array=re.split(SENTENCE_SEP, doc.encode('utf8').decode("utf8"))
    i = 0
    for elem in doc_array:
        if len(elem) <= 5:
            continue
        result[str(i)] = elem.strip()
        keyword = set()
        keyword = {word for word in jieba.cut_with_stop(elem.strip())}
        keyword_list = list(keyword)
        result_cut[str(i)] = keyword_list
        # result.append(elem.strip())
        i = i + 1
    return result, result_cut

def is_normal_info(paragraph):
    paragraph = paragraph
    pattern=re.compile(ur'http[:：]|[[【]|[]】]|扫描二维码|来源[:：]|编辑[:：]|作者[:：]|发布[:：]|正文已结束|字号[:：]|未经授权禁止转载')
    result = re.search(pattern, paragraph)
    if result:
        return False
    else:
        return True

def data_tranfer(domain_events):
    i =0
    result = []
    for elem in domain_events:
        dict = {"_id": i, "text": elem}
        result.append(dict)
        i = i + 1
    return result

def compare_doc_is_duplicate_copy(main_event, event_elem, duplicate_result, result):
    sentence_cut = main_event["sentence_cut"]
    paragraph = event_elem["paragraph"]
    url = main_event["_id"]
    for paragraph_key, paragraph_value in sentence_cut.items():
        for sentence_key, sentence_value in paragraph_value.items():
            top_match_ratio = 0.0
            top_match_paragraph_id = "-1"
            keyword_num = len(sentence_value)
            # if keyword_num <=5:
            #     continue
            for compare_paragraph_key , compare_paragraph_value in paragraph.items():
                match_num = 0
                for sentence_keyword in sentence_value:
                    compare_result = compare_paragraph_value.find(sentence_keyword)
                    if compare_result >= 0:
                        match_num = match_num + 1
                if keyword_num < 2:
                    match_ratio = 0
                else:
                    match_ratio = match_num / (keyword_num * 1.0)
                if match_ratio > top_match_ratio:
                    top_match_ratio = match_ratio
                    top_match_paragraph_id = compare_paragraph_key
            if top_match_ratio > 0.8:
                if url not in duplicate_result.keys():
                    duplicate_result[url] = {}
                if paragraph_key not in duplicate_result[url].keys():
                    duplicate_result[url][paragraph_key] = {}
                if sentence_key not in duplicate_result[url][paragraph_key].keys():
                    duplicate_result[url][paragraph_key][sentence_key] = []
                    duplicate_result[url][paragraph_key][sentence_key] = [{"url": url, "paragraph_id": top_match_paragraph_id, "match_ratio": top_match_ratio}]

                else:
                    duplicate_result[url][paragraph_key][sentence_key].append({"url": url, "paragraph_id": top_match_paragraph_id, "match_ratio": top_match_ratio})

            if paragraph_key not in result.keys():
                result[paragraph_key] = {}
            if sentence_key not in result[paragraph_key].keys():
                result[paragraph_key][sentence_key] = []
                result[paragraph_key][sentence_key] = [{"url": url, "paragraph_id": top_match_paragraph_id, "match_ratio": top_match_ratio}]

            else:
                result[paragraph_key][sentence_key].append({"url": url, "paragraph_id": top_match_paragraph_id, "match_ratio": top_match_ratio})
    return duplicate_result, result



if __name__ == '__main__':

    domain_events = [u"今日，法晚记者从河南警方获悉，北京和颐酒店女子遇袭案发生后，河南公安厅全力配合北京警方抓捕逃犯，由李法正副厅长坐镇指挥，整个抓捕过程保密性很强，行动十分迅速。\n今日，法晚记者从河南警方获悉，北京和颐酒店女子遇袭案发生后，五名嫌犯逃窜到了原籍河南省许昌市襄城县汾陈乡。北京警方调查得知后，随即向河南省公安厅发出了协助抓捕的请求。河南省公安厅的主要领导对这起案件非常重视，派出了负责打击刑事犯罪和网络安全保卫工作的李法正副厅长坐镇指挥。这次抓捕行动由许昌市公安局刑侦支队统一调配，在掌握了犯罪嫌疑人李某的逃窜轨迹后，襄城县刑警队迅速出动，将李某抓获归案。许昌市、襄城县公安机关很多重要岗位的警官直到破案才知道原来自己的同事也参与了此次行动。此前，北京警方回应网友对破案速度的质疑时称：此次抓捕行动需要跨省、跨警种的合作，两地警方的协调、沟通工作就花费了一部分时间。"
                     ,u"法晚深度即时（稿件统筹 朱顺忠 实习生 尚妍）今日，法晚记者从河南警方获悉，北京和颐酒店女子遇袭案发生后，河南公安厅全力配合北京警方抓捕逃犯，由李法正副厅长坐镇指挥，整个抓捕过程保密性很强，行动十分迅速。\n今日，法晚（微信公号ID：fzwb_52165216）记者从河南警方获悉，北京和颐酒店女子遇袭案发生后，五名嫌犯逃窜到了原籍河南省许昌市襄城县汾陈乡。北京警方调查得知后，随即向河南省公安厅发出了协助抓捕的请求。河南省公安厅的主要领导对这起案件非常重视，派出了负责打击刑事犯罪和网络安全保卫工作的李法正副厅长坐镇指挥。这次抓捕行动由许昌市公安局刑侦支队统一调配，在掌握了犯罪嫌疑人李某的逃窜轨迹后，襄城县刑警队迅速出动，将李某抓获归案。许昌市、襄城县公安机关很多重要岗位的警官直到破案才知道原来自己的同事也参与了此次行动。此前，北京警方回应网友对破案速度的质疑时称：此次抓捕行动需要跨省、跨警种的合作，两地警方的协调、沟通工作就花费了一部分时间。"]

    result = data_tranfer(domain_events)
    print duplicate_docs_check(result)
    # print (extract_opinion(article))
