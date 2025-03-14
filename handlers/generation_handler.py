import logging
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import sys
import os

# Добавляем родительскую директорию в sys.path для импорта из других модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loader.bot import bot
from config.config import WEBAPP_URL
from utils.states import UserState
from utils.keyboard import get_models_keyboard
from repository.user_repo import get_user_tokens, update_user_tokens
from repository.model_repo import get_user_models, get_model
from services.replicate_service import generate_image


async def cmd_generate(message: types.Message):
    """
    Обработчик команды /generate
    Показывает пользователю его модели и возможность генерации изображений
    """
    user_id = message.from_user.id
    
    # Получаем список моделей пользователя
    models = get_user_models(user_id)
    
    if not models:
        await message.answer(
            "❌ У вас еще нет обученных моделей.\n"
            "Загрузите фотографии с помощью команды /upload для обучения вашей первой модели."
        )
        return
    
    # Получаем количество доступных токенов
    tokens = get_user_tokens(user_id)
    
    # Проверяем, достаточно ли токенов для генерации
    if tokens <= 0:
        await message.answer(
            "❌ У вас недостаточно токенов для генерации изображений.\n"
            "Воспользуйтесь командой /pay для приобретения токенов."
        )
        return
    
    # Создаем клавиатуру с моделями
    keyboard = get_models_keyboard(models)
    
    await message.answer(
        f"🔮 Генерация изображений\n\n"
        f"У вас {tokens} токенов.\n"
        f"1 токен = 1 сгенерированное изображение.\n\n"
        f"Выберите модель для генерации:",
        reply_markup=keyboard
    )


async def select_model(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обработчик выбора модели для генерации
    """
    await callback_query.answer()
    
    # Извлекаем ID модели из callback_data
    model_id = int(callback_query.data.split("_")[1])
    
    # Получаем информацию о модели
    model = get_model(model_id)
    
    if not model:
        await callback_query.message.answer(
            "❌ Выбранная модель не найдена.\n"
            "Пожалуйста, выберите другую модель."
        )
        return
    
    # Проверяем статус модели
    if model.status != "ready":
        await callback_query.message.answer(
            f"❌ Модель {model.name} еще не готова к использованию.\n"
            f"Текущий статус: {model.status}\n"
            f"Пожалуйста, дождитесь завершения обучения или выберите другую модель."
        )
        return
    
    # Сохраняем ID выбранной модели в состоянии
    await state.update_data(model_id=model_id)
    
    # Переводим пользователя в состояние генерации
    await state.set_state(UserState.generating_image)
    
    # Создаем кнопку для открытия Telegram Web App
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            "🖼 Открыть веб-интерфейс для генерации",
            web_app={"url": f"{WEBAPP_URL}?model_id={model_id}"}
        )
    )
    
    await callback_query.message.answer(
        f"✅ Выбрана модель: {model.name}\n\n"
        f"Теперь вы можете сгенерировать изображение с помощью этой модели.\n"
        f"Нажмите на кнопку ниже, чтобы открыть веб-интерфейс для генерации.",
        reply_markup=keyboard
    )


async def process_generation(message: types.Message, state: FSMContext):
    """
    Обработчик запроса на генерацию изображения
    """
    # Получаем данные из состояния
    data = await state.get_data()
    model_id = data.get("model_id")
    
    if not model_id:
        await message.answer(
            "❌ Не выбрана модель для генерации.\n"
            "Воспользуйтесь командой /generate и выберите модель."
        )
        await state.finish()
        return
    
    # Получаем информацию о пользователе и модели
    user_id = message.from_user.id
    tokens = get_user_tokens(user_id)
    model = get_model(model_id)
    
    # Проверяем, достаточно ли токенов
    if tokens <= 0:
        await message.answer(
            "❌ У вас недостаточно токенов для генерации изображений.\n"
            "Воспользуйтесь командой /pay для приобретения токенов."
        )
        await state.finish()
        return
    
    # Получаем запрос для генерации
    prompt = message.text
    
    # Проверяем наличие триггер-слова в запросе
    if model.trigger_word not in prompt:
        prompt = f"{model.trigger_word}, {prompt}"
    
    # Отправляем сообщение о начале генерации
    await message.answer(
        "⏳ Начинаю генерацию изображения...\n"
        "Это может занять некоторое время."
    )
    
    try:
        # Генерируем изображение
        result = await generate_image(model_id, prompt)
        
        # Списываем токен
        update_user_tokens(user_id, -1)
        
        # Отправляем сгенерированное изображение
        for image_url in result:
            await bot.send_photo(
                user_id,
                photo=image_url,
                caption=f"✅ Изображение сгенерировано!\n"
                        f"Модель: {model.name}\n"
                        f"Запрос: {prompt}\n\n"
                        f"Осталось токенов: {get_user_tokens(user_id)}"
            )
        
    except Exception as e:
        logging.error(f"Ошибка при генерации изображения: {e}")
        await message.answer(
            "❌ Произошла ошибка при генерации изображения.\n"
            "Пожалуйста, попробуйте позже или свяжитесь с администратором."
        )
    
    # Завершаем состояние генерации
    await state.finish()


def register_generation_handlers(dp: Dispatcher):
    """Регистрация обработчиков для генерации изображений"""
    dp.register_message_handler(cmd_generate, commands=["generate"])
    dp.register_callback_query_handler(
        select_model,
        lambda c: c.data.startswith("model_")
    )
    dp.register_message_handler(
        process_generation,
        state=UserState.generating_image,
        content_types=types.ContentTypes.TEXT
    ) 