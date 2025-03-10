from pymongo import MongoClient
from datetime import datetime, timezone
from operator import itemgetter
import csv
import multiprocessing
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver import ActionChains, Keys
from selenium import webdriver
import pymongo
import time
from dotenv import load_dotenv, find_dotenv
from os.path import join, dirname, abspath
import os
from module import MongoDB
import logging
from logging.handlers import TimedRotatingFileHandler
import json

selenium_logger = logging.getLogger("selenium_reviews")
selenium_logger.setLevel(logging.INFO)


log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, "log_get_reviews.log")
selenium_handler = TimedRotatingFileHandler(
    log_file, when="midnight", interval=1, backupCount=7)
selenium_handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
selenium_handler.setFormatter(formatter)
selenium_logger.addHandler(selenium_handler)


def wait_for_element_location_to_be_stable(element):
    initial_location = element.location
    previous_location = initial_location
    start_time = time.time()
    while time.time() - start_time < 1:
        current_location = element.location
        if current_location != previous_location:
            previous_location = current_location
            start_time = time.time()
        time.sleep(0.4)


def accept_policy(driver):
    try:
        accept_policy = driver.find_elements(By.TAG_NAME, 'button')
        for button in accept_policy:
            if button.text == "Accept all":
                logging.debug(button.text)
                button.click()
                break
    except TimeoutException:
        logging.error("Cookie policy button not found or unable to click.")


def click_more_buttons(driver):
    more_buttons = 0
    # Find buttons within the current 'jftiEf' element
    body_elements = driver.find_elements(By.CLASS_NAME, 'jftiEf')
    for body in body_elements:
        # Iterate over each button within the current 'jftiEf' element
        buttons = body.find_elements(By.CLASS_NAME, "w8nwRe")
        for button in buttons:
            if button.text == "全文":  # Check if the button text is "More"
                more_buttons += 1
                button.click()
            # this will tell us how many more buttons are currently loaded
            logging.debug(more_buttons)
            logging.debug(body.text)


def get_single_shop_reviews(name):
    website = 'https://www.google.com.tw/maps'
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-application-cache')
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-ssl-errors=yes')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument("--lang=zh-TW")
    options.add_argument("--window-size=2560,1440")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36")
    options.add_experimental_option(
        "prefs", {"intl.accept_languages": "zh-TW"})  # need to force it
    # chrome_driver_path = "/usr/local/bin/chromedriver"
    # service = Service(executable_path=chrome_driver_path)
    driver = webdriver.Remote(
        command_executor='http://remote_chromedriver:4444/wd/hub',
        keep_alive=True,
        options=options
    )
    # driver = webdriver.Chrome(service=service, options=options)
    driver.get(website)
    get_url = driver.current_url

    logging.info("The current url is:"+str(get_url))
    actionChains = ActionChains(driver)

    actionChains.send_keys(name)  # Send keys to the element
    actionChains.send_keys(Keys.ENTER)  # Press Enter key
    actionChains.perform()  # Perform the actions
    ######
    wait = WebDriverWait(driver, 20)
    try:
        wait.until(EC.presence_of_all_elements_located(
            (By.CLASS_NAME, "MyEned")))
    except Exception as e:
        logging.error(f"can not catch MyEned: {e}")

    accept_policy(driver)

    try:
        testing = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'button')))
        logging.debug(testing.text)
    except TimeoutException:
        logging.error("button element not found within the specified time.")

    try:
        buttons = driver.find_elements(By.CLASS_NAME, "Gpq6kf ")
        actionChains.move_to_element(buttons[1]).perform()
        logging.debug(buttons[1].text)
        buttons[1].click()

        # results = driver.find_elements(By.CLASS_NAME, 'MyEned')
        end_of_reviews = driver.find_elements(By.CLASS_NAME, 'qjESne ')

        break_condition = False
    except Exception as e:
        logging.error(f"cannot get buttons: {e}")

    results = {}

    while not break_condition:
        click_more_buttons(driver)
        time.sleep(2)
        try:
            actionChains.scroll_to_element(end_of_reviews[-1]).perform()

            results = wait.until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "MyEned")))
            temp = results[-1]
            wait_for_element_location_to_be_stable(temp)
        except Exception as e:
            break_condition = True
            logging.error(f"Error: {e}")

        # if len(results) > 100:
            # break_condition = True

    output = []

    for i, result in enumerate(results, start=1):
        span = result.find_element(By.CLASS_NAME, 'wiI7pd')
        logging.debug(f"Result {i}: {span.text}")  # user name & rating not yet
        output.append(span.text)

    get_url = driver.current_url
    logging.info("The current url is:"+str(get_url))

    time.sleep(3)
    driver.quit()
    return output


def get_all_shop_reviews():
    dotenv_path = 'plugins/.env'
    load_dotenv(dotenv_path, override=True)

    uri = os.environ.get("MONGO_URI")
    mongo = MongoDB(None, None, uri)
    client = MongoClient(uri)
    mongo_db = client['coffee-map']
    mongo_collection = mongo_db['raw_shop_info']

    re_collection = mongo_db['more_reviews']
    output_json = []

    count = 0

    for document in mongo_collection.find():
        if count >= 1:
            logging.info(f"count: {count}")
            break
        count += 1

        name = document.get('_id')

        re_skip = re_collection.find_one({"name": name})
        # if re_skip:
        #     continue

        current_utc_time = datetime.now(timezone.utc)
        review_output = []
        # try:
        # address = document['place_detail'].get('formatted_address')
        name = 'Piccolo Angolo角落咖啡館'
        address = '10491台灣台北市中山區松江路124巷19-1號'
        search_str = address+' '+name
        logging.info('Start crawling')
        review_output = get_single_shop_reviews(search_str)
        # except Exception as e:
        #     logging.error(f"error: {e}")
        #     review_output.append('error')

        # if re_skip:
        #     # If document exists, update it with new reviews
        #     re_collection.update_many(
        #         {"name": name}, {"$set": {"reviews": review_output, "update_at": current_utc_time}})
        #     logging.info(f"Updated reviews for {name}")
        #     updated_data = {
        #         "name": name,
        #         "reviews": review_output,
        #         "update_at": current_utc_time
        #     }
        #     output_json.append(updated_data)
        # else:
        #     insert_data = {
        #         "name": name,
        #         "reviews": review_output,
        #         "create_at": current_utc_time,
        #         "update_at": current_utc_time
        #     }
        #     output_json.append(insert_data)
        #     mongo.insert_list("coffee-map", "more_reviews", insert_data)

    client.close()
    mongo.close_connection()

    # current_date = datetime.now().strftime('%Y-%m-%d')
    # filename = f'files/more_reviews_{current_date}.json'
    # try:
    #     with open(filename, 'a') as json_file:
    #         json.dump(output_json, json_file)
    #     logging.info("Data write to file completed.")
    # except FileNotFoundError:
    #     with open(filename, 'w') as json_file:
    #         json.dump(output_json, json_file)
    #     logging.info("Data write to file completed.")
