from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.utils.markdown import hbold
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from datetime import datetime
import os

from app.repository.user import UserRepository
from app.utils.logger import logger

router = Router()


@router.message(CommandStart())
async def command_start(message: types.Message, state: FSMContext):
    await state.clear()

    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    user_repo = UserRepository()

    user = user_repo.get_by_id(user_id)
    if user is None:
        logger.info(f"Создание нового пользователя: {user_id} (@{username})")
        user_data = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "activation_dttm": datetime.now(),
            "tokens_left": 0,
            "blocked": False,
            "language": "ru",
            "user_state": "NEW"
        }
        created_user = user_repo.create(user_data)
        if not created_user:
            logger.error("Ошибка при создании пользователя")
            await message.answer("Произошла ошибка при регистрации. Попробуйте позже.")
            return
        await send_welcome_messages(message, created_user, is_new_user=True)
    else:
        await send_welcome_messages(message, user, is_new_user=False)


async def send_welcome_messages(message: types.Message, user: dict, is_new_user: bool):
    webapp_url = os.getenv("WEBAPP_URL", "https://localhost:3000")

    greeting = "👋 Привет" if is_new_user else "👋 С возвращением"
    text = (
        f"{greeting}, {hbold(message.from_user.full_name)}!\n\n"
        f"Я Dream Photo AI — твой помощник по созданию стильных фотографий с помощью ИИ."
    )
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🖼 Обучить модель", web_app=WebAppInfo(url=f"{webapp_url}/train")),
                KeyboardButton(text="👤 Личный кабинет", web_app=WebAppInfo(url=f"{webapp_url}/cabinet"))
            ],
            [
                KeyboardButton(text="⚙️ Выбор настроек", web_app=WebAppInfo(url=f"{webapp_url}/extra"))
            ]
        ],
        resize_keyboard=True,
        is_persistent=True
    )

    await message.answer(text, reply_markup=keyboard)

    features = (
        f"🔮 *Что я умею:*\n"
        f"• Генерация изображений\n"
        f"• Обучение моделей по фото\n"
        f"• Применение художественных стилей\n"
        f"• Создание аватаров, постеров и т.п.\n"
    )
    await message.answer(features, parse_mode="Markdown")

    tokens_msg = f"💰 *Твой баланс:*\n\nТокенов на счету: {user.get('tokens_left', 0)}"
    if user.get("tokens_left", 0) == 0:
        tokens_msg += "\nДля использования бота необходимо пополнить баланс."

    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Пополнить баланс", callback_data="add_balance")
    await message.answer(tokens_msg, parse_mode="Markdown", reply_markup=builder.as_markup())
