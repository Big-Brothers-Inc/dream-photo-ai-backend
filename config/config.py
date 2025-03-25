from pydantic_settings import BaseSettings
from typing import List, Optional, Set
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseSettings):
    # ==== Telegram Bot ====
    BOT_TOKEN: str
    BOT_USERNAME: Optional[str]
    TELEGRAM_WEBHOOK_URL: Optional[str] = None

    # ==== Database ====
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "dream_photo"
    DB_USER: str
    DB_PASSWORD: str = ""
    DB_MIN_CONN: int = 1
    DB_MAX_CONN: int = 10

    @property
    def DB_CONFIG(self) -> dict:
        return {
            'host': self.DB_HOST,
            'port': self.DB_PORT,
            'database': self.DB_NAME,
            'user': self.DB_USER,
            'password': self.DB_PASSWORD,
            'min_size': self.DB_MIN_CONN,
            'max_size': self.DB_MAX_CONN,
        }

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # ==== Redis ====
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = ""
    REDIS_DB: int = 0

    @property
    def REDIS_CONFIG(self) -> dict:
        return {
            'host': self.REDIS_HOST,
            'port': self.REDIS_PORT,
            'password': self.REDIS_PASSWORD,
            'db': self.REDIS_DB,
        }

    # ==== URLs ====
    NGROK_URL: str = "https://localhost:3000"
    WEBAPP_URL: str = os.getenv("WEBAPP_URL", NGROK_URL)
    API_URL: str = f"{NGROK_URL}/api"

    # ==== API Server ====
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # ==== Security ====
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ==== Uploading ====
    BASE_UPLOAD_DIR: str = "user_training_photos"
    MAX_IMAGE_SIZE: int = 5 * 1024 * 1024  # 5 MB
    ALLOWED_IMAGE_TYPES: Set[str] = {"image/jpeg", "image/png"}

    # ==== Third-party APIs ====
    REPLICATE_API_TOKEN: Optional[str]
    FALAI_API_KEY: Optional[str]
    NGROK_AUTH_TOKEN: Optional[str]
    CLOUD_STORAGE_API_KEY: Optional[str]
    CLOUD_STORAGE_URL: Optional[str]

    # ==== Prices ====
    MODEL_TRAINING_PRICE: int = 50000
    GENERATION_PRICE: int = 5000

    # ==== Misc ====
    DEBUG: bool = False
    ADMIN_USER_IDS: List[int] = []
    SERVER_IP: str = "127.0.0.1"
    DISABLE_DB_CHECK: bool = False

    # ==== CORS ====
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        WEBAPP_URL,
        "https://t.me",
        "https://telegram.org",
    ]

    # ==== FastAPI ====
    API_TITLE: str = "Dream Photo AI API"
    API_DESCRIPTION: str = "REST API для генерации изображений и управления пользователями"
    API_VERSION: str = "1.0.0"
    API_CONTACT_NAME: Optional[str] = "Support Team"
    API_CONTACT_EMAIL: Optional[str] = "support@example.com"
    API_CONTACT_URL: Optional[str] = "https://dreamphoto.ai"

    DOCS_URL: str = "/docs"        # Swagger UI
    REDOC_URL: str = "/redoc"      # ReDoc UI
    OPENAPI_URL: str = "/openapi.json"

    @property
    def SWAGGER_URL(self) -> str:
        return f"http://{self.API_HOST}:{self.API_PORT}{self.DOCS_URL}"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Создание глобального экземпляра конфигурации
config = Settings()
