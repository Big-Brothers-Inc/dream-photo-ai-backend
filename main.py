# main.py

import asyncio
import os
import sys

# Добавляем корневую директорию проекта в путь поиска модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import logger
from loader import bot, dp
from repository import init_db, close_db

from handlers.admin_db_commands import setup_admin_handlers
from handlers.commands import router as commands_router
from handlers.training_handlers import setup_training_handlers
# импорт других обработчиков...

import handlers.admin_notifications  # чтобы точно подгрузился

# Регистрируем обработчики
setup_admin_handlers(dp)
dp.include_router(commands_router)
setup_training_handlers(dp)
# другие обработчики...


async def on_startup():
    logger.info("Инициализация базы данных...")
    if init_db():
        logger.info("База данных успешно инициализирована")
    else:
        logger.error("Ошибка при инициализации базы данных")


async def on_shutdown():
    logger.info("Закрытие соединений с базой данных...")
    if close_db():
        logger.info("Соединения с базой данных закрыты")
    else:
        logger.error("Ошибка при закрытии соединений с базой данных")


async def main():
    logger.info("Запуск бота...")

    await on_startup()

    try:
        logger.info("Бот запущен!")
        await dp.start_polling(bot)
    finally:
        await on_shutdown()
        logger.info("Бот остановлен!")


if __name__ == "__main__":
    asyncio.run(main())
