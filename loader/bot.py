from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
import logging
import sys
import os

# Добавляем родительскую директорию в sys.path для импорта из других модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import BOT_TOKEN

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

# Функция для запуска бота
async def start_bot():
    from handlers import register_all_handlers
    
    # Регистрация всех обработчиков
    register_all_handlers(dp)
    
    # Запуск поллинга
    await dp.start_polling()

if __name__ == "__main__":
    from aiogram import executor
    from handlers import register_all_handlers
    
    # Регистрация всех обработчиков
    register_all_handlers(dp)
    
    # Запуск бота
    executor.start_polling(dp, skip_updates=True) 