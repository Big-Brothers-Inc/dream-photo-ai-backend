import os
import sys
import logging
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Добавляем корневую директорию проекта в путь поиска модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Загружаем переменные окружения
load_dotenv(override=True)

# Проверяем, нужно ли отключить проверку подключения к базе данных
DISABLE_DB_CHECK = os.getenv("DISABLE_DB_CHECK", "false").lower() == "true"
print(f"[api.py] DISABLE_DB_CHECK из окружения: {os.getenv('DISABLE_DB_CHECK')}")
print(f"[api.py] DISABLE_DB_CHECK после обработки: {DISABLE_DB_CHECK}")

# Импортируем репозитории для работы с базой данных
from repository import init_db, close_db

# Импортируем API-эндпоинты для обучения моделей
from handlers.training_api import setup_training_api

# Импортируем настройки CORS и сервера
from config import CORS_ORIGINS, API_HOST, API_PORT, NGROK_URL

# Устанавливаем уровень логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("api.log"),
        logging.StreamHandler()
    ]
)

# Получаем логгер для этого модуля
logger = logging.getLogger(__name__)

# Создаем экземпляр FastAPI приложения
app = FastAPI(
    title="Dream Photo API",
    description="API для работы с Dream Photo AI",
    version="1.0.0"
)

# Добавляем middleware для CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все источники для тестирования с ngrok
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


# Middleware для логирования запросов и обработки заголовков
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Логируем заголовки запроса для отладки
    logger.info(f"Request headers: {request.headers}")

    # Продолжаем обработку запроса
    response = await call_next(request)
    return response


# Регистрируем API-эндпоинты для обучения моделей
setup_training_api(app)


# События при запуске и остановке приложения
@app.on_event("startup")
async def startup_event():
    """
    Действия при запуске приложения
    """
    logger.info("Инициализация базы данных...")
    if DISABLE_DB_CHECK:
        logger.warning("Проверка подключения к базе данных отключена")
    else:
        if init_db():
            logger.info("База данных успешно инициализирована")
        else:
            logger.error("Ошибка при инициализации базы данных")
            raise HTTPException(status_code=500, detail="Database initialization failed")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Действия при остановке приложения
    """
    if not DISABLE_DB_CHECK:
        logger.info("Закрытие соединений с базой данных...")
        if close_db():
            logger.info("Соединения с базой данных закрыты")
        else:
            logger.error("Ошибка при закрытии соединений с базой данных")


# Корневой эндпоинт для проверки работоспособности API
@app.get("/")
async def root():
    """
    Корневой эндпоинт для проверки работоспособности API
    """
    return {"status": "success", "message": "Dream Photo API is running"}


# Эндпоинт для проверки подключения к базе данных
@app.get("/health")
async def health_check():
    """
    Эндпоинт для проверки подключения к базе данных
    """
    try:
        if DISABLE_DB_CHECK:
            return {"status": "success", "database": "check_disabled"}
        else:
            # Проверяем подключение к базе данных
            if init_db():
                return {"status": "success", "database": "connected"}
            else:
                return {"status": "error", "database": "disconnected"}
    except Exception as e:
        logger.error(f"Ошибка при проверке здоровья приложения: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Запуск приложения
if __name__ == "__main__":
    # Запускаем сервер
    uvicorn.run(
        "api:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,  # В продакшене нужно установить False
        log_level="info"
    )
