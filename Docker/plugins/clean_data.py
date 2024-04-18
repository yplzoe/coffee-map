import os
from os.path import join, dirname, abspath
from dotenv import load_dotenv, find_dotenv
import time
import pymongo
from pymongo import MongoClient, UpdateOne, DESCENDING
from pymongo.errors import BulkWriteError
from datetime import datetime
import logging

logging.basicConfig(filename='log_cleand_data.log', level=logging.INFO)

parent_path = abspath(join(dirname(__file__), os.pardir))
root_path = abspath(join(parent_path, os.pardir))
dotenv_path = join(root_path, '.env')
load_dotenv(dotenv_path, override=True)


def clean_data_from_test_to_raw():
    uri = os.environ.get("MONGO_URI")
    client = MongoClient(uri)

    mongo_db = client['coffee-map']
    original_collection = mongo_db['test_db']
    new_collection = mongo_db['raw_shop_info']

    unique_names = original_collection.distinct("name")

    bulk_operations = []

    for name in unique_names:
        latest_doc = original_collection.find_one(
            {"name": name}, sort=[("create_at", DESCENDING)])
        existing_doc = new_collection.find_one({"_id": name})
        if existing_doc:
            new_doc = {
                "doc": latest_doc,
                "create_at": datetime.utcnow()
            }
            update_one = UpdateOne(
                {"_id": name},
                {"$set": new_doc}
            )
            logging.info(f"Updated document with name: {name}")
        else:
            new_doc = {
                "_id": name,
                "doc": latest_doc,
                "create_at": datetime.utcnow()
            }
            update_one = UpdateOne(
                {"_id": name},
                {"$setOnInsert": new_doc},
                upsert=True
            )
            logging.info(f"Inserted new document with name: {name}")
        bulk_operations.append(update_one)

    try:
        bulk_result = new_collection.bulk_write(bulk_operations)
    except BulkWriteError as e:
        for error in e.details['writeErrors']:
            logging.error(f"Error: {error['errmsg']}")

    client.close()
