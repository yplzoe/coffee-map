import time
import os
import logging
import urllib.request
import json
from pathlib import Path
from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dummy import DummyOperator
import pyarrow.csv as pv
import pyarrow.parquet as pq
import datetime
from datetime import datetime, timedelta
import pytz
import airflow.providers as ap
import airflow
import classify_shop as cls_shop
import get_reviews
from selenium import webdriver
from selenium.webdriver.common.by import By

logging.basicConfig(filename='airflow.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def test_selenium():
    logging.info("Test Execution Started")
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-ssl-errors=yes')
    options.add_argument('--ignore-certificate-errors')
    driver = webdriver.Remote(
        command_executor='http://remote_chromedriver:4444/wd/hub',
        options=options
    )
    get_url = driver.current_url
    # maximize the window size
    driver.maximize_window()
    time.sleep(2)
    # navigate to browserstack.com
    driver.get("https://www.browserstack.com/")
    time.sleep(2)
    # click on the Get started for free button
    result = driver.find_element(By.ID, 'signupModalProductButton')
    logging.info(f"find button text: {result.text}")
    time.sleep(2)
    # close the browser
    driver.close()
    driver.quit()
    logging.info("Test Execution Successfully Completed!")


def dum_test():
    logging.info("dum_test")


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='coffee_map_fetch_data_2',
    # schedule_interval='@monthly',
    schedule_interval='@once',
    default_args=default_args,
    catchup=False,
    tags=['coffee_map']
) as dag:

    start_task = DummyOperator(task_id='start_task')
    # more_reviews = PythonOperator(
    #     task_id='get_more_reviews',
    #     python_callable=test_selenium,
    # )

    more_reviews = PythonOperator(
        task_id='get_more_reviews',
        python_callable=get_reviews.get_all_shop_reviews,
    )

    more_reviews_2 = PythonOperator(
        task_id='get_more_reviews_2',
        python_callable=get_reviews.get_all_shop_reviews,
    )

    shop_classified = PythonOperator(
        task_id='get_each_shop_classified_tag',
        python_callable=cls_shop.get_classified_tag,
    )
    end_task = DummyOperator(task_id='end_task')

start_task >> more_reviews >> shop_classified >> end_task
