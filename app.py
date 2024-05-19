from flask import send_from_directory
from app_fun import *
from collections import defaultdict
from flask import Flask, request, jsonify, make_response, render_template, redirect, url_for, session, flash
from flask_session import Session
from dotenv import load_dotenv
from os.path import join, dirname, abspath
import os
import logging
from logging.handlers import TimedRotatingFileHandler
import time
import datetime
from datetime import timedelta, datetime
import pytz
import Routes.tabu_search as tabu_search
import Routes.get_travel_time_dictionary as get_travel_time_dictionary

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create a TimedRotatingFileHandler
# Rotate daily, keep 7 days of logs
handler = TimedRotatingFileHandler(
    'app.log', when='midnight', interval=1, backupCount=7)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

root_path = abspath(join(dirname(__file__), os.pardir))
dotenv_path = join(root_path, '.env')
load_dotenv(dotenv_path, override=True)


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)


@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(days=1)


@app.route('/clear-cart-list', methods=['POST'])
def clear_cart_list():
    session.pop('cart_list', None)  # Clear 'cart-list' from session
    return jsonify(success=True)


@app.route('/add-cart', methods=['POST'])
def add_cart():
    """
    Endpoint to add an item to the cart.

    Expects 'shop_name' and 'shop_ob_id' in the POST form data.
    Adds the item to the session's 'cart_list'.
    """
    logging.info("in add_cart")
    try:
        shop_name = request.form.get('shop_name')
        shop_ob_id = request.form.get('shop_ob_id')

        if not shop_name or not shop_ob_id:
            return jsonify({'success': False, 'error': 'Missing shop_name or shop_ob_id'}), 400

        dict_items = {shop_ob_id: {'shop_name': shop_name}}
        if 'cart_list' in session:
            # logging.info(session['cart_list'])
            if shop_ob_id in session['cart_list']:
                logging.info(f"{shop_name} has already in cart.")
                return jsonify({'success': True, 'already_in': True}), 200
            else:
                session['cart_list'] = merge_dicts(
                    session['cart_list'], dict_items)
        else:
            session['cart_list'] = dict_items
        return jsonify({'success': True, 'already_in': False}), 200
    except Exception as e:
        logging.error(f"ERROR in add-cart: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/search-shops')
def search_shops():
    """
    Endpoint to search for shops by name.

    Retrieves shop information and location based on the provided name query parameter.
    """
    try:
        shop_name = request.args.get('name', '')
        logging.info(f'input shop name: {shop_name}')

        if not shop_name:
            return jsonify({'status': 'fail', 'message': 'Shop name is required'}), 400

        search_query = defaultdict(dict)
        search_query['name'] = {'text': shop_name}

        shops = search_db(search_query)

        if len(shops) == 0:
            return jsonify({'status': 'fail', 'message': 'No shops found'}), 200

        for ss in shops:
            ss['doc']['_id'] = ss['doc']['_id'].__str__()

        output = [shops[0]] if len(shops) > 1 else shops
        shop_name = output[0]['_id']
        shop_location = get_lat_lng(shop_name)

        return jsonify({'status': 'success', 'shop_info': output, 'shop_location': shop_location}), 200

    except Exception as e:
        logging.error(f"Error in search-shops: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/get-scheduling', methods=['GET', 'POST'])
def get_scheduling():
    """_summary_

    Returns:
        _type_: _description_
    """
    data = request.json
    shop_names = data['shops']

    travel_mode = data["travel_mode"]
    start_place = data['start_place']
    end_place = data['end_place']
    fixed_start = False
    fixed_end = False
    # TODO: if start==end
    if start_place != '' and start_place in shop_names:
        shop_names.insert(0, shop_names.pop(shop_names.index(start_place)))
        fixed_start = True
    elif start_place != '':
        shop_names.insert(0, start_place)
        fixed_start = True
    if end_place != '' and end_place in shop_names:
        shop_names.pop(shop_names.index(end_place))
        shop_names.append(end_place)
        fixed_end = True
    elif end_place != '':
        shop_names.append(end_place)
        fixed_end = True
    logging.info(f"shop name: {shop_names}")
    dis_dict, shortest_index, full_routes = get_travel_time_dictionary.get_route_dict(
        shop_names, travel_mode, fixed_start, fixed_end)
    logging.info(f"dis_dict: {dis_dict}")
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
def scheduling():
    output = {}
    if request.method == 'GET':
        if 'cart_list' in session:
            for shop_id, shop_info in session['cart_list'].items():
                location = get_lat_lng(shop_info['shop_name'])
                if location:
                    session['cart_list'][shop_id]['shop_location'] = location
            logging.info(session['cart_list'])
            output = session['cart_list']
    return render_template('scheduling.html', cart_list=output)


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':

        if 'search_by_filters' in request.form:
            if request.form['checkboxValue'] == 'false' and 'district' not in request.form and 'mrt' not in request.form:
                flash('Please select at least one location condition.', 'error')
                return redirect(url_for('index'))

        search_query = prepare_search_query(request.form)
        # selected_tags = []

        results = search_db(search_query)  # list of shop info
        len_results = len(results)
        if len_results == 0:
            flash('Store does not exist in the database.', 'error')
            return redirect(url_for('index'))
        for ss in results:
            ss['doc']['_id'] = ss['doc']['_id'].__str__()

        selected_tags = request.form.getlist('tags')
        for i in range(len_results):
            if 'tags' in results[i]:
                tag_data = data_for_radars(results[i]['tags'], selected_tags)
                results[i]['for_radar'] = tag_data

        taiwan_timezone = pytz.timezone('Asia/Taipei')
        cur_date = datetime.now(taiwan_timezone)
        day_of_week = cur_date.isoweekday() % 7
        cur_hour = cur_date.hour
        time_info = {
            'cur_date': cur_date,
            'cur_hour': cur_hour,
            'day_of_week': day_of_week
        }
        return render_template('search.html', search_result=results, time_info=time_info)
    return redirect(url_for('index'))


@app.errorhandler(400)
def bad_request(error):
    return render_template('400.html'), 400


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@ app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
