# import tabu_search
import os
from os.path import join, dirname, abspath
from dotenv import load_dotenv
import logging
import requests
import json
from collections import defaultdict
from pymongo import MongoClient
from datetime import datetime
from pprint import pprint

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


parent_path = abspath(join(dirname(__file__), os.pardir))
root_path = abspath(join(parent_path, os.pardir))
dotenv_path = join(root_path, '.env')
load_dotenv(dotenv_path, override=True)

GOOGLE_PLACES_API_KEY = os.environ.get("GOOGLE_ROUTES_API_KEY")

uri = os.environ.get("MONGO_URI")
client = MongoClient(uri)
db = client['coffee-map']

# TODO: for bus, set time and show which bus


def get_route(origin, destination, travel_mode):
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': GOOGLE_PLACES_API_KEY,
        'X-Goog-FieldMask': (
            'routes.polyline,'
            'routes.routeLabels,'
            'routes.duration,'
            'routes.distanceMeters,'
            'routes.localizedValues,'
            'routes.legs.distanceMeters,'
            'routes.legs.stepsOverview,'
            'routes.legs.steps.staticDuration,'
            'routes.legs.steps.transitDetails,'
            'routes.legs.steps.navigationInstruction,'
            'routes.legs.steps.localizedValues,'
            'routes.legs.steps.travelMode,'
            'routes.legs.steps.polyline'
        )
    }
    payload = {
        "origin": {
            "address": origin  # option 2
        },
        "destination": {
            "address": destination  # option 3
        },
        "travelMode": travel_mode,  # option 4
        "computeAlternativeRoutes": "true",
        "polylineEncoding": "GEO_JSON_LINESTRING",  # specifying GeoJSON line string
        "transitPreferences": {
            "routingPreference": "LESS_WALKING",  # option 5
            "allowedTravelModes": ["BUS", "RAIL", "SUBWAY"]  # option 6
        },
    }
    response = requests.post(url, headers=headers, json=payload)
    result = response.json()
    if 'error' in result:
        pass
    else:
        add_to_mongo(origin, destination, result, travel_mode)

    return result


def add_to_mongo(origin, destination, data, travel_mode):
    collection = db['routes']
    data['origin'] = origin
    data['destination'] = destination
    data['travel_mode'] = travel_mode
    create_at = datetime.utcnow()
    data['create_at'] = create_at
    try:
        result = collection.insert_one(data)
        logging.info(f"Document inserted with _id: {result.inserted_id}")
    except Exception as e:
        logging.error(f'Error when insert into mongo: {e}')


def get_route_dict(arr, travel_mode, fixed_start=False, fixed_end=False):
    output = defaultdict(
        lambda: defaultdict(lambda: float('inf')))
    output_shortest_index = defaultdict(dict)
    full_routes = defaultdict(dict)
    collection = db['routes']
    start_place = arr[0]
    end_place = arr[-1]
    n = len(arr)
    for i in range(n):
        origin = arr[i]
        if i == n-1 and fixed_end == True:
            continue
        for j in range(n):
            destination = arr[j]
            if j == 0 and i > j and fixed_start == True:
                continue
            if origin == destination:
                continue
            query = {'$and': [{'origin': origin}, {
                'destination': destination}, {'travel_mode': travel_mode}]}
            in_db = collection.find_one(query)
            if in_db:
                if 'error' in in_db:
                    in_db = None
            if in_db:
                route_result = {}
                route_result['routes'] = in_db['routes']
            else:
                route_result = get_route(origin, destination, travel_mode)
            full_routes[origin][destination] = route_result['routes']
            durations = [(int(route['duration'][:-1]), index)
                         for index, route in enumerate(route_result['routes'])]
            shortest_duration, shortest_index = min(
                durations, key=lambda x: x[0])
            output[origin][destination] = shortest_duration
            output_shortest_index[origin][destination] = shortest_index
    return output, output_shortest_index, full_routes


def return_all_path(arr, shortest_index, full_routes):
    n = len(arr)
    output = []
    for i in range(1, n):
        origin = arr[i-1]
        destinaton = arr[i]
        index = shortest_index[origin][destinaton]
        encoded_polyline = full_routes[origin][destinaton][index]['polyline']['geoJsonLinestring']
        output.append(encoded_polyline)
    return output


def turn_into_geojson(all_path):
    output = {
        "type": "FeatureCollection",
        "features": []
    }
    len_all_path = len(all_path)
    count = 1
    for i in range(len_all_path):
        for j in range(1, len(all_path[i]['coordinates'])):
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [all_path[i]['coordinates'][j-1], all_path[i]['coordinates'][j]]
                },
                "properties": {},
                "id": count
            }
            output['features'].append(feature)
            count += 1

    return output


def close_mongo():
    client.close()


# arr = ['特有種商行Realguts cafe（藝文咖啡）', 'Coffee sind',
#        'Coffee Underwater', 'Le Park Cafe公園咖啡館']
# travel_mode = "DRIVE"

# dis_dict, shortest_index, full_routes = get_route_dict(arr, travel_mode)

# test = return_all_path(arr, shortest_index, full_routes)

# turn_into_geojson(test)

# dis_dict = {'Coffee Underwater': {'Coffee sind': 564,
#                                   'Le Park Cafe公園咖啡館': 145,
#                                   '特有種商行Realguts cafe（藝文咖啡）': 553},
#             'Coffee sind': {'Coffee Underwater': 634,
#                             'Le Park Cafe公園咖啡館': 619,
#                             '特有種商行Realguts cafe（藝文咖啡）': 89},
#             'Le Park Cafe公園咖啡館': {'Coffee Underwater': 110,
#                                   'Coffee sind': 578,
#                                   '特有種商行Realguts cafe（藝文咖啡）': 567},
#             '特有種商行Realguts cafe（藝文咖啡）': {'Coffee Underwater': 558,
#                                          'Coffee sind': 113,
#                                          'Le Park Cafe公園咖啡館': 584}}
# best_solution, best_obj = tabu_search.tabu_search(
#     arr, 100, 2**(len(arr)-1), dis_dict)
# # pprint(best_solution)
# # pprint(best_obj)
