import os
import zipfile
import logging
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
import sys

# Добавляем родительскую директорию в sys.path для импорта из других модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loader.bot import bot
from config.config import PHOTO_STORAGE_PATH, MIN_PHOTOS_REQUIRED, MAX_PHOTOS_ALLOWED
from utils.states import UserState
from utils.notifications import notify_user
from repository.model_repo import create_model, update_model_status
from services.replicate_service import train_model


# Создаем директорию для хранения фотографий, если её не существует
os.makedirs(PHOTO_STORAGE_PATH, exist_ok=True)


async def start_photo_upload(message: types.Message, state: FSMContext):
    """
    Обработчик команды /upload
    Начинает процесс загрузки фотографий
    """
    user_id = message.from_user.id
    
    # Создаем папку для пользователя, если её не существует
    user_folder = os.path.join(PHOTO_STORAGE_PATH, str(user_id))
    os.makedirs(user_folder, exist_ok=True)
    
    # Очищаем папку от предыдущих фотографий
    for file in os.listdir(user_folder):
        file_path = os.path.join(user_folder, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
    
    # Переводим пользователя в состояние загрузки фотографий
    await state.set_state(UserState.uploading_photos)
    
    # Сохраняем пустой список фотографий в состояние
    await state.update_data(photos=[])
    
    upload_text = (
        f"📸 Начинаем загрузку фотографий\n\n"
        f"Пожалуйста, загрузите от {MIN_PHOTOS_REQUIRED} до {MAX_PHOTOS_ALLOWED} фотографий "
        f"вашего лица в хорошем качестве.\n\n"
        f"Рекомендации:\n"
        f"✅ Различные ракурсы и освещение\n"
        f"✅ Четкое изображение лица\n"
        f"✅ Однородный фон\n"
        f"❌ Избегайте фото с другими людьми\n"
        f"❌ Не используйте фото с сильными искажениями\n\n"
        f"Отправьте фотографии по одной. После загрузки всех фото, "
        f"нажмите кнопку 'Завершить загрузку'"
    )
    
    await message.answer(upload_text, reply_markup=types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Завершить загрузку")]
        ],
        resize_keyboard=True
    ))


async def process_photo(message: types.Message, state: FSMContext):
    """
    Обработчик загрузки фотографий
    Сохраняет фотографии в папку пользователя
    """
    # Получаем данные из состояния
    data = await state.get_data()
    photos = data.get("photos", [])
    
    # Проверяем, не превышено ли максимальное количество фотографий
    if len(photos) >= MAX_PHOTOS_ALLOWED:
        await message.answer(f"Вы уже загрузили максимальное количество фотографий ({MAX_PHOTOS_ALLOWED}).")
        return
    
    user_id = message.from_user.id
    user_folder = os.path.join(PHOTO_STORAGE_PATH, str(user_id))
    
    # Получаем фото в наилучшем качестве
    photo = message.photo[-1]
    
    # Загружаем файл
    file_id = photo.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    
    # Генерируем имя файла
    photo_name = f"{len(photos) + 1}.jpg"
    destination = os.path.join(user_folder, photo_name)
    
    # Сохраняем файл
    await bot.download_file(file_path, destination)
    
    # Добавляем путь к файлу в список фотографий
    photos.append(destination)
    await state.update_data(photos=photos)
    
    # Отправляем сообщение о успешной загрузке
    await message.answer(
        f"✅ Фото #{len(photos)} загружено.\n"
        f"Загружено {len(photos)} из {MAX_PHOTOS_ALLOWED} фотографий.\n"
        f"Для завершения загрузки необходимо минимум {MIN_PHOTOS_REQUIRED} фото."
    )


async def finish_photo_upload(message: types.Message, state: FSMContext):
    """
    Обработчик завершения загрузки фотографий
    Создает ZIP-архив и отправляет его на обучение модели
    """
    # Получаем данные из состояния
    data = await state.get_data()
    photos = data.get("photos", [])
    
    # Проверяем, загружено ли минимальное количество фотографий
    if len(photos) < MIN_PHOTOS_REQUIRED:
        await message.answer(
            f"❌ Вы загрузили недостаточное количество фотографий.\n"
            f"Необходимо минимум {MIN_PHOTOS_REQUIRED}, у вас загружено {len(photos)}.\n"
            f"Пожалуйста, загрузите еще фотографии."
        )
        return
    
    user_id = message.from_user.id
    user_folder = os.path.join(PHOTO_STORAGE_PATH, str(user_id))
    zip_path = os.path.join(PHOTO_STORAGE_PATH, f"{user_id}.zip")
    
    # Создаем ZIP-архив с фотографиями
    with zipfile.ZipFile(zip_path, "w") as zip_file:
        for photo_path in photos:
            photo_name = os.path.basename(photo_path)
            zip_file.write(photo_path, photo_name)
    
    # Отправляем сообщение о начале обучения модели
    await message.answer(
        "✅ Все фотографии успешно загружены!\n\n"
        "Начинаю обучение персональной модели. Это может занять некоторое время (примерно 15-20 минут).\n"
        "Вы получите уведомление, когда модель будет готова к использованию.",
        reply_markup=types.ReplyKeyboardRemove()
    )
    
    # Создаем модель в базе данных
    model_name = f"model_{user_id}_{len(photos)}"
    trigger_word = f"TOK_{user_id}"
    model_id = create_model(user_id, model_name, trigger_word)
    
    # Запускаем обучение модели
    try:
        # Отправляем ZIP-архив на обучение
        training_id = await train_model(zip_path, model_name, trigger_word)
        
        # Обновляем статус модели в базе данных
        update_model_status(model_id, "training", training_id)
        
        # Сохраняем training_id в состоянии пользователя
        await state.update_data(training_id=training_id, model_id=model_id)
        
        # Переводим пользователя в состояние ожидания обучения
        await state.set_state(UserState.waiting_training)
        
    except Exception as e:
        logging.error(f"Ошибка при обучении модели: {e}")
        await message.answer(
            "❌ Произошла ошибка при обучении модели.\n"
            "Пожалуйста, попробуйте позже или свяжитесь с администратором."
        )
        update_model_status(model_id, "error")
        await state.finish()


def register_photo_handlers(dp: Dispatcher):
    """Регистрация обработчиков фотографий"""
    dp.register_message_handler(start_photo_upload, commands=["upload"])
    dp.register_message_handler(process_photo, content_types=["photo"], state=UserState.uploading_photos)
    dp.register_message_handler(
        finish_photo_upload,
        lambda message: message.text == "Завершить загрузку",
        state=UserState.uploading_photos
    ) 