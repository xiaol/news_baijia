import sys
import codecs
import json
import datetime
import threading
import thread
import logging
from logging.handlers import RotatingFileHandler

try:
    import Global
except Exception, e:
    pass
    
try:
    import web
except Exception, e:
    pass

    
_loggers = {}
_params = {}

def openlog(filename, level=logging.INFO, name='default', part_id=1):

    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    FORMAT = '%(levelname)s %(asctime)s T%(thread)d %(part)s %(message)s'
    formatter = logging.Formatter(FORMAT)
    
    handler = RotatingFileHandler(filename, backupCount=10, maxBytes=1000*1000*10)
    #handler.doRollover()
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    _loggers[name] = logger

    _params['part_id'] = part_id
    
    info('logging start')
 
    #logging.basicConfig(filename=filename, format=FORMAT, level=level)
    
def get_logger(name):
    return debug(name), info(name), error(name)
        
def encode_safe(uni_str, encoding='utf-8'):
    if type(uni_str) == unicode:
        return uni_str.encode(encoding)
    elif type(uni_str) == str:
        return uni_str
    else:
        try:
            ss = json.dumps(uni_str, ensure_ascii=False).encode('utf-8')
        except Exception,e:
            ss = str(uni_str)
        return ss
        


def construct_msg(name, *args):    
   
    account = ''
    nick = ''
    controller = ''
    d = {'part': _params.get('part_id', 1)}
    msg = ' '.join([encode_safe(x) for x in args])
    return msg, d

 
def info(name):   
    def _info(*args):
        msg, d = construct_msg(name, *args)
        L = _loggers.get(name)
        if L != None:
            L.info(msg, extra=d)
            
    return _info

def debug(name):    
    def _debug(*args):
        msg, d = construct_msg(name, *args)
        L = _loggers.get(name)
        if L != None:
            L.debug(msg, extra=d)
    return _debug

def error(name):    
    def _error(*args):
        msg, d = construct_msg(name, *args)
        L = _loggers.get(name)
        if L != None:
            L.error(msg, extra=d)
    return _error
        
INFO = info('default')
DBG = debug('default')
ERR = error('default')
'''
def INFO(*s): print s
def ERR(*s): print s
def DBG(*s): pass
   
'''
            
if __name__ == '__main__':
    pass
    # openlog('xxx.log', logging.DEBUG)
    # INFO('hello', 'xx')
    # INFO('hello', 'xx', '中asdf文', u'中asdf文', {u'x二个': '中文', 'y一个': u'中文'})
    # DBG('hello', 'xx', '中asdf文', u'中asdf文', {u'x二个': '中文', 'y一个': u'中文'})
    # ERR('hello', 'xx', '中asdf文', u'中asdf文', {u'x二个': '中文', 'y一个': u'中文'})
