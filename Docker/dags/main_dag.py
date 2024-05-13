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
import get_place_detail
import get_map_data
import clean_data
import upload_s3

#! remove test before running

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
    dag_id='coffee_map_fetch_data',
    schedule_interval='@monthly',
    # schedule_interval='@once',
    default_args=default_args,
    catchup=False,
    tags=['coffee_map']
) as dag:

    start_task = DummyOperator(task_id='start_task')

    search_cafe_shop = PythonOperator(
        task_id='search_cafe',
        python_callable=get_map_data.search_cafe
    )

    upload_files = PythonOperator(
        task_id='upload_files',
        python_callable=upload_s3.upload_json_to_s3
    )

    clean_from_test_to_raw = PythonOperator(
        task_id='clean_data',
        python_callable=clean_data.clean_data_from_test_to_raw
    )

    place_details = PythonOperator(
        task_id='get_place_detail',
        python_callable=get_place_detail.get_all_details,
    )

    upload_files_2 = PythonOperator(
        task_id='upload_files_2',
        python_callable=upload_s3.upload_json_to_s3
    )

    more_reviews = PythonOperator(
        task_id='get_more_reviews',
        python_callable=get_reviews.get_all_shop_reviews,
    )

    upload_files_3 = PythonOperator(
        task_id='upload_files_3',
        python_callable=upload_s3.upload_json_to_s3
    )

    shop_classified = PythonOperator(
        task_id='get_each_shop_classified_tag',
        python_callable=cls_shop.get_classified_tag,
    )
    end_task = DummyOperator(task_id='end_task')

start_task >> search_cafe_shop >> [
    upload_files, clean_from_test_to_raw] >> place_details >> [upload_files_2, more_reviews] >> upload_files_3 >> shop_classified >> end_task
