import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Telegram Bot токен
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Replicate API токен
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

# FalAI API токен (альтернатива Replicate)
FALAI_API_KEY = os.getenv("FALAI_API_KEY")

# Настройки базы данных
POSTGRES_DB = os.getenv("POSTGRES_DB", "dream_photo_ai")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

# Формируем строку подключения к базе данных
DB_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# URL для подключения к Redis (опционально)
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_DB = os.getenv("REDIS_DB", "0")

if REDIS_PASSWORD:
    REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
else:
    REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# URL фронтенда (Telegram Web App)
WEBAPP_URL = os.getenv("WEBAPP_URL")

# Настройки для обучения модели
TRAINING_VERSION = "ostris/flux-dev-lora-trainer:b6af14222e6bd9be257cbc1ea4afda3cd0503e1133083b9d1de0364d8568e6ef"
GENERATION_VERSION = "ostris/flux-dev-lora-trainer:b6af14222e6bd9be257cbc1ea4afda3cd0503e1133083b9d1de0364d8568e6ef"

# Настройки для загрузки фотографий
PHOTO_STORAGE_PATH = "temp_photos"
MIN_PHOTOS_REQUIRED = 10
MAX_PHOTOS_ALLOWED = 15

# Цены
MODEL_TRAINING_PRICE = int(os.getenv("MODEL_TRAINING_PRICE", "50000"))
GENERATION_PRICE = int(os.getenv("GENERATION_PRICE", "5000"))

# Другие настройки
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
SERVER_IP = os.getenv("SERVER_IP")

# Администраторы
ADMIN_USER_IDS = []
admin_ids = os.getenv("ADMIN_USER_IDS", "")
if admin_ids:
    ADMIN_USER_IDS = [int(admin_id) for admin_id in admin_ids.split(",") if admin_id.strip()] 