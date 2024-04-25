from app_fun import search_db, get_lat_lng, data_for_radars
from collections import defaultdict
from flask import Flask, request, jsonify, make_response, render_template, redirect, url_for
from flask_restful import Resource, Api
import logging
import time
import datetime
from bson.objectid import ObjectId
import Routes
import Routes.tabu_search as tabu_search
import Routes.get_travel_time_dictionary as get_travel_time_dictionary

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
api = Api(app)


@app.route('/search-shops')
def search_shops():
    shop_name = request.args.get('name', '')
    logging.info(f'input shop name: {shop_name}')
    search_query = defaultdict(dict)
    search_query['name'] = {'text': shop_name}
    shops = search_db(search_query)
    if shops[0]['_id'] == 'There is no store that matches.':
        return jsonify({'status': 'fail'}), 200

    for ss in shops:
        ss['doc']['_id'] = ss['doc']['_id'].__str__()
    output = []
    if len(shops) > 1:
        output.append(shops[0])
    else:
        output = shops
    shop_name = output[0]['_id']
    shop_location = get_lat_lng(shop_name)
    # logging.info(f"output: {output}")
    return jsonify({'status': 'success', 'shop_info': output, 'shop_location': shop_location}), 200


@app.route('/get-scheduling', methods=['GET', 'POST'])
def get_scheduling():
    data = request.json
    shop_names = data['shops']
    logging.info(f"shop name: {shop_names}")
    travel_mode = "DRIVE"
    dis_dict, shortest_index, full_routes = get_travel_time_dictionary.get_route_dict(
        shop_names, travel_mode)
    best_solution, best_obj = tabu_search.tabu_search(
        shop_names, 100, 2**len(shop_names), dis_dict)
    logging.info(f"best_solution: {best_solution}, best_obj: {best_obj}")
    polyline_list = get_travel_time_dictionary.return_all_path(
        best_solution, shortest_index, full_routes)
    # logging.info(f"polyline: {polyline_list}")
    geojson_list = get_travel_time_dictionary.turn_into_geojson(polyline_list)
    logging.info(f'geojson: {geojson_list}')

    return jsonify({'status': 'success', 'best_route': geojson_list, 'best_solution': best_solution, 'best_obj': best_obj}), 200


@app.route('/scheduling', methods=['GET', 'POST'])
def route():
    return render_template('scheduling.html')


@app.route('/search', methods=['GET', 'POST'])
def search():
    # search_query = None
    search_query = defaultdict(dict)
    if request.method == 'POST':
        selected_tags = []
        if 'search_by_name' in request.form:
            search_query['name'] = {'text': request.form['shop_name']}
        elif 'search_by_filters' in request.form:
            selected_district = request.form['district']
            selected_lat_lng = [request.form['latitude'],
                                request.form['longitude']]
            selected_tags = request.form.getlist('tags')
            search_query['filters'] = {
                'district': selected_district, 'tags': selected_tags}
        logging.info(f"search query: {search_query}")

        results = search_db(search_query)  # list of shop info
        len_results = len(results)
        for ss in results:
            ss['doc']['_id'] = ss['doc']['_id'].__str__()
        for i in range(len_results):
            if 'tags' in results[i]:
                tag_data = data_for_radars(results[i], selected_tags)
                results[i]['for_radar'] = tag_data
        logging.info(f"return data: {results}")
        return render_template('search.html', search_result=results)
    return redirect(url_for('index'))


@ app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)
