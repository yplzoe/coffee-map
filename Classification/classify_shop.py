import logging
from logging.handlers import TimedRotatingFileHandler
from dotenv import load_dotenv, find_dotenv
from os.path import join, dirname, abspath
import os
from pymongo import MongoClient
from datetime import datetime
from ..config import *

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


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


root_path = abspath(join(dirname(__file__), os.pardir))
dotenv_path = join(root_path, '.env')
load_dotenv(dotenv_path, override=True)
uri = os.environ.get("MONGO_URI")


client = MongoClient(uri)
db = client['coffee-map']
raw_collection = db['raw_shop_info']
more_collection = db['more_reviews']


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
