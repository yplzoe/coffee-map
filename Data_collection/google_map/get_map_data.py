"""_summary_
    利用google map api 取得所有位在(25.30118, 121.28282)~(24.67403, 122.00316)之間的咖啡廳
    1. 取的locations 每個點間隔2km
    2. 用place_neaby 找中心點為loc 半徑為1km內的咖啡廳 最多60筆
    3. insert to mongodb
"""
# !: 不同location 取得相同結果

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


def calculate_location_points(init_location=(25.30118, 121.28282), bound_location=(24.67403, 122.00316), add_longitude=0.009 * 2, add_latitude=0.009 * 2):

    # taipei_location = (25.0330, 121.5654)
    # taipei_radius = 25000
    # appworks_location = (25.038724858601867, 121.53243166589439)
    # small_radius = 1000  # 1km

    # init_location = (25.30118, 121.28282)  # left-up corner
    # bound_location = (24.67403, 122.00316)  # right-button corner
    # add_longitude = 0.009 * 2  # 經度
    # add_latitude = 0.009 * 2  # 緯度

    location_queue = queue.Queue()

    # test_loc_list = []

    def add_locations(latitude, longitude):
        if latitude < bound_location[0]:
            return
        while longitude <= bound_location[1]:
            location_queue.put((latitude, longitude))
            # test_loc_list.append((latitude, longitude))
            longitude += add_longitude
        add_locations(latitude-add_latitude, init_location[1])

    add_locations(init_location[0], init_location[1])

    return location_queue


def get_location_from_txt(file_name=join(dirname(__file__), 'locations.txt')):
    with open(file_name, 'r') as file:
        locations = file.readlines()

    # Remove newline characters and convert strings to tuples
    locations = [eval(location.strip()) for location in locations]

    # Shuffle the list randomly
    random.shuffle(locations)

    # Print the shuffled list
    print(len(locations))

    return locations


def get_places_to_mongodb(params, location, token_dict):
    """use place_nearby to get info and insert to mongodb by insert many

    Args:
        params (dict): _description_
        location (tuple(lat, lng)): _description_
    """
    gmaps = googlemaps.Client(key=GOOGLE_PLACES_API_KEY)
    params['location'] = location
    # session_token = gmaps.session()
    # params['session_token'] = session_token

    uri = os.environ.get("MONGO_URI")
    client = MongoClient(uri)

    try:
        client.admin.command('ping')
        # print("Pinged your deployment. You successfully connected to MongoDB!")
        # with lock:
        #     print(f"location: {location}")
    except Exception as e:
        print(e)

    mongo_db = client['coffee-map']
    mongo_collection = mongo_db['test_db']
    places_result = {}
    places_result = gmaps.places_nearby(**params)

    # with lock:
    print(f"input location: {params['location']}")
    # places_result
    # print(f"return location: {}")
    print(places_result['status'])
    for i in range(len(places_result['results'])):
        print(places_result['results'][i]['name'])

    if places_result['status'] != 'ZERO_RESULTS':
        if 'next_page_token' in places_result:
            has_next = True
            params['page_token'] = places_result['next_page_token']
            if places_result['next_page_token'] in token_dict:
                token_dict[places_result['next_page_token']] += 1
            else:
                token_dict[places_result['next_page_token']] = 1
        else:
            has_next = False

        try:
            mongo_insert = mongo_collection.insert_many(
                places_result['results'])
        except BulkWriteError as e:
            for error in e.details['writeErrors']:
                print(f"Error: {error['errmsg']}")

        while has_next:
            time.sleep(5)
            places_result = gmaps.places_nearby(**params)
            # with lock:
            for i in range(len(places_result['results'])):
                print(places_result['results'][i]['name'])

            try:
                mongo_insert = mongo_collection.insert_many(
                    places_result['results'])
            except BulkWriteError as e:
                for error in e.details['writeErrors']:
                    print(f"Error: {error['errmsg']}")

            if 'next_page_token' in places_result:
                has_next = True
                params['page_token'] = places_result['next_page_token']
                if places_result['next_page_token'] in token_dict:
                    token_dict[places_result['next_page_token']] += 1
                else:
                    token_dict[places_result['next_page_token']] = 1
            else:
                break

    client.close()


def run_get_places_queue(item_queue, result_queue, lock):
    count = 0
    while not item_queue.empty():
        if count == 200:
            time.sleep(60*5)
            count = 0
        time.sleep(random.randint(1, 5))
        location = item_queue.get()
        try:
            output = get_places_to_mongodb(params, location)
            result_queue.put(output)
        except Exception as e:
            print(f"Error: {e}")
        count += 1


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
test_loc = (25.038995380814494, 121.53253176715249)
get_places_to_mongodb(params, test_loc)
locations = get_location_from_txt()
token_dict = {}
# appworks = (25.038722892075647, 121.53235946829987)
# get_places_to_mongodb(params, appworks, token_dict)
for loc in locations:
    time.sleep(random.randint(5, 10))
    print(f"before enter: {params}")
    if 'page_token' in params:
        params.pop('page_token')
    print(f"clean before enter: {params}")
    get_places_to_mongodb(params, loc, token_dict)
    print(f"loc: {loc}")
    print(f"params: {params}")
    print('--------------------')

print(token_dict)

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
