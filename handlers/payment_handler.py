from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
import logging
import sys
import os

# Добавляем родительскую директорию в sys.path для импорта из других модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loader.bot import bot
from repository.user_repo import update_user_tokens
from utils.states import UserState
from utils.keyboard import get_payment_keyboard, get_back_keyboard


async def cmd_pay(message: types.Message):
    """
    Обработчик команды /pay
    Отправляет информацию о платежах и предлагает связаться с администратором
    """
    payment_text = (
        "💰 Оплата услуг Dream Photo AI\n\n"
        "Для использования сервиса необходимы токены:\n"
        "- 1 токен = 1 сгенерированное изображение\n"
        "- 10 токенов = 500 руб.\n"
        "- 25 токенов = 1000 руб.\n"
        "- 60 токенов = 2000 руб.\n\n"
        "📱 Свяжитесь с администратором для приобретения токенов"
    )
    
    # Создаем клавиатуру для связи с администратором
    keyboard = get_payment_keyboard()
    
    await message.answer(payment_text, reply_markup=keyboard)


async def process_payment(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обработчик нажатия на кнопку оплаты
    В текущей версии - это заглушка, которая предлагает связаться с администратором
    """
    await callback_query.answer()
    
    payment_info = (
        "📱 Для приобретения токенов:\n\n"
        "1. Напишите администратору: @admin_username\n"
        "2. Укажите желаемое количество токенов\n"
        "3. Получите инструкции по оплате\n\n"
        "После подтверждения оплаты, токены будут начислены на ваш счет"
    )
    
    keyboard = get_back_keyboard()
    
    await callback_query.message.answer(payment_info, reply_markup=keyboard)


def register_payment_handlers(dp: Dispatcher):
    """Регистрация обработчиков платежей"""
    dp.register_message_handler(cmd_pay, commands=["pay"])
    dp.register_callback_query_handler(process_payment, lambda c: c.data == "pay") 