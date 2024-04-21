import logging
from logging.handlers import TimedRotatingFileHandler
from dotenv import load_dotenv, find_dotenv
from os.path import join, dirname, abspath
import os
from pymongo import MongoClient
from datetime import datetime

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

dotenv_path = 'plugins/.env'
load_dotenv(dotenv_path, override=True)


mongo_logger = logging.getLogger("MongoDB")
mongo_logger.setLevel(logging.INFO)


log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, "log_classify_shop.log")
mongo_handler = TimedRotatingFileHandler(
    log_file, when="midnight", interval=1, backupCount=7)
mongo_handler.setLevel(logging.INFO)


formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
mongo_handler.setFormatter(formatter)
mongo_logger.addHandler(mongo_handler)


BREW_TAGS = ["手沖", "單品", "賽風", "虹吸", "冰滴"]
COFFEE_TAGS = ["咖啡好喝", "拿鐵好喝", "咖啡不錯", "特調"]
BEANS_TAGS = ["咖啡豆", "熟豆", "豆子"]
INTERNET_TAGS = ["網路", "有wifi", "免費wifi"]
SOCKET_TAGS = ["插座"]
SEAT_TAGS = ["座位", "位置多"]
DESERT_TAGS = ["甜點", "提拉米蘇", "塔", "布丁", "蛋糕"]
PET_TAGS = ["寵物", "貓", "狗", "鸚鵡"]
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


def categorize_data_raw(reviews):
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


def categorize_data_more_reviews(reviews, tag_result):
    # result = {}
    for review in reviews:  # array
        if review:
            for tag_type, tags in TAGS.items():
                for tag in tags:
                    if tag in review:
                        if tag_type in tag_result:
                            tag_result[tag_type] += 1
                        else:
                            tag_result[tag_type] = 1
                        break


def get_classified_tag():
    try:
        uri = os.environ.get("MONGO_URI")
        client = MongoClient(uri)
        db = client['coffee-map']
        raw_collection = db['raw_shop_info']
        more_collection = db['more_reviews']
        count = 0

        for document in raw_collection.find():
            if count > 1:
                break
            count += 1
            id = document.get('_id')  # name of coffee
            reviews = document['doc'].get(
                'place_details', {}).get('reviews', [])
            tag_result = categorize_data_raw(reviews)

            find_latest = more_collection.find_one(
                {"name": id}, sort=[("create_at", -1)])
            find_latest_review = find_latest.get('reviews')
            if (find_latest_review != []) and (find_latest_review != ["error"]):
                categorize_data_more_reviews(
                    find_latest_review, tag_result)

            current_time = datetime.utcnow()
            result = raw_collection.update_one(
                {'_id': id},
                {'$set': {'tags': tag_result, 'update_at': current_time},
                 '$setOnInsert': {'create_at': current_time}},
                upsert=True
            )
            mongo_logger.info(f"Tags updated for coffee shop: {id}")

        client.close()
        logging.info("Tag categorization completed.")
    except Exception as e:
        logging.error(f"Error occurred during tag categorization: {str(e)}")


# if __name__ == "__main__":
#     get_classified_tag()
