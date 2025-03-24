import asyncio
import logging
import os
import sys
from datetime import datetime

# Добавляем корневую директорию проекта в путь поиска модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

from dotenv import load_dotenv
load_dotenv()

# Импортируем модуль для работы с базой данных
from repository import init_db, close_db

# Импортируем обработчики
from handlers.admin_db_commands import setup_admin_handlers
from handlers.commands import router as commands_router
from handlers.training_handlers import setup_training_handlers
# импорт других обработчиков...

# Убедимся, что модуль admin_notifications импортируется
import handlers.admin_notifications

# Устанавливаем уровень логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Получаем логгер для этого модуля
logger = logging.getLogger(__name__)

# Токен для бота
TOKEN = os.getenv("BOT_TOKEN")

# Создаем экземпляр бота
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)

# Создаем диспетчер для бота
dp = Dispatcher()

# Регистрируем обработчики
setup_admin_handlers(dp)
dp.include_router(commands_router)
setup_training_handlers(dp)
# Регистрация других обработчиков...

async def on_startup():
    """
    Действия при запуске бота
    """
    logger.info("Инициализация базы данных...")
    if init_db():
        logger.info("База данных успешно инициализирована")
    else:
        logger.error("Ошибка при инициализации базы данных")

async def on_shutdown():
    """
    Действия при остановке бота
    """
    logger.info("Закрытие соединений с базой данных...")
    if close_db():
        logger.info("Соединения с базой данных закрыты")
    else:
        logger.error("Ошибка при закрытии соединений с базой данных")

async def main():
    """
    Основная функция запуска бота
    """
    logger.info("Запуск бота...")
    
    # Действия при запуске
    await on_startup()
    
    # Запуск поллинга бота
    try:
        logger.info("Бот запущен!")
        await dp.start_polling(bot)
    finally:
        # Действия при остановке
        await on_shutdown()
        logger.info("Бот остановлен!")

if __name__ == "__main__":
    # Запуск бота
    asyncio.run(main()) 