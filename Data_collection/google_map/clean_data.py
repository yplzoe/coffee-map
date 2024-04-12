import os
from os.path import join, dirname, abspath
from dotenv import load_dotenv, find_dotenv
import time
import pymongo
from pymongo import MongoClient
from pymongo.errors import BulkWriteError

parent_path = abspath(join(dirname(__file__), os.pardir))
root_path = abspath(join(parent_path, os.pardir))
dotenv_path = join(root_path, '.env')
load_dotenv(dotenv_path, override=True)

uri = os.environ.get("MONGO_URI")
client = MongoClient(uri)

mongo_db = client['coffee-map']
original_collection = mongo_db['test_db']
new_collection = mongo_db['raw_shop_info']

pipeline = [
    {"$sort": {"_id": 1}},
    {"$sort": {"fields_count": -1}},  # contain most info
    {"$group": {"_id": "$name", "doc": {"$first": "$$ROOT"}}}
]
duplicates = original_collection.aggregate(
    pipeline,  maxTimeMS=60000, allowDiskUse=True)
# print(duplicates)

try:
    mongo_insert = new_collection.insert_many(
        duplicates)
except BulkWriteError as e:
    for error in e.details['writeErrors']:
        print(f"Error: {error['errmsg']}")

client.close()
