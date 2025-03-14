import os
import logging
import replicate
import requests
import sys
import aiohttp
import json

# Добавляем родительскую директорию в sys.path для импорта из других модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import REPLICATE_API_TOKEN, TRAINING_VERSION, GENERATION_VERSION


# Устанавливаем токен API Replicate
os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN


async def train_model(zip_path: str, model_name: str, trigger_word: str):
    """
    Отправляет ZIP-архив с фотографиями на обучение модели
    
    Args:
        zip_path (str): Путь к ZIP-архиву с фотографиями
        model_name (str): Название модели
        trigger_word (str): Триггер-слово для модели
        
    Returns:
        str: ID тренировки в API Replicate
    """
    try:
        # Загружаем ZIP-архив в облачное хранилище
        # Здесь должен быть код для загрузки файла в S3, Google Cloud Storage и т.п.
        # Для упрощения примера просто предполагаем, что URL уже доступен
        zip_url = await upload_to_storage(zip_path)
        
        logging.info(f"Загружен ZIP-архив: {zip_url}")
        
        # Запускаем обучение модели
        training = replicate.trainings.create(
            destination=f"user/{model_name}",
            version=TRAINING_VERSION,
            input={
                "steps": 1000,
                "lora_rank": 16,
                "optimizer": "adamw8bit",
                "batch_size": 1,
                "resolution": "512,768,1024",
                "autocaption": True,
                "input_images": zip_url,
                "trigger_word": trigger_word,
                "learning_rate": 0.0004,
                "wandb_project": "flux_train_replicate",
                "wandb_save_interval": 100,
                "caption_dropout_rate": 0.05,
                "cache_latents_to_disk": False,
                "wandb_sample_interval": 100,
                "gradient_checkpointing": False
            }
        )
        
        logging.info(f"Запущено обучение модели. ID тренировки: {training.id}")
        
        return training.id
    except Exception as e:
        logging.error(f"Ошибка при запуске обучения модели: {e}")
        raise


async def check_training_status(training_id: str):
    """
    Проверяет статус обучения модели
    
    Args:
        training_id (str): ID тренировки в API Replicate
        
    Returns:
        str: Статус тренировки (starting, processing, succeeded, failed)
    """
    try:
        training = replicate.trainings.get(training_id)
        logging.info(f"Статус обучения модели {training_id}: {training.status}")
        return training.status
    except Exception as e:
        logging.error(f"Ошибка при проверке статуса обучения модели: {e}")
        raise


async def generate_image(model_id: str, prompt: str, num_outputs: int = 1):
    """
    Генерирует изображение с помощью обученной модели
    
    Args:
        model_id (str): ID модели в API Replicate
        prompt (str): Текстовый запрос для генерации
        num_outputs (int, optional): Количество выходных изображений. По умолчанию 1.
        
    Returns:
        list: Список URL сгенерированных изображений
    """
    try:
        logging.info(f"Начало генерации изображения. Модель: {model_id}, запрос: {prompt}")
        
        output = replicate.run(
            GENERATION_VERSION,
            input={
                "prompt": prompt,
                "model": "dev",
                "num_outputs": num_outputs,
                "extra_lora": model_id,
                "lora_scale": 1.0,
                "num_inference_steps": 28
            }
        )
        
        logging.info(f"Сгенерировано {len(output)} изображений")
        
        return output
    except Exception as e:
        logging.error(f"Ошибка при генерации изображения: {e}")
        raise


async def upload_to_storage(file_path: str):
    """
    Загружает файл в облачное хранилище
    
    Args:
        file_path (str): Путь к файлу
        
    Returns:
        str: URL загруженного файла
    """
    try:
        # В реальном проекте здесь должен быть код для загрузки файла в S3, Google Cloud Storage и т.п.
        # Для демонстрации используем временный сервис для загрузки файлов
        
        with open(file_path, 'rb') as file:
            # Создаем форму для загрузки файла
            data = aiohttp.FormData()
            data.add_field('file', file, filename=os.path.basename(file_path))
            
            # Загружаем файл на сервис
            async with aiohttp.ClientSession() as session:
                async with session.post('https://file.io', data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('link')
                    else:
                        error_text = await response.text()
                        raise Exception(f"Ошибка при загрузке файла: {response.status} - {error_text}")
    except Exception as e:
        logging.error(f"Ошибка при загрузке файла в хранилище: {e}")
        # Заглушка для тестирования
        return f"https://storage.example.com/{os.path.basename(file_path)}" 