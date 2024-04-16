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
    # schedule_interval='@monthly',
    schedule_interval='@once',
    default_args=default_args,
    catchup=False,
    tags=['coffee_map']
) as dag:

    start_task = DummyOperator(task_id='start_task')

    shop_classified = PythonOperator(
        task_id='get_each_shop_classified_tag',
        python_callable=cls_shop.get_classified_tag,
    )
    end_task = DummyOperator(task_id='end_task')

start_task >> shop_classified >> end_task
