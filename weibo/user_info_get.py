__author__ = 'jianghao'

import time
from task import requests_with_sleep as requests

ACCESS_TOKEN = "2.004t5RdCHB_LqCd7d61482d5iGDbcD"


def get_weibo_user(weibo_id):


    result = {}
    try:
        api_url = "https://api.weibo.com/2/statuses/queryid.json?type=1" + "&mid=" + weibo_id + "&access_token=" + ACCESS_TOKEN

        r = requests.get(api_url)

        id = (r.json())["id"]

        api_url = "https://api.weibo.com/2/statuses/show.json?access_token=" + ACCESS_TOKEN + "&id=" + id

        r = requests.get(api_url)

        user = (r.json())["user"]

        # print ">>>>", user, r.url


        result["screenName"] = user["screen_name"]
        result["name"] = user["name"]
        result["profileImageUrl"] = user["profile_image_url"]
        result["description"] = user["description"]
        result["url"] = user["url"]

    except Exception as e:


        print "get_weibo_user error", e
        return None


    return result


if __name__ == '__main__':
    print get_weibo_user("3821293965254017")



