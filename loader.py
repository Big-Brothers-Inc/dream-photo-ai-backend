# loader.py

from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv
import os
from aiogram.fsm.storage.memory import MemoryStorage  # <-- если ты на aiogram 3

load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"), parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()

dp = Dispatcher(bot=bot, storage=storage)
