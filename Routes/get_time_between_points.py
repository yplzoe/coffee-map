from webdriver_manager.chrome import ChromeDriverManager
import sys
import os
from dotenv import load_dotenv
from os.path import join, dirname, abspath
import requests
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver import ActionChains, Keys
from selenium import webdriver
import time
from operator import itemgetter
from datetime import datetime, timezone
from module import MongoDB

root_path = abspath(join(dirname(__file__), os.pardir))
dotenv_path = join(root_path, '.env')
load_dotenv(dotenv_path, override=True)

uri = os.environ.get("MONGO_URI")


def get_route_estimate(origin, destination):
    """get estimate time of all travel mode

    Args:
        origin (_type_): can be (25.05304227910595, 121.55030567410216), address, 台北101
        destination (_type_): _description_
    """
    if isinstance(origin, tuple) and isinstance(destination, tuple):
        origin_str = str(origin[0])+","+str(origin[1])
        destination_str = str(destination[0])+","+str(destination[1])
        direction_url = f'https://www.google.com/maps/dir/{origin_str}/{destination_str}/'
    else:
        direction_url = f'https://www.google.com/maps/dir/{origin}/{destination}/'

    # print(direction_url)
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    chrome_driver_path = "/usr/local/bin/chromedriver"
    service = Service(executable_path=chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(direction_url)
    redirected_url = driver.current_url
    print("Redirected URL:", redirected_url)
    # driver.get(redirected_url)

    wait = WebDriverWait(driver, 10)
    wait.until(EC.visibility_of_element_located(
        (By.CSS_SELECTOR, '.FkdJRd.vRIAEd.dS8AEf')))

    parent_div = driver.find_element(
        By.XPATH, "//div[@class='FkdJRd vRIAEd dS8AEf']")

    mode_divs = parent_div.find_elements(By.XPATH, "//div[@data-travel_mode]")
    use_time = parent_div.find_elements(By.CSS_SELECTOR, '.Fl2iee.HNPWFe')
    output = {}
    output['result'] = {}
    for ch, ut in zip(mode_divs, use_time):
        label = ch.get_attribute("data-travel_mode")
        print(f'data-travel_mode: {label}')
        use_time_text = ut.text
        print("Estimated Time: ", use_time_text)
        output['result'][label] = use_time_text

    driver.quit()

    output['origin'] = origin
    output['destination'] = destination
    current_utc_time = datetime.now(timezone.utc)
    output['create_at'] = current_utc_time

    output_list = [output]
    mongo = MongoDB(host=None, port=27017, uri=uri)
    mongo.insert_list("coffee-map", "travel_time", output_list)
    mongo.close_connection()

    return output

# test
# origin = (25.05304227910595, 121.55030567410216)
# destination = (25.03850115585252, 121.5327103833683)
# result = get_route_estimate(origin, destination)
# print(result)
