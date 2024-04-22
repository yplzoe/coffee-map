from dotenv import load_dotenv, find_dotenv
from os.path import join, dirname, abspath
import os
import pymongo
from pymongo import MongoClient
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


def search_db(query):
    output = []
    logging.info("in search_db")
    if 'filters' in query:
        # search with places and tags
        # {'filters': { 'district': selected_district, 'tags': selected_tags}}
        district = query['filters']['district']
        search_tags = query['filters']['tags']
        if district == 'all' or district == "":
            district = '北市'

        query_conditions = [{'tags.' + tag: {'$exists': True}}
                            for tag in search_tags]
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
    logging.info(f"output: {output}")
    return output


# query = {'filters': {'district': '中正區', 'tags': ['手沖']}}
# result = search_db(query)
# print(result[0])

# query_name = {'name': {'text': 'starbucks'}}
# result_name = search_db(query_name)
# print(len(result_name))
