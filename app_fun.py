from dotenv import load_dotenv
from os.path import join, dirname, abspath
import os
import pymongo
from pymongo import MongoClient
import plotly.express as px
import pandas as pd
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
mrt_collection = db['mrt_location']


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


def find_mrt_shop(station_name):
    exits_dict = search_mrt(station_name)
    output = []
    for exit_number, corrdinates in exits_dict.items():
        query = {'geometry': {'$geoWithin': {"$centerSphere": [
            corrdinates, 0.66/6378.1]}}}
        shops = list(raw_collection.find(query))

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


exits_dict = find_mrt_shop("土城")


def search_db(query):
    output = []
    logging.info("enter search_db")
    if 'filters' in query:
        # search with places and tags
        # {'filters': { 'district': selected_district, 'tags': selected_tags}}
        district = query['filters']['district']
        search_tags = query['filters']['tags']

        if district == 'all' or district == "":
            district = '北市'

        query_conditions = [{'tags.' + tag: {'$exists': True}}
                            for tag in search_tags]

        if query['filters']['user_location'] != ['', '']:
            user_location = query['filters']['user_location']  # str
            user_location = [float(user_location[0]), float(user_location[1])]
            user_query = {'geometry': {'$geoWithin': {"$centerSphere": [
                user_location, 0.66/6378.1]}}}
            query_conditions.append(user_query)
        else:
            query_conditions.append({
                'place_detail.formatted_address': {'$regex': district}})

        query = {'$and': query_conditions}
        output = list(raw_collection.find(
            query).sort('doc.user_ratings_total', -1))
        print()

    elif 'name' in query:
        # search with name
        keyword = query['name']['text']
        logging.info(f"keyword: {keyword}")
        results = raw_collection.find({
            "$and": [{"_id": {"$regex": keyword, "$options": "i"}},
                     {'place_detail.formatted_address': {'$regex': '北市'}}]}).sort('doc.user_ratings_total', -1)

        output = list(results)
        print()
        # for result in results:
        #     logging.info(f"search result: {result['_id']}")
        #     output.append(result)
    if len(output) == 0:
        output.append(
            {'_id': 'There is no store that matches.',
             'place_detail': {'name': 'There is no store that matches.'}}
        )
    # logging.info(f"output: {output}")
    return output


def get_lat_lng(shop_name):
    query = {'_id': shop_name}
    result = raw_collection.find_one(query)
    # print(result)
    if result:
        try:
            return result['doc']['geometry']['location']
        except Exception as e:
            logging.error(f"Error: {e}")
            return None
    else:
        return None


def calculate_lat_lng_dis(lat, lng):
    pass


def data_for_radars(data, selected_tags):
    tags = data["tags"]
    tag_translations = {
        "brew": '手沖',
        "coffee": '咖啡',
        "beans": '咖啡豆',
        "internet": '網路',
        "socket": '插座',
        "seat": '座位',
        "desert": '甜點',
        "pet": '寵物',
        "work": '適合工作',
        "comfort": '氛圍',
        "quiet": '安靜',
        "time": '不限時'
    }
    df = pd.DataFrame(list(tags.items()), columns=['tag', 'count'])
    df.sort_values(
        by=['count'], inplace=True, ignore_index=True, ascending=False)

    if len(selected_tags) < 5:
        additional_tags = df[~df['tag'].isin(
            selected_tags)].head(5 - len(selected_tags))
        selected_tags.extend(additional_tags['tag'].tolist())

    selected_df = df.loc[df['tag'].isin(selected_tags)]
    selected_df['tag'] = selected_df['tag'].map(tag_translations)
    selected_df = selected_df.to_dict(orient='list')

    return selected_df


def plot_radars(data, selected_tags):
    tags = data["tags"]
    df = pd.DataFrame(list(tags.items()), columns=['tag', 'count'])
    df.sort_values(
        by=['count'], inplace=True, ignore_index=True, ascending=False)

    if len(selected_tags) < 5:
        additional_tags = df[~df['tag'].isin(
            selected_tags)].head(5 - len(selected_tags))
        selected_tags.extend(additional_tags['tag'].tolist())

    selected_df = df.loc[df['tag'].isin(selected_tags)]
    fig = px.line_polar(selected_df, r='count', theta='tag', line_close=True)
    return fig

# query = {'filters': {'district': '中正區', 'tags': ['手沖']}}
# result = search_db(query)
# print(result[0])

# query_name = {'name': {'text': 'starbucks'}}
# result_name = search_db(query_name)
# print(len(result_name))


shop_name = '光進來的地方'
# get_lat_lng(shop_name)
