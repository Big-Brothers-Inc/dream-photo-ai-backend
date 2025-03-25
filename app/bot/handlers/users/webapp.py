from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
import os
import logging

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("webapp"))
async def command_webapp(message: types.Message):
    webapp_url = os.getenv("WEBAPP_URL", "https://localhost:3000")
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🖼 Обучить модель", web_app=WebAppInfo(url=f"{webapp_url}/train")),
             KeyboardButton(text="👤 Личный кабинет", web_app=WebAppInfo(url=f"{webapp_url}/cabinet"))],
            [KeyboardButton(text="⚙️ Выбор настроек", web_app=WebAppInfo(url=f"{webapp_url}/extra"))]
        ],
        resize_keyboard=True,
        is_persistent=True
    )
    await message.answer("Выберите действие:", reply_markup=keyboard)
