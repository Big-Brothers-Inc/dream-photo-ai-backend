import os
import logging
from aiogram import Bot
from typing import List

# Настройка логирования
logger = logging.getLogger(__name__)

# Получаем список ID администраторов из переменных окружения
admin_ids_str = os.getenv("ADMIN_USER_IDS", "")
logger.info(f"Значение ADMIN_USER_IDS из .env: '{admin_ids_str}'")

# Парсим список ID администраторов
ADMIN_IDS = []
if admin_ids_str:
    try:
        ADMIN_IDS = [int(id_str) for id_str in admin_ids_str.split(",") if id_str.strip().isdigit()]
        logger.info(f"Распознанные ID администраторов: {ADMIN_IDS}")
    except Exception as e:
        logger.error(f"Ошибка при парсинге ID администраторов: {e}")
else:
    logger.warning("Переменная ADMIN_USER_IDS не установлена или пуста")


async def notify_admins_about_payment(bot: Bot, user_id: int, username: str):
    """
    Отправляет уведомление всем администраторам о запросе на пополнение баланса
    
    Args:
        bot: Экземпляр бота для отправки сообщений
        user_id: ID пользователя, запросившего пополнение
        username: Имя пользователя
    """
    if not ADMIN_IDS:
        logger.warning("Список администраторов пуст. Уведомления не будут отправлены.")
        return
    
    # Формируем текст сообщения
    message_text = f"💰 *Запрос на пополнение баланса*\n\n"
    message_text += f"Пользователь: @{username}\n"
    message_text += f"ID пользователя: `{user_id}`\n\n"
    message_text += f"Для пополнения баланса используйте команду:\n"
    message_text += f"`/add_tokens {user_id} <количество_токенов>`"
    
    # Отправляем сообщение всем администраторам
    sent_count = 0
    for admin_id in ADMIN_IDS:
        try:
            logger.info(f"Отправка уведомления администратору {admin_id}")
            await bot.send_message(admin_id, message_text, parse_mode="Markdown")
            logger.info(f"Уведомление успешно отправлено администратору {admin_id}")
            sent_count += 1
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления администратору {admin_id}: {e}")
    
    if sent_count > 0:
        logger.info(f"Уведомления о запросе пополнения баланса от пользователя {user_id} отправлены {sent_count} администраторам")
    else:
        logger.error(f"Не удалось отправить уведомление ни одному администратору для пользователя {user_id}") 