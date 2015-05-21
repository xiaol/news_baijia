#coding=utf-8
__author__ = 'Ivan liu'


import time
import pymongo
import datetime
from pymongo.read_preferences import ReadPreference
conn = pymongo.MongoReplicaSetClient("h44:27017, h213:27017, h241:27017", replicaSet="myset",
                                                             read_preference=ReadPreference.SECONDARY)
'''
chemicalBond
elementName
createTime
'''


def elementary(elements):
    results_elementary = {'elements': [], 'ions': [], 'covalents': []}
    for element in elements:
        if element['chemicalBond'] == 'element':  #element 单质  double bond 双键  ionic bond 离子键 covalent bond 共价键
            results_elementary['elements'].append(element['elementName'])
        elif element['chemicalBond'] == 'ionic bond':
            results_elementary['elements'].append([element['atomName'], element['ionicName']])

    return results_elementary


def construct_element(chemical_bond, element_name):
    now = datetime.datetime.now()
    conn['news_ver2']['elementary'].update({'elementName': element_name},
                                           {'chemicalBond': chemical_bond, 'elementName': element_name, 'createTime': now}, upsert=True)


def construct_ionic(ionic_name, atom_name):
    now = datetime.datetime.now()
    conn['news_ver2']['elementary'].update({'atomName': atom_name},
        {'chemicalBond': 'ionic bond', 'ionicName': ionic_name, 'atomName': atom_name, 'createTime': now}, upsert=True)


def construct_covalent(atom_name_a, atom_name_b):
    now = datetime.datetime.now()
    conn['news_ver2']['elementary'].update({'atomNameA': atom_name_a},
            {'chemicalBond': 'covalent bond', 'atomNameA': atom_name_a, 'atomNameB': atom_name_b, 'createTime': now}, upsert=True)

if __name__ == '__main__':
    #construct_element('element', '武继长')
    #construct_element('element', '网购火车票')
    #construct_element('element', '韩正')
    construct_element('element', '省委书记')
    construct_element('element', '田源')
    construct_element('element', '拜仁')
    construct_element('element', '３６０')
    construct_element('element', '政法委书记')
    construct_element('element', '习近平')
    construct_element('element', '苏文茂')
    construct_element('element', '成龙')
    construct_element('element', '亚冠')
    construct_element('element', '小米')
    construct_element('element', '震中分布图')
    construct_element('element', '吴镇宇')
    #construct_element('element', 'MVP')
    #construct_ionic('IS', '先知漫画展')
    construct_ionic('三大评测机构', '杀软')
    construct_ionic('生日', '谢娜')
    construct_ionic('烟草消费税', '烟草税')
    construct_ionic('冯绍峰', '倪妮')
    construct_ionic('范冰冰', '张馨予')
    construct_ionic('范冰冰', '王思聪')

