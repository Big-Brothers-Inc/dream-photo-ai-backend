from aiogram import Router
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.utils.admin_notifications import notify_admins_about_payment
from app.repository.user import UserRepository
import logging

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(lambda c: c.data == "add_balance")
async def process_add_balance(callback: CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.username or "без имени"

    await callback.answer("Запрос на пополнение отправлен")
    await callback.message.answer("✅ Запрос отправлен! С вами свяжется администратор.")

    try:
        await notify_admins_about_payment(callback.bot, user_id, username)
        logger.info(f"Баланс-запрос от {user_id} отправлен админам")
    except Exception as e:
        logger.error(f"Ошибка при отправке админам: {e}")


@router.message(Command("check_balance"))
async def check_balance(message: Message):
    user_id = message.from_user.id
    user_repo = UserRepository()
    user = user_repo.get_by_id(user_id)

    if user:
        builder = InlineKeyboardBuilder()
        builder.button(text="💳 Пополнить баланс", callback_data="add_balance")

        await message.answer(
            f"💰 <b>Ваш текущий баланс:</b> <code>{user['tokens_left']}</code> токенов",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Пользователь не найден.", parse_mode="HTML")