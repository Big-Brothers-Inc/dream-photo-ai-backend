import logging
import sys
import os

# Добавляем родительскую директорию в sys.path для импорта из других модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loader.bot import bot
from repository.admin_repo import get_admin_ids


async def notify_user(user_id: int, message: str):
    """
    Отправляет уведомление пользователю
    
    Args:
        user_id (int): ID пользователя в Telegram
        message (str): Текст сообщения
    """
    try:
        await bot.send_message(user_id, message)
        return True
    except Exception as e:
        logging.error(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")
        return False


async def send_admin_notification(message: str):
    """
    Отправляет уведомление всем администраторам
    
    Args:
        message (str): Текст сообщения
    """
    admin_ids = get_admin_ids()
    
    for admin_id in admin_ids:
        try:
            await bot.send_message(admin_id, f"🔔 УВЕДОМЛЕНИЕ: {message}")
        except Exception as e:
            logging.error(f"Ошибка при отправке уведомления администратору {admin_id}: {e}")


async def notify_model_ready(user_id: int, model_name: str):
    """
    Отправляет уведомление пользователю о готовности модели
    
    Args:
        user_id (int): ID пользователя в Telegram
        model_name (str): Название модели
    """
    message = (
        f"🎉 Ваша модель *{model_name}* успешно обучена и готова к использованию!\n\n"
        f"Теперь вы можете генерировать изображения с помощью команды /generate\n"
        f"или нажав кнопку ниже."
    )
    
    try:
        from utils.keyboard import get_models_keyboard
        from repository.model_repo import get_user_models
        
        # Получаем список моделей пользователя
        models = get_user_models(user_id)
        
        # Создаем клавиатуру с моделями
        keyboard = get_models_keyboard(models)
        
        await bot.send_message(user_id, message, reply_markup=keyboard, parse_mode="Markdown")
        return True
    except Exception as e:
        logging.error(f"Ошибка при отправке уведомления о готовности модели пользователю {user_id}: {e}")
        await notify_user(user_id, message)
        return False 