from fastapi import FastAPI, HTTPException
from app.config import config
from app.repository.db import BaseRepository
from app.api.routes import register_all_routes
from app.utils.logger import logger


def setup_lifecycle(app: FastAPI):
    @app.on_event("startup")
    async def startup_event():
        logger.info("🚀 Запуск FastAPI приложения...")

        if config.DISABLE_DB_CHECK:
            logger.warning("⚠️ Проверка подключения к базе данных отключена")
        else:
            try:
                BaseRepository.initialize_pool(
                    database=config.DB_CONFIG["database"],
                    user=config.DB_CONFIG["user"],
                    password=config.DB_CONFIG["password"],
                    host=config.DB_CONFIG["host"],
                    port=config.DB_CONFIG["port"],
                    min_connections=config.DB_CONFIG.get("min_connections", 1),
                    max_connections=config.DB_CONFIG.get("max_connections", 10),
                )
                logger.info("✅ Подключение к базе данных успешно установлено")
            except Exception as e:
                logger.error(f"❌ Ошибка подключения к базе данных: {e}")
                raise HTTPException(status_code=500, detail="Database connection failed")

        register_all_routes(app)
        logger.info("✅ Роуты API успешно зарегистрированы")

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("🛑 Остановка FastAPI приложения...")

        if config.DISABLE_DB_CHECK:
            logger.warning("⚠️ Завершение без проверки базы данных")
        else:
            try:
                if BaseRepository._connection_pool:
                    BaseRepository._connection_pool.closeall()
                    logger.info("✅ Все соединения с базой данных закрыты")
            except Exception as e:
                logger.error(f"❌ Ошибка при закрытии соединений с БД: {e}")
