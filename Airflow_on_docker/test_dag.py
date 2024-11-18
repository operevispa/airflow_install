from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def test_libraries():
    # Тест импорта библиотек
    import cv2
    import numpy as np
    import pandas as pd
    import torch
    import tensorflow as tf
  
    
    print("All libraries imported successfully!")

with DAG(
    'test_libraries',
    default_args=default_args,
    description='Test installed libraries',
    schedule_interval=timedelta(days=1),
) as dag:

    test_task = PythonOperator(
        task_id='test_libraries',
        python_callable=test_libraries,
    )