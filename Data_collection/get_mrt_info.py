import urllib.request
import pymongo
from pymongo import MongoClient, UpdateOne
import requests
from pymongo.errors import BulkWriteError
from dotenv import load_dotenv
from os.path import join, dirname, abspath
import os
from datetime import datetime
import logging
import json
import urllib
import pandas as pd
import ssl
import re

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

root_path = abspath(join(dirname(__file__), os.pardir))
dotenv_path = join(root_path, '.env')
load_dotenv(dotenv_path, override=True)
uri = os.environ.get("MONGO_URI")

client = MongoClient(uri)
db = client['coffee-map']
collection = db['mrt_location']

url = 'https://tdx.transportdata.tw/api/basic/v2/Rail/Metro/StationExit/TRTC?%24format=JSON'
context = ssl._create_unverified_context()

data = {}

# with open('/Users/a123/Documents/GitHub/coffee-map/Data_collection/response_mrt.json') as f:
#     data = json.load(f)

# with urllib.request.urlopen(url, context=context) as jsondata:
#     data = json.loads(jsondata.read().decode('utf-8'))
print(data)
bulk_operatons = []
error = []
for doc in collection.find():
    station_id = doc['StationID']
    line_name = re.split('(\d+)', station_id)[0]
    print(line_name)
    lat = doc['ExitPosition']['PositionLat']
    lon = doc['ExitPosition']['PositionLon']
    update_operation = UpdateOne(
        {'_id': doc['_id']},
        {'$set': {
            'Line': line_name,
            'geometry': {
                'type': 'Point',
                'coordinates': [lon, lat]
            }
        }},
        upsert=True
    )
    bulk_operatons.append(update_operation)

if bulk_operatons:
    try:
        bulk_result = collection.bulk_write(bulk_operatons)
    except BulkWriteError as bwe:
        logging.error(f"Error writing bulk operations: ", bwe.details)

client.close()
