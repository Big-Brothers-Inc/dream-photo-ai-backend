from typing import List
import logging

from aiogram import Bot
from app.config import config  # <-- импорт настроек

logger = logging.getLogger(__name__)


def get_admin_ids() -> List[int]:
    """
    Получает список администраторов из pydantic-конфига
    """
    admin_ids = config.ADMIN_USER_IDS
    if not admin_ids:
        logger.warning("Список администраторов пуст. Уведомления не будут отправлены.")
    else:
        logger.debug(f"Получены ADMIN_USER_IDS: {admin_ids}")
    return admin_ids


async def notify_admins_about_payment(bot: Bot, user_id: int, username: str):
    """
    Уведомляет всех администраторов о запросе пополнения баланса от пользователя.
    """
    ADMIN_IDS = get_admin_ids()

    if not ADMIN_IDS:
        return

    message = (
        "💰 *Запрос на пополнение баланса*\n\n"
        f"Пользователь: @{username or 'неизвестно'}\n"
        f"ID: `{user_id}`\n\n"
        f"Для пополнения используйте:\n"
        f"`/add_tokens {user_id} <кол-во_токенов>`"
    )

    success_count = 0

    for admin_id in ADMIN_IDS:
        try:
            logger.debug(f"Отправка уведомления администратору {admin_id}")
            await bot.send_message(chat_id=admin_id, text=message, parse_mode="Markdown")
            logger.info(f"Уведомление отправлено администратору {admin_id}")
            success_count += 1
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение админу {admin_id}: {e}")

    if success_count:
        logger.info(f"Уведомления успешно отправлены {success_count} из {len(ADMIN_IDS)} администраторам")
    else:
        logger.error("Не удалось отправить уведомление ни одному администратору")
