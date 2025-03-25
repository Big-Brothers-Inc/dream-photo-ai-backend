from aiogram import Router
from aiogram.types import CallbackQuery
from app.utils.admin_notifications import notify_admins_about_payment
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
