from flask import Flask, request, jsonify, session, render_template
from collections import defaultdict
import logging


def search_shops():
    """
    Endpoint to search for shops by name.

    Retrieves shop information and location based on the provided name query parameter.
    """
    try:
        shop_name = request.args.get('name', '').strip()
        logging.info(f'input shop name: {shop_name}')

        if not shop_name:
            return jsonify({'status': 'fail', 'message': 'Shop name is required'}), 400

        search_query = defaultdict(dict)
        search_query['name'] = {'text': shop_name}

        shops = get_cafe_store(search_query)

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
        return jsonify({'status': 'fail', 'error': str(e)}), 500


def get_scheduling():
    """ Handle scheduling requests for shops.

    Returns:
        json: Best route and scheduling information.
    """
    data = request.json
    logging.info(f"schedule data: {data}")
    shop_names = data['shops']
    travel_mode = data["travel_mode"]
    start_place = data['start_place']
    end_place = data['end_place']

    shop_names, fixed_start, fixed_end = handle_start_end_place(
        shop_names, start_place, end_place)
    logging.info(f"shop name: {shop_names}")

    # Get travel time dictionary and perform tabu search
    dis_dict, shortest_index, full_routes = get_travel_time_dictionary.get_route_dict(
        shop_names, travel_mode, fixed_start, fixed_end)
    best_solution, best_obj = tabu_search.tabu_search(
        shop_names, 100, 2**len(shop_names), dis_dict, fixed_start, fixed_end)
    logging.info(f"best_solution: {best_solution}, best_obj: {best_obj}")

    # Get route information
    polyline_list = get_travel_time_dictionary.return_all_path(
        best_solution, shortest_index, full_routes)
    geojson_list = get_travel_time_dictionary.turn_into_geojson(polyline_list)

    return jsonify({'status': 'success', 'best_route': geojson_list, 'best_solution': best_solution, 'best_obj': best_obj}), 200


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


def search():
    if request.method == 'POST':
        try:
            if 'search_by_filters' in request.form:
                if request.form['checkboxValue'] == 'false' and 'district' not in request.form and 'mrt' not in request.form:
                    flash('Please select at least one location condition.', 'error')
                    return redirect(url_for('index'))

            search_query = prepare_search_query(request.form)

            results = get_cafe_store(search_query)  # list of shop info

            len_results = len(results)
            if len_results == 0:
                flash('Store does not exist in the database.', 'error')
                return redirect(url_for('index'))

            for ss in results:
                ss['doc']['_id'] = ss['doc']['_id'].__str__()

            selected_tags = request.form.getlist('tags')
            for i in range(len_results):
                if 'tags' in results[i]:
                    tag_data = data_for_radars(
                        results[i]['tags'], selected_tags)
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
        except Exception as e:
            logging.error(f"Error in search: {e}")
            return jsonify({'status': 'fail', 'error': str(e)}), 500
    return redirect(url_for('index'))


def register_shop_routes(app):
    app.add_url_rule('/search-shops', search_shops, methods=['GET', 'POST'])
    app.add_url_rule('/get-scheduling', get_scheduling,
                     methods=['GET', 'POST'])
    app.add_url_rule('/scheduling', 'scheduling',
                     scheduling, methods=['GET', 'POST'])
    app.add_url_rule('/search', 'search', search, methods=['GET', 'POST'])
