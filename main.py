import asyncio

from utils.logger import logger
from loader import bot, dp
from db import init_connection, close_connection
from handlers import register_all_handlers


async def on_startup() -> None:
    logger.info("Инициализация подключения к базе данных...")
    #init_connection()

    logger.info("Регистрация всех обработчиков...")
    register_all_handlers(dp)

    logger.info("Бот готов к запуску.")


async def on_shutdown() -> None:
    logger.info("Остановка бота...")
    close_connection()
    logger.info("Подключение к базе данных закрыто.")


async def main() -> None:
    logger.info("Запуск бота...")

    await on_startup()

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception(f"Ошибка при запуске бота: {e}")
    finally:
        await on_shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен вручную (Ctrl+C)")
