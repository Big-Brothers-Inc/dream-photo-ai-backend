from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
dotenv_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=dotenv_path)

class Settings(BaseSettings):
    # Настройки базы данных
    DB_CONFIG: dict = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'dream_photo'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD', ''),
        'min_size': int(os.getenv('DB_MIN_CONN', 1)),
        'max_size': int(os.getenv('DB_MAX_CONN', 10)),
    }
    DATABASE_URL: str = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    
    # Настройки Redis
    REDIS_CONFIG: dict = {
        'host': os.getenv('REDIS_HOST', 'localhost'),
        'port': int(os.getenv('REDIS_PORT', 6379)),
        'password': os.getenv('REDIS_PASSWORD', ''),
        'db': int(os.getenv('REDIS_DB', 0)),
    }
    
    # Настройки API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = int(os.getenv('API_PORT', 8000))
    
    # Настройки Telegram бота
    BOT_TOKEN: Optional[str] = os.getenv('BOT_TOKEN')
    BOT_USERNAME: Optional[str] = os.getenv('BOT_USERNAME')
    TELEGRAM_WEBHOOK_URL: Optional[str] = os.getenv('TELEGRAM_WEBHOOK_URL')
    
    # Настройки URL и веб-приложения
    NGROK_URL: str = os.getenv('NGROK_URL', 'https://daad-95-163-176-193.ngrok-free.app')
    WEBAPP_URL: str = os.getenv('WEBAPP_URL', NGROK_URL)
    API_URL: str = f"{NGROK_URL}/api"
    
    # Настройки безопасности
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Настройки для работы с изображениями
    BASE_UPLOAD_DIR: str = os.getenv('BASE_UPLOAD_DIR', 'user_training_photos')
    MAX_IMAGE_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_IMAGE_TYPES: set = {"image/jpeg", "image/png"}
    
    # Настройки для API интеграций
    REPLICATE_API_TOKEN: Optional[str] = os.getenv('REPLICATE_API_TOKEN')
    FALAI_API_KEY: Optional[str] = os.getenv('FALAI_API_KEY')
    NGROK_AUTH_TOKEN: Optional[str] = os.getenv('NGROK_AUTH_TOKEN')
    
    # Цены
    MODEL_TRAINING_PRICE: int = int(os.getenv('MODEL_TRAINING_PRICE', 50000))
    GENERATION_PRICE: int = int(os.getenv('GENERATION_PRICE', 5000))
    
    # Настройки CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        NGROK_URL,
        "https://t.me",
        "https://telegram.org",
        WEBAPP_URL
    ]
    
    # Другие настройки
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
    ADMIN_USER_IDS: List[int] = [int(x) for x in os.getenv('ADMIN_USER_IDS', '').split(',') if x]
    SERVER_IP: str = os.getenv('SERVER_IP', '127.0.0.1')
    DISABLE_DB_CHECK: bool = os.getenv('DISABLE_DB_CHECK', 'False').lower() in ('true', '1', 't')
    
    # Настройки облачного хранилища
    CLOUD_STORAGE_API_KEY: Optional[str] = os.getenv('CLOUD_STORAGE_API_KEY')
    CLOUD_STORAGE_URL: Optional[str] = os.getenv('CLOUD_STORAGE_URL')
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Создаем экземпляр настроек
settings = Settings() 