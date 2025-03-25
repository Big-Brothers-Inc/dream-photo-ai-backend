# loader.py

from aiogram import Bot, Dispatcher, enums
from aiogram.fsm.storage.memory import MemoryStorage
from config import config

# Используем данные из конфигурации
bot = Bot(token=config.BOT_TOKEN, parse_mode=enums.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)
