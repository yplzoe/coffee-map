"""_summary_:
get every details need for map
"""

import googlemaps
import os
from os.path import join, dirname, abspath
from dotenv import load_dotenv, find_dotenv
import time
import pymongo
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
import threading
from threading import Lock
import queue
import random
import logging
from logging.handlers import TimedRotatingFileHandler
import json
from datetime import datetime

gmaps_logger = logging.getLogger("gmaps_place_detail")
gmaps_logger.setLevel(logging.INFO)


log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, "log_get_place_detail.log")
gmaps_handler = TimedRotatingFileHandler(
    log_file, when="midnight", interval=1, backupCount=7)
gmaps_handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
gmaps_handler.setFormatter(formatter)
gmaps_logger.addHandler(gmaps_handler)


def get_all_details():
    try:
        dotenv_path = 'plugins/.env'
        load_dotenv(dotenv_path, override=True)
        uri = os.environ.get("MONGO_URI")
        client = MongoClient(uri)

        mongo_db = client['coffee-map']
        mongo_collection = mongo_db['raw_shop_info']

        GOOGLE_PLACES_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY")

        gmaps = googlemaps.Client(key=GOOGLE_PLACES_API_KEY)

        params = {
            'language': 'zh-TW',
            'fields': ["opening_hours", "reviews", "address_component", "formatted_address",
                       "serves_lunch", "website", "serves_breakfast", "serves_dinner", "serves_brunch",
                       "reservable",
                       "place_id", "name"
                       ]
        }
        output_json = []

        count = 0
        for document in mongo_collection.find():
            # if count > 3:
            #     break
            count += 1
            place_id = document['doc'].get('place_id')
            logging.info(f'Processing place with ID: {place_id}')
            place_detail = document.get('place_detail')
            if place_id and (place_detail == None):
                time.sleep(random.randint(3, 6))
                places_result = gmaps.place(place_id, **params)
                logging.info(f"status: {places_result['status']}")
                if places_result['status'] != 'ZERO_RESULTS':
                    place_detail = places_result['result']
                    logging.info(f"get_id: {place_detail['place_id']}")
                    if place_detail['place_id'] == place_id:
                        current_time = datetime.utcnow()
                        update_result = mongo_collection.update_one({'doc.place_id': place_id},
                                                                    {'$set': {'place_detail': place_detail, 'update_at': current_time},
                                                                     '$setOnInsert': {'create_at': current_time}},
                                                                    upsert=True)
                        output_json.append(place_detail)

        client.close()
        logging.info("Data fetching completed.")

        current_date = datetime.now().strftime('%Y-%m-%d')
        filename = f'files/places_detail_{current_date}.json'
        try:
            with open(filename, 'a') as json_file:
                json.dump(output_json, json_file)
            logging.info("Data write to file completed.")
        except FileNotFoundError:
            with open(filename, 'w') as json_file:
                json.dump(output_json, json_file)
            logging.info("Data write to file completed.")
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
