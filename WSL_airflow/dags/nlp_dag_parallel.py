from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import nltk
import spacy
from textblob import TextBlob
import pandas as pd
from rake_nltk import Rake
import os
import json

# DAG аргументы
default_args = {
    'owner': 'nlp_airflow_1',
    'depends_on_past': False,
    'start_date': datetime(2024, 10, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# создание DAG
dag = DAG(
    'nlp_processing_pipeline',
    default_args=default_args,
    description='Advanced NLP processing DAG',
    schedule_interval=timedelta(days=1),
)

def initialize_nlp(**context):
    """Initialize NLP components"""
    # Загрузка всех пакетов NLTK
    nltk.download('all')
    
    # Загрузка русской модели spaCy
    if not spacy.util.is_package('ru_core_news_lg'):
        spacy.cli.download('ru_core_news_lg')
    
    return "NLP components initialized"

def load_text(**context):
    """Load text from file"""
    # пример текста, если текст не загружен
    default_text = """
    Обработка естественного языка (NLP) - это раздел искусственного интеллекта,
    который помогает компьютерам понимать, интерпретировать и манипулировать
    человеческим языком. Эта технология используется во многих приложениях,
    от служб перевода до чат-ботов и виртуальных помощников.
    """
    
    try:
        with open('3110.txt', 'r', encoding='utf-8') as file:
            text = file.read()
    except:
        text = default_text
    
    context['task_instance'].xcom_push(key='input_text', value=text)
    return text

def basic_text_stats(**context):
    """Basic text statistics"""
    text = context['task_instance'].xcom_pull(task_ids='load_text', key='input_text')
    tokens = nltk.word_tokenize(text)
    stats = {
        'word_count': len(tokens),
        'unique_words': len(set(tokens)),
        'sentence_count': len(nltk.sent_tokenize(text))
    }
    context['task_instance'].xcom_push(key='text_stats', value=stats)
    return stats

def sentiment_analysis(**context):
    """Sentiment analysis"""
    text = context['task_instance'].xcom_pull(task_ids='load_text', key='input_text')
    blob = TextBlob(text)
    sentiment = {
        'polarity': blob.sentiment.polarity,
        'subjectivity': blob.sentiment.subjectivity
    }
    context['task_instance'].xcom_push(key='sentiment', value=sentiment)
    return sentiment

def pos_tagging(**context):
    """POS tagging"""
    text = context['task_instance'].xcom_pull(task_ids='load_text', key='input_text')
    nlp = spacy.load('ru_core_news_lg')
    doc = nlp(text)
    pos_tags = [(token.text, token.pos_) for token in doc]
    context['task_instance'].xcom_push(key='pos_tags', value=pos_tags)
    return pos_tags

def named_entity_recognition(**context):
    """Named Entity Recognition"""
    text = context['task_instance'].xcom_pull(task_ids='load_text', key='input_text')
    nlp = spacy.load('ru_core_news_lg')
    doc = nlp(text)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    context['task_instance'].xcom_push(key='entities', value=entities)
    return entities

def extract_keywords(**context):
    """Extract keywords"""
    text = context['task_instance'].xcom_pull(task_ids='load_text', key='input_text')
    rake = Rake(language='russian')
    rake.extract_keywords_from_text(text)
    keywords = rake.get_ranked_phrases()
    context['task_instance'].xcom_push(key='keywords', value=keywords)
    return keywords

def summarize_results(**context):
    """Summarize all results"""

    
    ti = context['task_instance']
    
    text_stats = ti.xcom_pull(task_ids='basic_stats', key='text_stats')
    sentiment = ti.xcom_pull(task_ids='sentiment', key='sentiment')
    pos_tags = ti.xcom_pull(task_ids='pos_tagging', key='pos_tags')
    entities = ti.xcom_pull(task_ids='ner', key='entities')
    keywords = ti.xcom_pull(task_ids='keywords', key='keywords')
    
    summary = {
        'text_statistics': text_stats,
        'sentiment_analysis': sentiment,
        'pos_tags': pos_tags[:10],  
        'named_entities': entities,
        'keywords': keywords[:5]  
    }
    
    # Сохраняем результаты в JSON файл
    try:
        with open('/home/shose/nlp_airflow_project/airflow/dags/nlp_results.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=4)
        print("Results successfully saved to JSON file")
    except Exception as e:
        print(f"Error saving JSON file: {str(e)}")
    
    return summary


# Создание задач
init_nlp_task = PythonOperator(
    task_id='init_nlp',
    python_callable=initialize_nlp,
    provide_context=True,
    dag=dag,
)

load_text_task = PythonOperator(
    task_id='load_text',
    python_callable=load_text,
    provide_context=True,
    dag=dag,
)

basic_stats_task = PythonOperator(
    task_id='basic_stats',
    python_callable=basic_text_stats,
    provide_context=True,
    dag=dag,
)

sentiment_task = PythonOperator(
    task_id='sentiment',
    python_callable=sentiment_analysis,
    provide_context=True,
    dag=dag,
)

pos_tag_task = PythonOperator(
    task_id='pos_tagging',
    python_callable=pos_tagging,
    provide_context=True,
    dag=dag,
)

ner_task = PythonOperator(
    task_id='ner',
    python_callable=named_entity_recognition,
    provide_context=True,
    dag=dag,
)

keywords_task = PythonOperator(
    task_id='keywords',
    python_callable=extract_keywords,
    provide_context=True,
    dag=dag,
)

summary_task = PythonOperator(
    task_id='summarize',
    python_callable=summarize_results,
    provide_context=True,
    dag=dag,
)

# Определение зависимостей
init_nlp_task >> load_text_task

# параллельные задачи после загрузки текста
load_text_task >> [
    basic_stats_task,
    sentiment_task,
    pos_tag_task,
    ner_task,
    keywords_task
] >> summary_task
