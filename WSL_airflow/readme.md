1. Установить wsl в PowerShell с правами администратора  
`wsl --install`  
Перезагрузить компьютер  

2. Настройка Ubuntu:
    ```# Обновление пакетов
        sudo apt update && sudo apt upgrade -y

        # Установка необходимых инструментов
        sudo apt install -y python3-pip python3-venv git curl wget
    ```

3. Установим virtualenv глобально:  
    `sudo apt update sudo apt install python3-virtualenv`

4. Создадим виртуальное окружение с помощью virtualenv:  
    `virtualenv .venv`

5. Активируем виртуальное окружение:  
    `source .venv/bin/activate`

6. Установим Airflow в виртуальном окружении:  
    `pip install 'apache-airflow==2.10.3'  `

7. Настроим переменную окружения AIRFLOW_HOME:
В вашем случае, учитывая, что вы работаете в проекте nlp_airflow_project, лучше установить AIRFLOW_HOME в директорию вашего проекта:

`echo 'export AIRFLOW_HOME=/home/shose/nlp_airflow_project/airflow' >> ~/.bashrc source ~/.bashrc`


8. Установим PostgreSQL и зависимости:
        ```
        sudo apt-get update      
        sudo apt-get install postgresql postgresql-contrib       
        sudo apt-get install python3-dev libpq-dev    
        ```

 - Установим PostgreSQL:  

    `pip install psycopg2-binary`

 - Создадим PostgreSQL пользователя и базу Airflow:  

    `sudo -u postgres psql  CREATE USER airflow WITH PASSWORD 'your_password';`  
    `CREATE DATABASE airflow; `  
    `GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;`  
    `\q`  

 - Обновим конфигурацию Airflow (`~/airflow/airflow.cfg`):  
    Изменить SQLite соединение to PostgreSQL:
    ```
    [core]
    sql_alchemy_conn = postgresql+psycopg2://airflow:your_password@localhost/airflow
    ```

9. Инициализация базы данных Airflow:

    `airflow db init`


10. Создание пользователя администратора:

```
    airflow users create \   
    --username admin \     
    --firstname Admin \     
    --lastname Admin \   
    --role Admin \   
    --email admin@example.com \  
    --password admin
```
11. Настройка конфигурационного файла (airflow.cfg):
```
    [core]
    # Путь к DAGs
    dags_folder = /home/shose/nlp_airflow_project/airflow/dags
    # База данных
    sql_alchemy_conn = sqlite:///home/shose/nlp_airflow_project/airflow/airflow.db
    # Executor
    executor = LocalExecutor
    [webserver]
    # Порт веб-интерфейса
    web_server_port = 8080
    # Аутентификация
    authenticate = True
    auth_backend = airflow.auth.backend.session
```

12. Создайте файл requirements.txt:

```
    apache-airflow==2.6.3
    nltk==3.8.1
    spacy==3.5.3
    textblob==0.17.1
    pandas==2.0.3
    rake-nltk==1.0.6
```


13. Установите зависимости:

`pip install -r requirements.txt`

    - Установите русскую модель spaCy:

        `python -m spacy download ru_core_news_lg`



    - Загрузите необходимые данные NLTK:

        ```
            python -c "import nltk;  
            nltk.download('punkt'); 
            nltk.download('stopwords'); 
            nltk.download('averaged_perceptron_tagger')"
        ```

14. Создадим сервисные файлы, чтобы автоматизировать процесс управления:  
    - Создадим сервисный файл для веб-сервера:
    `sudo nano /etc/systemd/system/airflow-webserver.service`

    Вставьте следующее содержимое (замените shose на ваше имя пользователя):
    ```
        [Unit]
        Description=Airflow webserver daemon
        After=network.target

        [Service]
        User=shose
        Group=shose
        Type=simple
            Environment="PATH=/home/shose/nlp_airflow_project/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
        Environment="AIRFLOW_HOME=/home/shose/nlp_airflow_project/airflow"
        ExecStart=/home/shose/nlp_airflow_project/.venv/bin/airflow webserver
        Restart=on-failure
        RestartSec=5s
        PrivateTmp=true

        [Install]
        WantedBy=multi-user.target

    ```

    - Создадим сервисный файл для планировщика:

        `sudo nano /etc/systemd/system/airflow-scheduler.service`
    ```
    [Unit]
    Description=Airflow scheduler daemon
    After=network.target

    [Service]
    User=shose
    Group=shose
    Type=simple
    Environment="PATH=/home/shose/nlp_airflow_project/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    Environment="AIRFLOW_HOME=/home/shose/nlp_airflow_project/airflow"
    ExecStart=/home/shose/nlp_airflow_project/.venv/bin/airflow scheduler
    Restart=on-failure
    RestartSec=5s
    PrivateTmp=true

    [Install]
    WantedBy=multi-user.target
    ```

15. Перезагрузим демон systemd и запустим сервисы:
    ```
    sudo systemctl daemon-reload 
    sudo systemctl enable airflow-webserver 
    sudo systemctl enable airflow-scheduler 
    sudo systemctl start airflow-webserver 
    sudo systemctl start airflow-scheduler
    ```
16. Проверим статус сервисов:  

```   
    sudo systemctl status airflow-webserver 
    sudo systemctl status airflow-scheduler
```
17. Теперь вы можете открыть веб-интерфейс Airflow:  
http://localhost:8080

    Логин: admin  
    Пароль: admin  


Использование декораторов (`@dag`, `@task`, `@task_group`) в Apache Airflow добавляет ясности и уменьшает количество кода, необходимого для определения вашего DAG и задач:

- @dag используется для определения функции как DAG. Это синтаксический сахар, который позволяет легко определить и настроить параметры DAG'а одним декоратором.

- @task позволяет определять задачи внутри DAG как отдельные функции. Декоратор автоматически управляет созданием экземпляров задач и их запуском на основе зависимостей.

- @task_group  позволяет организовать и управлять несколькими связанными задачами как одной логической группой, что упрощает параллельное выполнение связанных задач.


Для перезапуска проекта надо:
1. Зайти в папку с проектом
2. Запустить базу:
    `sudo service postgresql start`
3. Запустить окружение:
    `source .venv/bin/activate`
4. Активировать сервисы:
     `sudo systemctl start airflow-webserver`  
    `sudo systemctl start airflow-scheduler`
