from dotenv import load_dotenv, find_dotenv
from os.path import join, dirname, abspath
import os
from pymongo import MongoClient
from module import MongoDB

BREW_TAGS = ["手沖", "單品", "賽風", "虹吸", "冰滴"]
COFFEE_TAGS = ["咖啡好喝", "拿鐵好喝", "咖啡不錯", "特調"]
BEANS_TAGS = ["咖啡豆", "熟豆", "豆子"]
INTERNET_TAGS = ["網路", "有wifi", "免費wifi"]
SOCKET_TAGS = ["插座"]
SEAT_TAGS = ["座位", "位置多"]
DESERT_TAGS = ["甜點", "提拉米蘇", "塔", "布丁", "蛋糕"]
PET_TAGS = ["寵物", "貓", "狗"]
WORK_TAGS = ["工作", "讀書", "辦公", "看書"]
COMFORT_TAGS = ["舒適", "放鬆"]
QUIET_TAGS = ["安靜"]
TIME_TAGS = ["不限時"]

TAGS = {
    "brew": BREW_TAGS,
    "coffee": COFFEE_TAGS,
    "beans": BEANS_TAGS,
    "internet": INTERNET_TAGS,
    "socket": SOCKET_TAGS,
    "seat": SEAT_TAGS,
    "desert": DESERT_TAGS,
    "pet": PET_TAGS,
    "work": WORK_TAGS,
    "comfort": COMFORT_TAGS,
    "quiet": QUIET_TAGS,
    "time": TIME_TAGS
}

root_path = abspath(join(dirname(__file__), os.pardir))
dotenv_path = join(root_path, '.env')
load_dotenv(dotenv_path, override=True)


def categorize_data(reviews):
    result = {}
    for review in reviews:
        text = review.get('text', '')
        if text:
            for tag_type, tags in TAGS.items():
                for tag in tags:
                    if tag in text:
                        if tag_type in result:
                            result[tag_type] += 1
                        else:
                            result[tag_type] = 1
                        break
    return result


def get_classified_tag():
    uri = os.environ.get("MONGO_URI")
    client = MongoClient(uri)
    db = client['coffee-map']
    raw_collection = db['raw_shop_info']

    for document in raw_collection.find():
        id = document.get('_id')  # name of coffee
        reviews = document['doc'].get('place_details', {}).get('reviews', [])
        tag_result = categorize_data(reviews)
        document.pop('tags', None)
        document['tags'] = tag_result
        raw_collection.replace_one({'_id': document['_id']}, document)

    client.close()
