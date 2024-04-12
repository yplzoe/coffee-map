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


parent_path = abspath(join(dirname(__file__), os.pardir))
root_path = abspath(join(parent_path, os.pardir))
dotenv_path = join(root_path, '.env')
load_dotenv(dotenv_path, override=True)

GOOGLE_PLACES_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY")


gmaps = googlemaps.Client(key=GOOGLE_PLACES_API_KEY)

params = {
    'language': 'zh-TW',
    # 'fields': ["address_component"]
    'fields': ["opening_hours", "reviews", "address_component", "formatted_address",
               "serves_lunch", "website", "serves_breakfast", "serves_dinner", "serves_brunch",
               "reservable",
               "place_id", "name"
               ]
}

# result = gmaps.place('ChIJg2stEwmvQjQRlflmhwug3_A', **params)
# print(result)


# insert mongo
uri = os.environ.get("MONGO_URI")
client = MongoClient(uri)

mongo_db = client['coffee-map']
mongo_collection = mongo_db['raw_shop_info']

for document in mongo_collection.find():
    place_id = document['doc'].get('place_id')
    print(f'place_id: {place_id}')
    if place_id:
        time.sleep(random.randint(3, 6))
        places_result = gmaps.place(place_id, **params)
        print(f'status: {places_result['status'] }')
        if places_result['status'] != 'ZERO_RESULTS':
            place_detail = places_result['result']
            document['doc'].pop('place_details', None)
            document['doc']['place_details'] = place_detail
            mongo_collection.replace_one({'_id': document['_id']}, document)

client.close()
