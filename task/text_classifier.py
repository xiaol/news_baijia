#coding=utf-8
import requests
import json
import time


def get_category_by_tencent(text):
    categoryList = []
    headers = {
           "S-Openid": "114242123", "S-Token": "qlgpbnkxoa"}
    response = requests.post('http://api.nlp.qq.com/text/classify', data={'content': text}, headers=headers)
    if response['ret_code'] == 0:
        categoryList = response['classes']
    else:
        print "failed to category"
    return categoryList


def get_token():
    response = requests.post('http://api.nlp.qq.com/get_token.cgi?user=114242123&key=qlgpbnkxoa')
    response['token']

def get_category_by_hack(text):
    categoryList = []
    body_data = {"content": text}
    try:
        response = requests.post('http://nlp.qq.com/public/wenzhi/api/common_api.php', data={'url_path': 'http://10.209.0.215:55000/text/classify','body_data':json.dumps(body_data)})
        time.sleep(0.5)
        content = json.loads(response.content)
        if content['ret_code'] == 0:
            categoryList = content['classes']
        else:
            print "failed to category"
    except Exception,e:
        return categoryList

    return categoryList


if __name__ == '__main__':
    get_category_by_tencent('刘强东与奶茶妹妹的婚纱照冲淡了翻新手机的丑闻?')
    #get_category_by_hack('妻子曝阿兰两周后返广州复出在即只为亚冠夺冠')
    #get_category_by_hack('故宫回应"女模裸照"：拍摄是有计划、有准备的')
    #get_category_by_hack('俄外交部：俄期望能按期就伊朗核计划达成协议')
    #get_category_by_hack('媒体盘点：李克强出访拉美带来的签证便利')
    #get_category_by_hack('可米小子成员安钧璨被曝因肝癌去世')
    #get_category_by_hack('安钧璨生前乐观交好小S安以轩系大S红娘')
    #get_category_by_hack('美媒曝FBI正在调查布拉特被捕人员将提供线索')
    #get_category_by_hack('河南将整治人员密集场所消防安全重查彩钢板建筑')
    #get_category_by_hack('国产厂商转战799元价位手机或将迎来降价潮')
    #get_category_by_hack('广东举行发呆比赛 小朋友夺前三名')

