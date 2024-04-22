from app_fun import search_db
from collections import defaultdict
from flask import Flask, request, jsonify, make_response, render_template, redirect, url_for
from flask_restful import Resource, Api
import logging
import time

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
api = Api(app)


@app.route('/search', methods=['POST'])
def search():
    # search_query = None
    search_query = defaultdict(dict)
    if request.method == 'POST':
        if 'search_by_name' in request.form:
            search_query['name'] = {'text': request.form['shop_name']}
        elif 'search_by_filters' in request.form:
            selected_district = request.form['district']
            selected_tags = request.form.getlist('tags')
            search_query['filters'] = {
                'district': selected_district, 'tags': selected_tags}
    logging.info(f"search query: {search_query}")
    # 根據條件得到所有店家
    results = search_db(search_query)  # list of shop info

    return render_template('search.html', search_result=results)


@ app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)
