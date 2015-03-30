try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser

import os

# print os.getcwd()

cf = ConfigParser.ConfigParser()
pwd = os.getcwd()
pwd_2 = pwd.split('/')
pwd_2 = pwd_2[:-1]
pwd_2 = '/'.join(pwd_2)

try:
    with open(os.path.join(pwd,'controller/config/config.ini'),'r') as configfile:
        cf.readfp(configfile)
except IOError:
    with open(os.path.join(pwd_2,'controller/config/config.ini'),'r') as configfile:
        cf.readfp(configfile)

# cf.read("config.ini")



def getcfg(session, key):
    """
    :param session:
    :param key:
    :return: the value in config.ini

    """
    return cf.get(session, key)

if __name__ == '__main__':
    print cf.get("db-h39","db_port")
