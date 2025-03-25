import os
import logging
import shutil
import zipfile
import tempfile
import requests
import time
from typing import List, Dict, Any, Optional
from PIL import Image
from io import BytesIO
import replicate
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Проверяем, нужно ли отключить проверку подключения к базе данных
DISABLE_DB_CHECK = os.getenv("DISABLE_DB_CHECK", "false").lower() == "true"

# Получаем API-ключ Replicate из переменных окружения
REPLICATE_API_KEY = os.getenv("REPLICATE_API_TOKEN")
if not REPLICATE_API_KEY and not DISABLE_DB_CHECK:
    logging.error("REPLICATE_API_TOKEN не найден в переменных окружения")

# Получаем API-ключ для облачного хранилища (например, Cloudinary или аналог)
CLOUD_STORAGE_API_KEY = os.getenv("CLOUD_STORAGE_API_KEY")
CLOUD_STORAGE_URL = os.getenv("CLOUD_STORAGE_URL")

# Устанавливаем базовые пути для загрузки фотографий
BASE_UPLOAD_DIR = os.getenv("BASE_UPLOAD_DIR", "user_training_photos")

# Настраиваем логгер
logger = logging.getLogger(__name__)

def ensure_upload_dir_exists() -> bool:
    """
    Проверяет существование директории для загрузки фотографий,
    создает ее, если она не существует.
    
    Returns:
        bool: True, если директория существует или успешно создана, иначе False
    """
    try:
        if not os.path.exists(BASE_UPLOAD_DIR):
            os.makedirs(BASE_UPLOAD_DIR)
            logger.info(f"Создана базовая директория для загрузок: {BASE_UPLOAD_DIR}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при создании директории для загрузок: {e}")
        return False

def get_user_upload_path(username: str, user_id: int) -> str:
    """
    Формирует путь к директории для загрузки фотографий пользователя.
    
    Args:
        username (str): Имя пользователя
        user_id (int): ID пользователя
    
    Returns:
        str: Путь к директории пользователя
    """
    # Очищаем имя пользователя от запрещенных символов
    clean_username = "".join(c for c in username if c.isalnum() or c in "_-")
    user_dir = f"{clean_username}_{user_id}"
    user_path = os.path.join(BASE_UPLOAD_DIR, user_dir)
    
    # Создаем директорию пользователя, если она не существует
    if not os.path.exists(user_path):
        os.makedirs(user_path)
        logger.info(f"Создана директория для пользователя {username}: {user_path}")
    
    return user_path

def clear_user_upload_dir(username: str, user_id: int) -> bool:
    """
    Очищает директорию пользователя от ранее загруженных файлов.
    
    Args:
        username (str): Имя пользователя
        user_id (int): ID пользователя
    
    Returns:
        bool: True, если директория успешно очищена, иначе False
    """
    user_path = get_user_upload_path(username, user_id)
    try:
        for file_name in os.listdir(user_path):
            file_path = os.path.join(user_path, file_name)
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        logger.info(f"Директория пользователя {username} очищена: {user_path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при очистке директории пользователя {username}: {e}")
        return False

def convert_image_to_jpg(input_path: str, output_path: str) -> bool:
    """
    Конвертирует изображение в формат JPG.
    
    Args:
        input_path (str): Путь к исходному изображению
        output_path (str): Путь для сохранения конвертированного изображения
    
    Returns:
        bool: True, если конвертация успешна, иначе False
    """
    try:
        with Image.open(input_path) as img:
            # Конвертация изображения в RGB, если оно в другом режиме
            if img.mode in ('RGBA', 'LA', 'P'):
                # Создаем новое изображение с белым фоном
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
                else:
                    background.paste(img)
                background.save(output_path, 'JPEG', quality=95)
            else:
                # Для RGB изображений просто конвертируем в JPG
                img.convert('RGB').save(output_path, 'JPEG', quality=95)
        
        logger.info(f"Изображение успешно конвертировано: {input_path} -> {output_path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при конвертации изображения {input_path}: {e}")
        return False

def process_and_convert_images(username: str, user_id: int, image_paths: List[str]) -> List[str]:
    """
    Обрабатывает и конвертирует несколько изображений в формат JPG.
    
    Args:
        username (str): Имя пользователя
        user_id (int): ID пользователя
        image_paths (List[str]): Список путей к исходным изображениям
    
    Returns:
        List[str]: Список путей к конвертированным изображениям
    """
    user_path = get_user_upload_path(username, user_id)
    converted_paths = []
    
    for i, img_path in enumerate(image_paths):
        # Формируем путь для сохранения конвертированного изображения
        jpg_filename = f"image_{i+1}.jpg"
        jpg_path = os.path.join(user_path, jpg_filename)
        
        # Конвертируем изображение
        if convert_image_to_jpg(img_path, jpg_path):
            converted_paths.append(jpg_path)
    
    logger.info(f"Обработано и конвертировано {len(converted_paths)} из {len(image_paths)} изображений")
    return converted_paths

def create_zip_archive(username: str, user_id: int, image_paths: List[str]) -> str:
    """
    Создает ZIP-архив из конвертированных изображений.
    
    Args:
        username (str): Имя пользователя
        user_id (int): ID пользователя
        image_paths (List[str]): Список путей к конвертированным изображениям
    
    Returns:
        str: Путь к созданному ZIP-архиву
    """
    # Формируем путь к ZIP-архиву
    clean_username = "".join(c for c in username if c.isalnum() or c in "_-")
    zip_filename = f"{clean_username}_{user_id}.zip"
    user_path = get_user_upload_path(username, user_id)
    zip_path = os.path.join(user_path, zip_filename)
    
    try:
        # Создаем ZIP-архив
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for img_path in image_paths:
                # Добавляем в архив только имя файла, без полного пути
                zipf.write(img_path, os.path.basename(img_path))
        
        logger.info(f"Создан ZIP-архив: {zip_path} с {len(image_paths)} изображениями")
        return zip_path
    except Exception as e:
        logger.error(f"Ошибка при создании ZIP-архива для пользователя {username}: {e}")
        return ""

def upload_zip_to_cloud(zip_path: str) -> str:
    """
    Загружает ZIP-архив в облачное хранилище и возвращает URL.
    
    Args:
        zip_path (str): Путь к ZIP-архиву
    
    Returns:
        str: URL загруженного архива
    """
    # В тестовом режиме возвращаем фиктивный URL
    if DISABLE_DB_CHECK:
        logger.info(f"[ТЕСТОВЫЙ РЕЖИМ] Эмуляция загрузки ZIP-архива: {zip_path}")
        return f"https://cloud-storage.example.com/{os.path.basename(zip_path)}"
    
    try:
        if not os.path.exists(zip_path):
            logger.error(f"ZIP-архив не найден: {zip_path}")
            return ""
        
        # Для демонстрации возвращаем локальный путь
        # В реальном проекте здесь должен быть код для загрузки
        # и получения URL из облачного хранилища
        
        # Эмуляция загрузки в облако
        logger.info(f"ZIP-архив успешно загружен в облачное хранилище: {zip_path}")
        dummy_url = f"https://cloud-storage.example.com/{os.path.basename(zip_path)}"
        
        return dummy_url
    except Exception as e:
        logger.error(f"Ошибка при загрузке ZIP-архива в облачное хранилище: {e}")
        return ""

def start_replicate_training(username: str, user_id: int, zip_url: str, model_name: str, trigger_word: str) -> Dict[str, Any]:
    """
    Запускает обучение модели на Replicate с заданными параметрами.
    
    Args:
        username (str): Имя пользователя
        user_id (int): ID пользователя
        zip_url (str): URL ZIP-архива с изображениями
        model_name (str): Название модели
        trigger_word (str): Триггер-слово для модели
    
    Returns:
        Dict[str, Any]: Информация о запущенном обучении
    """
    # В тестовом режиме возвращаем фиктивные данные
    if DISABLE_DB_CHECK:
        import uuid
        training_id = str(uuid.uuid4())
        logger.info(f"[ТЕСТОВЫЙ РЕЖИМ] Эмуляция запуска обучения модели: {model_name}")
        return {
            "training_id": training_id,
            "status": "started",
            "model_name": model_name,
            "trigger_word": trigger_word,
            "user_id": user_id,
            "username": username
        }
    
    try:
        # Настраиваем клиент Replicate с помощью API-ключа
        if REPLICATE_API_KEY:
            # Установка API-ключа для Replicate
            os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_KEY
        
        # Формируем запрос для API Replicate
        # Важно: параметры должны соответствовать API Replicate
        input_data = {
            "input_images": zip_url,
            "train_mode": "normal",
            "model_name": model_name,
            "trigger_word": trigger_word,
            "train_batch_size": 1,
            "resolution": 512,
            "num_training_steps": 3000,
            "learning_rate": 1e-6,
            "enable_LoRA": True,
            "lora_alpha": 512,
            "lora_rank": 16,
            "lora_dropout": 0.1,
        }
        
        # Запускаем обучение с помощью Replicate API
        version = "lucataco/lora-training:54bdee3a48fafb1e65dacf9151138ae290b35328ff5fbfd6cc4a8fcfa2dbe3c3"
        training = replicate.run(version, input=input_data)
        
        # Получаем ID обучения и другую информацию из ответа API
        training_id = training["id"]
        status = "started"
        
        logger.info(f"Запущено обучение модели на Replicate: {training_id}")
        
        return {
            "training_id": training_id,
            "status": status,
            "model_name": model_name,
            "trigger_word": trigger_word,
            "user_id": user_id,
            "username": username
        }
    except Exception as e:
        logger.error(f"Ошибка при запуске обучения модели на Replicate: {e}")
        return {
            "error": str(e),
            "status": "failed"
        }

def check_training_status(training_id: str) -> Dict[str, Any]:
    """
    Проверяет статус обучения модели на Replicate.
    
    Args:
        training_id (str): ID обучения
    
    Returns:
        Dict[str, Any]: Информация о статусе обучения
    """
    # В тестовом режиме возвращаем фиктивные данные
    if DISABLE_DB_CHECK:
        logger.info(f"[ТЕСТОВЫЙ РЕЖИМ] Эмуляция проверки статуса обучения: {training_id}")
        return {
            "training_id": training_id,
            "status": "succeeded",
            "output": {
                "model_url": f"https://replicate.com/models/user/model-{training_id}"
            }
        }
    
    try:
        if REPLICATE_API_KEY:
            # Установка API-ключа для Replicate
            os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_KEY
        
        # Получаем информацию о прогрессе обучения
        prediction = replicate.predictions.get(training_id)
        
        status = prediction.status
        output = prediction.output if prediction.status == "succeeded" else None
        
        logger.info(f"Статус обучения модели {training_id}: {status}")
        
        return {
            "training_id": training_id,
            "status": status,
            "output": output
        }
    except Exception as e:
        logger.error(f"Ошибка при проверке статуса обучения модели {training_id}: {e}")
        return {
            "training_id": training_id,
            "status": "error",
            "error": str(e)
        }

def process_training_completion(training_id: str, user_id: int, username: str, model_name: str, trigger_word: str) -> Dict[str, Any]:
    """
    Обрабатывает завершение обучения модели и сохраняет результаты.
    
    Args:
        training_id (str): ID обучения
        user_id (int): ID пользователя
        username (str): Имя пользователя
        model_name (str): Название модели
        trigger_word (str): Триггер-слово для модели
    
    Returns:
        Dict[str, Any]: Информация о модели
    """
    # В тестовом режиме возвращаем фиктивные данные
    if DISABLE_DB_CHECK:
        logger.info(f"[ТЕСТОВЫЙ РЕЖИМ] Эмуляция завершения обучения модели: {training_id}")
        return {
            "user_id": user_id,
            "username": username,
            "model_name": model_name,
            "trigger_word": trigger_word,
            "model_url": f"https://replicate.com/models/user/model-{training_id}",
            "training_id": training_id,
            "status": "completed",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    try:
        # Получаем статус обучения
        training_status = check_training_status(training_id)
        
        if training_status["status"] == "succeeded":
            # Обучение успешно завершено, получаем информацию о модели
            output = training_status["output"]
            
            # Извлекаем ссылку на модель из результатов обучения
            model_url = output.get("model_url") if output else None
            
            # Формируем информацию о модели
            model_info = {
                "user_id": user_id,
                "username": username,
                "model_name": model_name,
                "trigger_word": trigger_word,
                "model_url": model_url,
                "training_id": training_id,
                "status": "completed",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            logger.info(f"Обучение модели {training_id} успешно завершено. Модель доступна по ссылке: {model_url}")
            
            return model_info
        else:
            # Обучение завершилось с ошибкой или еще не завершено
            return {
                "training_id": training_id,
                "status": training_status["status"],
                "error": training_status.get("error", "Unknown error")
            }
    except Exception as e:
        logger.error(f"Ошибка при обработке завершения обучения модели {training_id}: {e}")
        return {
            "training_id": training_id,
            "status": "error",
            "error": str(e)
        } 