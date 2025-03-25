import asyncio
from app.utils.logger import logger
from loader import bot, dp
from app.repository.db import BaseRepository
from app.config import config
from handlers import register_all_handlers
from app.utils.set_bot_commands import set_default_commands


async def on_startup() -> None:
    logger.info("🚀 Инициализация подключения к базе данных...")

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
            raise

    logger.info("📦 Регистрация всех обработчиков...")
    register_all_handlers(dp)

    logger.info("⚙️ Установка команд бота...")
    await set_default_commands(bot)

    logger.info("🤖 Бот готов к запуску.")


async def on_shutdown() -> None:
    logger.info("🛑 Остановка бота...")

    if config.DISABLE_DB_CHECK:
        logger.warning("⚠️ Завершение без проверки базы данных")
    else:
        try:
            if BaseRepository._connection_pool:
                BaseRepository._connection_pool.closeall()
                logger.info("✅ Все соединения с базой данных закрыты")
        except Exception as e:
            logger.error(f"❌ Ошибка при закрытии соединений с БД: {e}")


async def main() -> None:
    logger.info("🚦 Запуск бота...")

    await on_startup()

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception(f"❌ Ошибка при запуске бота: {e}")
    finally:
        await on_shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⛔ Бот остановлен вручную (Ctrl+C)")
