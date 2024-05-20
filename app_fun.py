from dotenv import load_dotenv
from os.path import join, dirname, abspath
import os
from collections import defaultdict
import pymongo
from pymongo import MongoClient
import plotly.express as px
import pandas as pd
from config import *
from logger import LoggerConfigurator
import logging

log_configurator = LoggerConfigurator(log_file='logs/app_fun.log')
log_configurator.configure()
logger = logging.getLogger()


root_path = abspath(join(dirname(__file__), os.pardir))
dotenv_path = join(root_path, '.env')
load_dotenv(dotenv_path, override=True)
uri = os.environ.get("MONGO_URI")

# TODO: py
client = MongoClient(uri)
db = client['coffee-map']
# raw_shop_collection
shop_collection = db['raw_shop_info']
mrt_collection = db['mrt_location']


def handle_start_end_place(shop_names, start_place, end_place):
    fixed_start = False
    fixed_end = False

    if start_place:
        if start_place in shop_names:
            shop_names.insert(0, shop_names.pop(shop_names.index(start_place)))
        else:
            shop_names.insert(0, start_place)
        fixed_start = True

    if end_place:
        if end_place in shop_names:
            shop_names.pop(shop_names.index(end_place))
            shop_names.append(end_place)
        else:
            shop_names.append(end_place)
        fixed_end = True

    return shop_names, fixed_start, fixed_end


def validate_and_get_walking_time(walking_time):
    return int(walking_time) if walking_time else 10


def get_selected_location(request_form):
    """
    Get selected district, MRT station, and user location from the form.
    """
    selected_district = request_form.get('district', '')
    selected_mrt = request_form.get('mrt', '')
    selected_lat_lng = [request_form.get(
        'longitude', ''), request_form.get('latitude', '')]

    if request_form.get('checkboxValue') == 'true' and (not selected_lat_lng[0] or not selected_lat_lng[1]):
        selected_lat_lng = [DEFAULT_CENTER[1], DEFAULT_CENTER[0]]

    return selected_district, selected_mrt, selected_lat_lng


def prepare_search_query(request_form):
    """
    Prepare the search query based on the form data.
    Args:
        request_form (_type_): request form from user input.
    """
    search_query = defaultdict(dict)
    if 'search_by_name' in request_form:
        search_query['name'] = {'text': request_form['shop_name']}
    elif 'search_by_filters' in request_form:
        selected_district, selected_mrt, selected_lat_lng = get_selected_location(
            request_form)
        walking_time = validate_and_get_walking_time(
            request_form.get('walking_time', ''))
        selected_tags = request_form.getlist('tags')
        search_query['filters'] = {
            'district': selected_district,
            'tags': selected_tags,
            'user_location': selected_lat_lng,
            'mrt': selected_mrt,
            'walking_time': walking_time
        }
    return search_query


def merge_dicts(dict1, dict2):
    if isinstance(dict1, list) and isinstance(dict2, list):
        return dict1+dict2
    if isinstance(dict1, dict) and isinstance(dict2, dict):
        return dict(list(dict1.items())+list(dict2.items()))
    return False


def search_mrt(station_name):
    query = {"StationName.Zh_tw": station_name}
    results = mrt_collection.find(query)
    exits_dict = {}
    for ele in results:
        id = ele['ExitID']
        location = ele['geometry']['coordinates']
        exits_dict[id] = location
    # print(exits_dict)
    return exits_dict


def find_mrt_shop(station_name, walking_time, tag_query):
    exits_dict = search_mrt(station_name)
    output = []
    wt_lm = 0.66*walking_time*0.1
    for exit_number, corrdinates in exits_dict.items():
        geo_query = {'geometry': {'$geoWithin': {"$centerSphere": [
            corrdinates, wt_lm/6378.1]}}}
        combined_query = {'$and': tag_query+[geo_query]}
        shops = list(shop_collection.find(combined_query))

        for shop in shops:
            found = False
            for existing_shop in output:
                if existing_shop['_id'] == shop['_id']:
                    if exit_number not in existing_shop['exit']:
                        existing_shop['exit'].append(exit_number)
                    found = True
                    break

            if not found:
                shop_info = shop
                shop_info['mrt'] = station_name
                shop_info['exit'] = [exit_number]
                output.append(shop_info)
    return output


def search_by_name(name):
    keyword = name['text']
    # logging.info(f"Keyword: {keyword}")
    output = list(shop_collection.find({
        "$and": [
            {"_id": {"$regex": keyword, "$options": "i"}},
            {'place_detail.formatted_address': {'$regex': '北市'}}
        ]
    }).sort('doc.user_ratings_total', -1))
    return output


def search_by_filters(filters):
    output = []
    # logging.info(f'Filters: {filters}')
    district = filters.get('district', '北市')
    search_tags = filters.get('tags', [])
    mrt_station = filters.get('mrt', '')
    walking_time = filters.get('walking_time', 10)

    if district == 'all':
        district = '北市'

    query_conditions = [{'tags.' + tag: {'$exists': True}}
                        for tag in search_tags]

    if mrt_station:
        output = find_mrt_shop(
            mrt_station, walking_time, query_conditions)
        return output

    if filters['user_location'] != ['', '']:
        user_location = filters['user_location']  # str
        user_location = [float(user_location[0]), float(user_location[1])]
        user_km = 0.66 * walking_time * 0.1
        user_query = {'geometry': {'$geoWithin': {"$centerSphere": [
            user_location, user_km/6378.1]}}}
        query_conditions.append(user_query)
    else:
        query_conditions.append({
            'place_detail.formatted_address': {'$regex': district}})

    query_conditions.append(
        {'place_detail.formatted_address': {'$regex': '北市'}})
    query = {'$and': query_conditions}

    output = list(shop_collection.find(
        query).sort('doc.user_ratings_total', -1))

    return output


def search_db(query):
    # TODO: search_cafe_store()
    """
    Search shops based on various filters.
    """
    output = []
    logging.info("Enter search_db.")
    logging.info(f"Query: {query}")
    if 'filters' in query:
        output = search_by_filters(query['filters'])
    elif 'name' in query:
        output = search_by_name(query['name'])
    else:
        logging.error("Invalid query format")

    logging.info(f"Search results count: {len(output)}")
    return output


def get_lat_lng(shop_name):
    query = {'_id': shop_name}
    result = shop_collection.find_one(query)
    if result:
        try:
            return result['doc']['geometry']['location']
        except Exception as e:
            logging.error(f"Error: {e}")
            return None
    else:
        return None


def data_for_radars(data_tags, selected_tags, min_tags=5):
    logging.info('in data_for_radars')
    from config import tag_translations

    df = pd.DataFrame(list(data_tags.items()), columns=['tag', 'count'])
    df.sort_values(
        by=['count'], inplace=True, ascending=False)

    if len(selected_tags) < min_tags:
        additional_tags = df.loc[~df['tag'].isin(selected_tags), 'tag'].head(
            min_tags - len(selected_tags)).tolist()
        selected_tags.extend(additional_tags)

    selected_df = df[df['tag'].isin(selected_tags)].copy()
    selected_df['tag'] = selected_df['tag'].map(tag_translations)
    return selected_df.to_dict(orient='list')
