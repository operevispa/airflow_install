from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import cv2
import numpy as np
import os
from datetime import datetime
import logging

# Настройки DAG
default_args = {
    'owner': 'my_airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'watermark_processor',
    default_args=default_args,
    description='DAG for adding watermarks to images',
    schedule_interval=timedelta(days=1),
)

def add_watermark(input_path, output_path):
    """
    Добавляет водяной знак на изображение
    """
    try:
        # Создаем выходную директорию, если она не существует
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Читаем изображение
        image = cv2.imread(input_path)
        if image is None:
            raise ValueError(f"Unable to read image: {input_path}")

        # Получаем размеры изображения
        height, width = image.shape[:2]
        
        # Настраиваем размер шрифта в зависимости от размера изображения
        font_scale = min(width, height) / 1000.0
        
        # Получаем текущую дату для водяного знака
        watermark_text = datetime.now().strftime("%Y-%m-%d")
        
        # Настройки шрифта
        font = cv2.FONT_HERSHEY_SIMPLEX
        thickness = max(1, int(font_scale * 2))
        
        # Получаем размеры текста
        (text_width, text_height), baseline = cv2.getTextSize(
            watermark_text, font, font_scale, thickness
        )
        
        # Вычисляем позицию для водяного знака (правый нижний угол)
        x = width - text_width - 10
        y = height - 10
        
        # Создаем полупрозрачный белый фон для текста
        overlay = image.copy()
        cv2.rectangle(
            overlay,
            (x - 5, y - text_height - 5),
            (x + text_width + 5, y + 5),
            (255, 255, 255),
            -1
        )
        
        # Применяем прозрачность
        alpha = 0.7
        image = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)
        
        # Добавляем текст
        cv2.putText(
            image,
            watermark_text,
            (x, y),
            font,
            font_scale,
            (0, 0, 0),
            thickness
        )
        
        # Сохраняем результат
        cv2.imwrite(output_path, image)
        logging.info(f"Successfully processed {input_path}")
        
    except Exception as e:
        logging.error(f"Error processing {input_path}: {str(e)}")
        raise

def process_images():
    """
    Обрабатывает все изображения в входной директории
    """
    input_dir = '/opt/airflow/dags/dogs'
    output_dir = '/opt/airflow/dags/dogs_prep'
    
    # Поддерживаемые форматы
    supported_formats = ('.png', '.jpg', '.jpeg')
    
    # Создаем выходную директорию
    os.makedirs(output_dir, exist_ok=True)
    
    # Обрабатываем каждый файл
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(supported_formats):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, f"watermarked_{filename}")
            
            try:
                add_watermark(input_path, output_path)
            except Exception as e:
                logging.error(f"Failed to process {filename}: {str(e)}")
                continue

# Определяем задачу
process_images_task = PythonOperator(
    task_id='process_images',
    python_callable=process_images,
    dag=dag,
)

# Определяем последовательность выполнения
process_images_task