#coding=utf-8
import requests
import json


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

def get_category_by_hack(text):
    categoryList = []
    body_data = {"content": text}
    response = requests.post('http://nlp.qq.com/public/wenzhi/api/common_api.php', data={'url_path': 'http://10.209.0.215:55000/text/classify','body_data':json.dumps(body_data)})
    content = json.loads(response.content)
    if content['ret_code'] == 0:
        categoryList = content['classes']
    else:
        print "failed to category"
    return categoryList


if __name__ == '__main__':
    #get_category_by_tencent('刘强东与奶茶妹妹的婚纱照冲淡了翻新手机的丑闻?')
    get_category_by_hack('刘强东与奶茶妹妹的婚纱照冲淡了翻新手机的丑闻?')

