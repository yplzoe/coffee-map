from flask import Flask, request, jsonify, session
import logging


def merge_dicts(dict1, dict2):
    if isinstance(dict1, list) and isinstance(dict2, list):
        return dict1+dict2
    if isinstance(dict1, dict) and isinstance(dict2, dict):
        return dict(list(dict1.items())+list(dict2.items()))
    return False


def clear_cart_list():
    session.pop('cart_list', None)  # Clear 'cart-list' from session
    return jsonify(success=True)


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


def register_cart_routes(app: Flask):
    app.add_url_rule('/clear-cart-list', 'clear_cart_list',
                     clear_cart_list, methods=['DELETE'])
    app.add_url_rule('/add-cart', 'add_cart', add_cart, methods=['POST'])
