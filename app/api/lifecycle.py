from fastapi import FastAPI, HTTPException
from app.config import config
from app.db.db import init_connection, close_connection
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
                init_connection()
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
                close_connection()
                logger.info("✅ Соединение с базой данных закрыто")
            except Exception as e:
                logger.error(f"❌ Ошибка при закрытии соединения с БД: {e}")
