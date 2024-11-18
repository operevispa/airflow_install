from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import cv2
import numpy as np
import os

# Определение путей
INPUT_DIR = '/opt/airflow/dags/dogs/'
OUTPUT_DIR = '/opt/airflow/dags/dogs_final/'

# Создание директорий для выходных данных
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/binary", exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/shifted", exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/filtered", exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/normalized", exist_ok=True)

def load_and_normalize_image(**context):
    """Загрузка и нормализация изображения"""
    processed_files = []
    for filename in os.listdir(INPUT_DIR):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            # Загрузка изображения
            img_path = os.path.join(INPUT_DIR, filename)
            img = cv2.imread(img_path)
            
            if img is not None:
                # Нормализация изображения
                normalized = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)
                
                # Сохранение нормализованного изображения
                output_path = os.path.join(OUTPUT_DIR, "normalized", filename)
                cv2.imwrite(output_path, normalized)
                
                processed_files.append(filename)
    
    # Передача списка всех обработанных файлов
    context['task_instance'].xcom_push(key='processed_files', value=processed_files)

def binarize_image(**context):
    """Бинаризация изображения"""
    filenames = context['task_instance'].xcom_pull(key='processed_files')
    if filenames:
        for filename in filenames:
            # Загрузка нормализованного изображения
            img_path = os.path.join(OUTPUT_DIR, "normalized", filename)
            img = cv2.imread(img_path, 0)  # Загрузка в градациях серого
            
            # Бинаризация
            _, binary = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
            
            # Сохранение результата
            output_path = os.path.join(OUTPUT_DIR, "binary", filename)
            cv2.imwrite(output_path, binary)

def shift_image(**context):
    """Сдвиг изображения"""
    filenames = context['task_instance'].xcom_pull(key='processed_files')
    if filenames:
        for filename in filenames:
            # Загрузка нормализованного изображения
            img_path = os.path.join(OUTPUT_DIR, "normalized", filename)
            img = cv2.imread(img_path)
            
            # Матрица сдвига
            rows, cols = img.shape[:2]
            M = np.float32([[1, 0, 100], [0, 1, 50]])
            
            # Применение сдвига
            shifted = cv2.warpAffine(img, M, (cols, rows))
            
            # Сохранение результата
            output_path = os.path.join(OUTPUT_DIR, "shifted", filename)
            cv2.imwrite(output_path, shifted)

def apply_filter(**context):
    """Применение фильтра"""
    filenames = context['task_instance'].xcom_pull(key='processed_files')
    if filenames:
        for filename in filenames:
            # Загрузка нормализованного изображения
            img_path = os.path.join(OUTPUT_DIR, "normalized", filename)
            img = cv2.imread(img_path)
            
            # Применение фильтра Гаусса
            filtered = cv2.GaussianBlur(img, (5, 5), 0)
            
            # Сохранение результата
            output_path = os.path.join(OUTPUT_DIR, "filtered", filename)
            cv2.imwrite(output_path, filtered)

# Определение DAG
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'parallel_image_processing',
    default_args=default_args,
    description='Параллельная обработка изображений',
    schedule_interval=timedelta(days=1),
    catchup=False
)

# Определение задач
normalize_task = PythonOperator(
    task_id='normalize_image',
    python_callable=load_and_normalize_image,
    dag=dag
)

binarize_task = PythonOperator(
    task_id='binarize_image',
    python_callable=binarize_image,
    dag=dag
)

shift_task = PythonOperator(
    task_id='shift_image',
    python_callable=shift_image,
    dag=dag
)

filter_task = PythonOperator(
    task_id='apply_filter',
    python_callable=apply_filter,
    dag=dag
)

# Определение зависимостей
normalize_task >> [binarize_task, shift_task, filter_task]