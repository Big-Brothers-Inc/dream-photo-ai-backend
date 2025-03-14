import logging
import asyncio
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
import sys
import os

# Добавляем родительскую директорию в sys.path для импорта из других модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loader.bot import bot
from utils.states import UserState
from utils.notifications import notify_model_ready
from repository.model_repo import get_model, update_model_status, update_model_preview
from services.replicate_service import check_training_status


async def check_training_progress(user_id: int, model_id: int, training_id: str):
    """
    Периодически проверяет статус обучения модели
    
    Args:
        user_id (int): ID пользователя в Telegram
        model_id (int): ID модели
        training_id (str): ID тренировки в API Replicate
    """
    try:
        # Первоначальная задержка для начала обучения
        await asyncio.sleep(60)
        
        while True:
            # Получаем статус обучения
            status = await check_training_status(training_id)
            
            logging.info(f"Проверка статуса обучения: {status} для модели {model_id}")
            
            if status == "succeeded":
                # Обучение успешно завершено
                model = get_model(model_id)
                update_model_status(model_id, "ready")
                
                # Устанавливаем URL превью (в реальном проекте нужно будет получить его из API)
                # Здесь просто заглушка для примера
                update_model_preview(model_id, f"https://example.com/previews/{model_id}.jpg")
                
                # Отправляем уведомление пользователю
                await notify_model_ready(user_id, model.name)
                
                break
                
            elif status == "failed":
                # Обучение завершилось с ошибкой
                update_model_status(model_id, "error")
                
                # Отправляем уведомление пользователю
                await bot.send_message(
                    user_id,
                    "❌ К сожалению, обучение модели завершилось с ошибкой.\n"
                    "Пожалуйста, попробуйте загрузить другие фотографии или свяжитесь с администратором."
                )
                
                break
                
            # Ждем некоторое время перед следующей проверкой
            await asyncio.sleep(300)  # Проверяем каждые 5 минут
            
    except Exception as e:
        logging.error(f"Ошибка при проверке статуса обучения: {e}")
        
        # Обновляем статус модели в случае ошибки
        update_model_status(model_id, "error")
        
        # Отправляем уведомление пользователю
        await bot.send_message(
            user_id,
            "❌ Произошла ошибка при проверке статуса обучения модели.\n"
            "Пожалуйста, свяжитесь с администратором."
        )


async def start_training_check(message: types.Message, state: FSMContext):
    """
    Запускает периодическую проверку статуса обучения модели
    """
    # Получаем данные из состояния
    data = await state.get_data()
    training_id = data.get("training_id")
    model_id = data.get("model_id")
    
    if not training_id or not model_id:
        await message.answer(
            "❌ Не удалось начать проверку статуса обучения модели.\n"
            "Отсутствуют необходимые данные."
        )
        return
    
    # Запускаем задачу проверки статуса обучения
    asyncio.create_task(check_training_progress(message.from_user.id, model_id, training_id))
    
    await message.answer(
        "✅ Обучение модели запущено!\n"
        "Этот процесс может занять около 15-20 минут.\n"
        "Вы получите уведомление, когда модель будет готова к использованию."
    )


def register_training_handlers(dp: Dispatcher):
    """Регистрация обработчиков для обучения моделей"""
    dp.register_message_handler(
        start_training_check,
        lambda message: message.text == "Начать проверку обучения",
        state=UserState.waiting_training
    ) 