import populartimes
import pymongo
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
import os
from os.path import join, dirname, abspath
from dotenv import load_dotenv, find_dotenv
import time
from datetime import datetime

parent_path = abspath(join(dirname(__file__), os.pardir))
root_path = abspath(join(parent_path, os.pardir))
dotenv_path = join(root_path, '.env')
load_dotenv(dotenv_path, override=True)

GOOGLE_PLACES_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY")

uri = os.environ.get("MONGO_URI")
client = MongoClient(uri)

mongo_db = client['coffee-map']
mongo_collection = mongo_db['raw_shop_info']


for doc in mongo_collection.find():
    if 'popularity_data' in doc:
        continue
    shop_name = doc['doc']['name']
    shop_place_id = doc['doc']['place_id']
    try:
        result = populartimes.get_id(GOOGLE_PLACES_API_KEY, shop_place_id)
    except:
        result = {}
    current_time = datetime.utcnow()
    if 'current_popularity' in result:
        popularity_data = {
            'collected_time': current_time,
            'current_popularity': result['current_popularity'],
            'populartimes': result['populartimes']
        }
    else:
        popularity_data = {
            'collected_time': current_time,
            'current_popularity': None,
            'populartimes': None
        }
    update_operation = mongo_collection.update_many(
        {'doc.place_id': shop_place_id},
        {'$set': {
            'popularity_data': popularity_data,
            'update_at': current_time
        }},
        upsert=True
    )


client.close()
