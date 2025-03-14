from aiogram import Dispatcher

from .start_handler import register_start_handlers
from .payment_handler import register_payment_handlers
from .photo_handler import register_photo_handlers
from .training_handler import register_training_handlers
from .generation_handler import register_generation_handlers


def register_all_handlers(dp: Dispatcher):
    """Регистрация всех обработчиков сообщений"""
    handlers = [
        register_start_handlers,
        register_payment_handlers,
        register_photo_handlers,
        register_training_handlers,
        register_generation_handlers,
    ]
    
    for handler in handlers:
        handler(dp) 