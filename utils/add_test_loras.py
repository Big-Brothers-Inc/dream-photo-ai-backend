#!/usr/bin/env python
import os
import sys
import psycopg2
import psycopg2.extras
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Добавляем путь к корневой директории проекта
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)
project_dir = os.path.dirname(backend_dir)
sys.path.append(backend_dir)

# Настройки подключения к базе данных (из .env)
db_config = {
    "host": "localhost",
    "port": 5432,
    "database": "dream_photo",
    "user": "serzhbigulov",
    "password": ""
}

logger.info(f"Параметры подключения к БД: хост={db_config['host']}, база={db_config['database']}, пользователь={db_config['user']}")

def connect_to_db():
    """Подключение к базе данных"""
    try:
        conn = psycopg2.connect(**db_config)
        logger.info(f"Успешное подключение к базе данных {db_config['database']} на {db_config['host']}:{db_config['port']}")
        return conn
    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        return None

def add_test_lora_models(conn):
    """Добавление тестовых LoRA моделей в базу данных"""
    
    # Список тестовых моделей
    test_loras = [
        {
            "name": "Kodak Motion Picture",
            "description": "Стилизация под пленочную фотографию Kodak",
            "lora_url": "https://civitai.com/api/download/models/805021?type=Model&format=SafeTensor&token=ae82acec6ad7050b7f1e3654da2bb265",
            "trigger_phrase": "Kodak Motion Picture Film style , Analog photography",
            "category": "style",
            "default_weight": 0.8
        },
        {
            "name": "Magazine Cover",
            "description": "Стилизация под обложку журнала",
            "lora_url": "https://civitai.com/api/download/models/834917?type=Model&format=SafeTensor&token=ae82acec6ad7050b7f1e3654da2bb265",
            "trigger_phrase": "magazine_style , magazine_cover",
            "category": "style",
            "default_weight": 0.7
        },
        {
            "name": "Cyberpunk 2077",
            "description": "Стилизация под игру Cyberpunk 2077",
            "lora_url": "https://civitai.com/api/download/models/747534?type=Model&format=SafeTensor&token=ae82acec6ad7050b7f1e3654da2bb265",
            "trigger_phrase": "cyberpunk , anime",
            "category": "style",
            "default_weight": 0.9
        },
        {
            "name": "Dune",
            "description": "Стилизация под фильм Dune",
            "lora_url": "https://civitai.com/api/download/models/865256?type=Model&format=SafeTensor&token=ae82acec6ad7050b7f1e3654da2bb265",
            "trigger_phrase": "in style of Dune movie",
            "category": "style",
            "default_weight": 0.75
        }
    ]
    
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Проверка на дубликаты перед вставкой
    for lora in test_loras:
        try:
            # Проверяем, существует ли модель с таким именем
            cursor.execute('SELECT COUNT(*) FROM "ExtraLora" WHERE name = %s', (lora["name"],))
            exists = cursor.fetchone()["count"] > 0
            
            if exists:
                logger.info(f"Модель '{lora['name']}' уже существует, пропускаем.")
                continue
            
            # Вставляем новую модель
            insert_query = '''
                INSERT INTO "ExtraLora" 
                (name, description, lora_url, trigger_phrase, default_weight, category, is_active, created_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING extra_lora_id
            '''
            
            cursor.execute(
                insert_query, 
                (
                    lora["name"],
                    lora["description"],
                    lora["lora_url"],
                    lora["trigger_phrase"],
                    lora["default_weight"],
                    lora["category"],
                    True,
                    datetime.now()
                )
            )
            
            lora_id = cursor.fetchone()["extra_lora_id"]
            conn.commit()
            logger.info(f"Добавлена модель '{lora['name']}' с ID: {lora_id}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Ошибка при добавлении модели '{lora['name']}': {e}")
    
    cursor.close()

def main():
    # Подключаемся к базе данных
    conn = connect_to_db()
    if not conn:
        logger.error("Невозможно подключиться к базе данных. Выход.")
        return
        
    try:
        # Добавляем тестовые модели
        add_test_lora_models(conn)
        logger.info("Операция успешно завершена.")
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
    finally:
        conn.close()
        logger.info("Соединение с базой данных закрыто.")

if __name__ == "__main__":
    main() 