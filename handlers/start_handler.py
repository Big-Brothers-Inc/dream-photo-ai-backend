from aiogram import Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging
import sys
import os

# Добавляем родительскую директорию в sys.path для импорта из других модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loader.bot import bot
from repository.user_repo import create_user, get_user
from utils.notifications import send_admin_notification
from utils.states import UserState
from utils.keyboard import get_start_keyboard


async def cmd_start(message: types.Message):
    """
    Обработчик команды /start
    Отправляет приветственное сообщение и создает пользователя в БД (если не существует)
    """
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Проверяем, существует ли пользователь в БД
    user = get_user(user_id)
    
    if not user:
        # Создаем нового пользователя
        create_user(user_id, username)
        
        # Уведомляем админа о новом пользователе
        await send_admin_notification(f"Новый пользователь: {username} (ID: {user_id})")
    
    # Отправляем приветственное сообщение
    welcome_text = (
        "👋 Добро пожаловать в Dream Photo AI!\n\n"
        "Этот бот поможет вам создавать потрясающие фотографии с вашим лицом "
        "с помощью технологии искусственного интеллекта LoRA.\n\n"
        "📸 Загрузите 10-15 фотографий вашего лица\n"
        "🔄 Бот обучит персональную модель\n"
        "✨ Генерируйте уникальные изображения\n\n"
        "Нажмите кнопку ниже, чтобы начать!"
    )
    
    # Создаем клавиатуру с кнопкой оплаты
    keyboard = get_start_keyboard()
    
    await message.answer(welcome_text, reply_markup=keyboard)


def register_start_handlers(dp: Dispatcher):
    """Регистрация обработчиков команды /start"""
    dp.register_message_handler(cmd_start, commands=["start"]) 