import logging
import os
from aiogram import Router, types
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from repository import get_user_repository, get_model_repository

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаем роутер для обработчиков обучения модели
training_router = Router()


# Определяем состояния для машины состояний
class TrainingStates(StatesGroup):
    waiting_for_photos = State()
    processing_photos = State()
    confirming_training = State()


# Получаем URL для WebApp из переменных окружения
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://example.com")
TRAINING_APP_URL = f"{WEBAPP_URL}/train-model"


# Обработчик нажатия кнопки "Обучить модель"
@training_router.callback_query(lambda c: c.data == "start_training")
async def process_start_training(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает нажатие на кнопку начала обучения модели"""
    user_id = callback.from_user.id

    # Получаем репозиторий пользователей
    user_repo = get_user_repository()
    if user_repo is None:
        logger.error(f"Не удалось получить репозиторий пользователей")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)
        return

    # Проверяем, достаточно ли у пользователя токенов для обучения модели
    user = user_repo.get_by_id(user_id)
    if not user:
        logger.error(f"Пользователь {user_id} не найден")
        await callback.answer("❌ Пользователь не найден.", show_alert=True)
        return

    tokens_left = user.get('tokens_left', 0)
    training_cost = 300  # Стоимость обучения модели

    if tokens_left < training_cost:
        await callback.answer(f"❌ Недостаточно токенов. Требуется {training_cost}, у вас {tokens_left}.",
                              show_alert=True)
        return

    # Отправляем пользователю Web App для выбора фотографий и обучения модели
    await callback.answer()

    # Создаем кнопку для открытия miniApp
    webapp_button = InlineKeyboardBuilder()
    webapp_button.button(
        text="📷 Выбрать фотографии для обучения",
        web_app=types.WebAppInfo(url=TRAINING_APP_URL)
    )

    # Отправляем сообщение с инструкцией и кнопкой
    message_text = "🖼 *Выберите фотографии для обучения модели*\n\n"
    message_text += "Нажмите на кнопку ниже, чтобы открыть интерфейс выбора фотографий. "
    message_text += "Выберите 10-20 качественных фотографий вашего лица для лучшего результата.\n\n"
    message_text += f"С вашего счета будет списано *{training_cost} токенов* после начала обучения."

    logger.info(f"Отправка пользователю {user_id} WebApp для обучения модели по URL: {TRAINING_APP_URL}")

    await callback.message.answer(message_text, reply_markup=webapp_button.as_markup(), parse_mode="Markdown")

    # Устанавливаем состояние ожидания фотографий
    await state.set_state(TrainingStates.waiting_for_photos)


# Обработчик нажатия кнопки "Как выбрать фотографии"
@training_router.callback_query(lambda c: c.data == "training_guide")
async def process_training_guide(callback: CallbackQuery):
    """Отправляет гайд по выбору фотографий для обучения модели"""
    await callback.answer()

    guide_text = "📚 *Как выбрать фотографии для обучения модели*\n\n"
    guide_text += "Для достижения наилучших результатов при обучении модели, следуйте этим рекомендациям:\n\n"
    guide_text += "✅ *Выберите 10-20 фотографий* — оптимальное количество для обучения\n\n"
    guide_text += "✅ *Качество фотографий*:\n"
    guide_text += "• Хорошее освещение, без теней на лице\n"
    guide_text += "• Высокое разрешение (не менее 512x512 пикселей)\n"
    guide_text += "• Четкое изображение лица без размытия\n\n"

    guide_text += "✅ *Разнообразие*:\n"
    guide_text += "• Разные ракурсы лица (анфас, профиль, 3/4)\n"
    guide_text += "• Разные выражения лица (улыбка, серьезное и т.д.)\n"
    guide_text += "• Разные фоны (но не слишком отвлекающие)\n\n"

    guide_text += "❌ *Избегайте*:\n"
    guide_text += "• Фотографий с другими людьми в кадре\n"
    guide_text += "• Снимков в очках или с закрытыми частями лица\n"
    guide_text += "• Чрезмерной обработки и фильтров\n"
    guide_text += "• Слишком темных или слишком ярких изображений\n\n"

    guide_text += "⚠️ *Важно*: Модель обучается распознавать ваше лицо, поэтому качество исходных фотографий напрямую влияет на результат генерации."

    # Создаем кнопку "Обучить модель"
    builder = InlineKeyboardBuilder()
    builder.button(text="🧠 Обучить модель", callback_data="start_training")

    await callback.message.answer(guide_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


# Функция для отображения информации о процессе и стоимости обучения
@training_router.message(Command("train"))
async def cmd_train(message: Message):
    """Обрабатывает команду /train и показывает информацию о процессе обучения модели"""
    user_id = message.from_user.id

    # Получаем репозиторий пользователей для проверки баланса
    user_repo = get_user_repository()
    if user_repo is None:
        logger.error(f"Не удалось получить репозиторий пользователей")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")
        return

    # Получаем данные пользователя
    user = user_repo.get_by_id(user_id)
    if not user:
        logger.error(f"Пользователь {user_id} не найден")
        await message.answer("❌ Пользователь не найден.")
        return

    tokens_left = user.get('tokens_left', 0)
    training_cost = 300

    # Проверяем наличие обученных моделей
    model_repo = get_model_repository()
    if model_repo is None:
        logger.error(f"Не удалось получить репозиторий моделей")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")
        return

    user_models = model_repo.get_models_by_user(user_id, status="ready")

    # Формируем текст сообщения
    message_text = "🧠 *Обучение персональной модели*\n\n"

    if user_models:
        message_text += f"У вас уже есть {len(user_models)} обученных моделей.\n\n"
        message_text += "Вы можете обучить новую модель или использовать существующие для генерации изображений.\n"
    else:
        message_text += "У вас пока нет обученных моделей. Создайте свою первую модель для генерации персонализированных изображений!\n\n"

    message_text += f"Стоимость обучения новой модели: *{training_cost} токенов*\n"
    message_text += f"Ваш текущий баланс: *{tokens_left} токенов*\n\n"

    if tokens_left < training_cost:
        message_text += f"⚠️ Для обучения модели необходимо пополнить баланс еще на {training_cost - tokens_left} токенов."

        # Создаем кнопку для пополнения баланса
        builder = InlineKeyboardBuilder()
        builder.button(text="💎 Пополнить баланс", callback_data="add_balance")
    else:
        # Создаем кнопки для начала обучения и просмотра гайда
        builder = InlineKeyboardBuilder()
        builder.button(text="🧠 Обучить модель", callback_data="start_training")
        builder.button(text="❓ Как выбрать фотографии", callback_data="training_guide")

    builder.adjust(1)  # Ставим кнопки одну под другой

    await message.answer(message_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


def setup_training_handlers(dp):
    """
    Регистрация обработчиков для функционала обучения модели
    """
    dp.include_router(training_router)
