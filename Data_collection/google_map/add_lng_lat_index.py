from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError
from dotenv import load_dotenv
from os.path import join, dirname, abspath
import os
from datetime import datetime
import logging

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
raw_collection = db['raw_shop_info']

bulk_operations = []
for doc in raw_collection.find():
    coordinates = [doc['doc']['geometry']['location']
                   ['lng'], doc['doc']['geometry']['location']['lat']]
    insert_dict = {
        'geometry': {
            'type': 'Point',
            'coordinates': coordinates
        },
        'update_at': datetime.utcnow()}
    name = doc['_id']

    update_one = UpdateOne(
        {"_id": name},
        {"$set": insert_dict},
        upsert=True
    )
    print(insert_dict)
    bulk_operations.append(update_one)

try:
    bulk_result = raw_collection.bulk_write(bulk_operations)
except BulkWriteError as e:
    for error in e.details['writeErrors']:
        logging.error(f"Error: {error['errmsg']}")


raw_collection.create_index([("geometry", "2dsphere")])
client.close()
