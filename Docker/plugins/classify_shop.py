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


BREW_TAGS = ["手沖", "單品", "賽風", "虹吸", "冰滴", "莊園咖啡", "精品咖啡", "競標豆"
             "耶加雪菲", "肯亞", "翡翠莊園", "曼特寧", "日曬", "水洗", "蜜處理", "厭氧", "SOE", "藝伎", "藝妓"]
COFFEE_TAGS = ["咖啡好喝", "拿鐵好喝", "咖啡不錯", "特調", "拿鐵", "SOE", "卡布奇諾", "摩卡"]
BEANS_TAGS = ["咖啡豆", "熟豆", "豆子"]
INTERNET_TAGS = ["網路", "有wifi", "免費wifi"]
SOCKET_TAGS = ["插座"]
SEAT_TAGS = ["座位", "位置多"]
DESERT_TAGS = ["甜點", "提拉米蘇", "塔", "布丁", "蛋糕", "戚風", "生乳捲", "乳酪", "費南雪",
               "冰淇淋", "馬卡龍", "餅乾", "泡芙", "糖果", "果凍", "巧克力", "米果", "派", "瑪德蓮", "司康", "可麗露", "可頌", "巴斯克"]
PET_TAGS = ["寵物", "貓", "狗", "鸚鵡", "可帶寵物"]
WORK_TAGS = ["工作", "讀書", "辦公", "看書"]
COMFORT_TAGS = ["舒適", "舒服", "柔軟", "溫馨", "安逸", "放鬆", "輕鬆", "休閒", "安心", "放鬆", "舒壓",
                "悠閒", "平靜", "安靜", "寧靜", "療癒", "安寧", "慵懶", "無壓力", "怡人", "心安", "舒緩"]
QUIET_TAGS = ["安靜", "寧靜", "靜謐", "肅靜", "無聲",  "靜默", "平靜", "安寧", "靜寂",
              "安然", "低調", "微聲", "悄然", "默默", "悄悄", "沉寂", "幽靜", "悠然"]
TIME_TAGS = ["不限時", "無時間限制", "不趕客"]

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
            try:
                reviews = document['doc'].get(
                    'place_details', {}).get('reviews', [])
                tag_result = categorize_data_raw(reviews)

                find_latest = more_collection.find_one(
                    {"name": id}, sort=[("update_at", -1)])
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
            except Exception as e:
                logging.error(f'Error: {e}')

        client.close()
        logging.info("Tag categorization completed.")
    except Exception as e:
        logging.error(f"Error occurred during tag categorization: {str(e)}")


# if __name__ == "__main__":
#     get_classified_tag()
