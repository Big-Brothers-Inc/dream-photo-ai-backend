# utils/logger.py

import logging
import sys
import os

# Получаем уровень логирования из переменных окружения или по умолчанию INFO
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Основная настройка логирования
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Экспортируем логгер, которым можно пользоваться в любом модуле
logger = logging.getLogger("bot")
