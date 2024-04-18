"""_summary_
    利用google map api 取得所有位在(25.30118, 121.28282)~(24.67403, 122.00316)之間的咖啡廳
    1. 取的locations 每個點間隔2km
    2. 用place_neaby 找中心點為loc 半徑為1km內的咖啡廳 最多60筆
    3. insert to mongodb
"""
import googlemaps
import os
from os.path import join, dirname, abspath
from dotenv import load_dotenv, find_dotenv
import time
from datetime import datetime
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

gmaps_logger = logging.getLogger("gmaps_map_data")
gmaps_logger.setLevel(logging.INFO)


log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, "log_get_map_data.log")
gmaps_handler = TimedRotatingFileHandler(
    log_file, when="midnight", interval=1, backupCount=7)
gmaps_handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
gmaps_handler.setFormatter(formatter)
gmaps_logger.addHandler(gmaps_handler)

dotenv_path = 'plugins/.env'
load_dotenv(dotenv_path, override=True)

GOOGLE_PLACES_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY")


def calculate_location_points(init_location=(25.30118, 121.28282), bound_location=(24.67403, 122.00316), add_longitude=0.009 * 2, add_latitude=0.009 * 2):

    location_queue = queue.Queue()

    def add_locations(latitude, longitude):
        if latitude < bound_location[0]:
            return
        while longitude <= bound_location[1]:
            location_queue.put((latitude, longitude))
            longitude += add_longitude
        add_locations(latitude-add_latitude, init_location[1])

    add_locations(init_location[0], init_location[1])

    return location_queue


def get_location_from_txt(file_name=('plugins/locations.txt')):
    with open(file_name, 'r') as file:
        locations = file.readlines()

    # Remove newline characters and convert strings to tuples
    locations = [eval(location.strip()) for location in locations]

    # Shuffle the list randomly
    random.shuffle(locations)

    # Print the shuffled list
    print(len(locations))

    return locations


def get_places_to_mongodb(params, location):
    """use place_nearby to get info and insert to mongodb test_db, and get result to json

    Args:
        params (dict): _description_
        location (tuple(lat, lng)): _description_
    """
    output_json = []

    gmaps = googlemaps.Client(key=GOOGLE_PLACES_API_KEY)
    params['location'] = location

    uri = os.environ.get("MONGO_URI")
    client = MongoClient(uri)

    try:
        client.admin.command('ping')
        logging.info(
            "Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        logging.info(f"Fail to ping mongodb: {e}")

    mongo_db = client['coffee-map']
    mongo_collection = mongo_db['test_db']
    places_result = {}
    places_result = gmaps.places_nearby(**params)

    logging.info(f"input location: {params['location']}")
    logging.info(f"status: {places_result['status']}")
    for result in places_result['results']:
        result['create_at'] = datetime.utcnow()
        logging.info(
            f"result place name: {result['name']}")

    if places_result['status'] != 'ZERO_RESULTS':
        if 'next_page_token' in places_result:
            has_next = True

        while has_next:
            time.sleep(5)
            places_result = gmaps.places_nearby(**params)
            for result in places_result['results']:
                result['create_at'] = datetime.utcnow()
                output_json.append(result)
                logging.info(
                    f"result place name: {result['name']}")
            try:
                mongo_insert = mongo_collection.insert_many(
                    places_result['results'])
            except BulkWriteError as e:
                for error in e.details['writeErrors']:
                    logging.info(f"Error: {error['errmsg']}")

            if 'next_page_token' in places_result:
                has_next = True
                params['page_token'] = places_result['next_page_token']
            else:
                break
        current_date = datetime.now().strftime('%Y-%m-%d')
        filename = f'files/places_results_{current_date}.json'
        try:
            with open(filename, 'a') as json_file:
                json.dump(output_json, json_file)
        except FileNotFoundError:
            with open(filename, 'w') as json_file:
                json.dump(output_json, json_file)

    client.close()


def run_get_places_queue(item_queue, result_queue, params):
    while not item_queue.empty():
        time.sleep(random.randint(1, 5))
        location = item_queue.get()
        try:
            output = get_places_to_mongodb(params, location)
            result_queue.put(output)
        except Exception as e:
            logging.info(f"Error: {e}")
        count += 1


def search_cafe():
    init_location = (25.30118, 121.28282)
    small_radius = 1000  # 1km
    params = {
        'type': 'cafe',
        'keyword': 'cafe',
        'location': init_location,
        'radius': small_radius,
        'open_now': False,
        'language': 'zh-TW'
    }
    locations = get_location_from_txt()
    # appworks = (25.038722892075647, 121.53235946829987)
    # get_places_to_mongodb(params, appworks)

    # test
    count = 0
    for loc in locations:
        if count > 1:
            break
        count += 1
        time.sleep(random.randint(5, 10))
        if 'page_token' in params:
            params.pop('page_token')
        try:
            get_places_to_mongodb(params, loc)
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
    logging.info("Search cafe shop completed.")


# num_threads = 10
# result_queue = queue.Queue()  # null
# lock = Lock()
# run_get_places_queue(location_queue, result_queue, lock)


# lock = Lock()

# job_threads = []
# for i in range(num_threads):
#     job = threading.Thread(target=run_get_places_queue,
#                            args=(location_queue, result_queue, lock))
#     job_threads.append(job)
#     job_threads[i].start()


# print('done')

# for i in range(num_threads):
#     job_threads[i].join()
