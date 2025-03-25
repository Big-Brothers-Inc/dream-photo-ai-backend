from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.utils.markdown import hbold
import logging
from datetime import datetime
import os
from app.repository import get_user_repository
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

# Настройка логирования
logger = logging.getLogger(__name__)

router = Router()


@router.message(CommandStart())
async def command_start(message: types.Message, state: FSMContext):
    """Обработчик команды /start"""
    await state.clear()

    # Получаем данные пользователя из сообщения
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    # Получаем репозиторий пользователей
    user_repo = get_user_repository()
    if user_repo is None:
        logger.error("Не удалось получить репозиторий пользователей")
        await message.answer("Произошла ошибка при регистрации. Попробуйте позже.")
        return

    # Проверяем, существует ли пользователь в базе данных
    user = user_repo.get_by_id(user_id)

    if user is None:
        # Создаем нового пользователя
        logger.info(f"Создание нового пользователя: {user_id} (@{username})")

        # Подготавливаем данные для создания пользователя
        user_data = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "activation_date": datetime.now(),
            "tokens_left": 0,  # Начальное количество токенов (изменено с 10 на 0)
            "tokens_spent": 0,
            "blocked": False,
            "language": "ru",
            "user_state": "new",
            "images_generated": 0,
            "models_trained": 0,
            "registration_complete": True
        }

        # Создаем пользователя
        created_user = user_repo.create(user_data)

        if created_user is None:
            logger.error(f"Ошибка при создании пользователя: {user_id}")
            await message.answer("Произошла ошибка при регистрации. Попробуйте позже.")
            return

        logger.info(f"Пользователь успешно создан: {user_id}")

        # Показываем приветственное сообщение для нового пользователя
        await send_welcome_messages(message, created_user, is_new_user=True)
    else:
        # Пользователь уже существует
        logger.info(f"Пользователь уже существует: {user_id} (@{username})")

        # Показываем приветственное сообщение для существующего пользователя
        await send_welcome_messages(message, user, is_new_user=False)


async def send_welcome_messages(message: types.Message, user: dict, is_new_user: bool):
    """Отправляет серию приветственных сообщений с информацией о боте"""

    # Первое сообщение - приветствие
    if is_new_user:
        welcome_message = f"👋 Привет, {hbold(message.from_user.full_name)}!\n\n"
        welcome_message += f"Добро пожаловать в Dream Photo AI! Я твой персональный помощник для создания стильных фотографий "
        welcome_message += f"с использованием искусственного интеллекта."
    else:
        welcome_message = f"👋 С возвращением, {hbold(message.from_user.full_name)}!\n\n"
        welcome_message += f"Я Dream Photo AI - твой персональный помощник для создания стильных фотографий "
        welcome_message += f"с использованием искусственного интеллекта."

    # Создаем постоянные кнопки для запуска web app
    webapp_url = os.getenv("WEBAPP_URL", "https://localhost:3000")

    # Проверяем источник URL для логирования
    if 'pinggy.link' in webapp_url:
        logger.info(f"Используем Pinggy URL для фронтенда: {webapp_url}")
    elif 'ngrok-free.app' in webapp_url:
        logger.info(f"Используем ngrok URL для фронтенда: {webapp_url}")
    else:
        logger.info(f"Используем стандартный URL для фронтенда: {webapp_url}")

    # Создаем кнопочную клавиатуру с веб-приложениями
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="🖼 Обучить модель",
                    web_app=WebAppInfo(url=f"{webapp_url}/train")
                ),
                KeyboardButton(
                    text="👤 Личный кабинет",
                    web_app=WebAppInfo(url=f"{webapp_url}/cabinet")
                ),
            ],
            [
                KeyboardButton(
                    text="⚙️ Выбор настроек",
                    web_app=WebAppInfo(url=f"{webapp_url}/extra")
                )
            ]
        ],
        resize_keyboard=True,
        is_persistent=True
    )

    await message.answer(welcome_message, reply_markup=keyboard)

    # Второе сообщение - о возможностях бота
    features_message = f"🔮 *Что я умею:*\n\n"
    features_message += f"• Обучаться на твоих фотографиях и создавать уникальный стиль\n"
    features_message += f"• Генерировать новые фотографии на основе твоего стиля и описания\n"
    features_message += f"• Применять различные художественные стили к твоим фотографиям\n"
    features_message += f"• Создавать аватарки, портреты, постеры и многое другое\n\n"

    await message.answer(features_message, parse_mode="Markdown")

    # Третье сообщение - о балансе и кнопка пополнения
    tokens_message = f"💰 *Твой баланс:*\n\n"
    tokens_message += f"Токенов на счету: {user.get('tokens_left', 0)}\n"

    if user.get('tokens_left', 0) == 0:
        tokens_message += f"\nДля использования бота необходимо пополнить баланс."

    # Создаем инлайн-кнопку для пополнения баланса
    builder = InlineKeyboardBuilder()
    builder.button(text="💎 Пополнить баланс", callback_data="add_balance")

    await message.answer(tokens_message, reply_markup=builder.as_markup(), parse_mode="Markdown")


@router.message(Command("help"))
async def command_help(message: types.Message):
    """Обработчик команды /help"""
    await message.answer(
        f"📚 {hbold('Доступные команды:')}\n\n"
        f"/start - Начать работу с ботом\n"
        f"/help - Показать это сообщение\n"
        f"/webapp - Показать кнопки для веб-приложения\n"
        f"/train - Обучить модель на ваших фотографиях\n"
        f"/generate - Создать новое изображение\n"
        f"/models - Показать ваши обученные модели\n"
        f"/settings - Настройки профиля\n"
        f"/cancel - Отменить текущую операцию"
    )


@router.message(Command("cancel"))
async def command_cancel(message: types.Message, state: FSMContext):
    """Обработчик команды /cancel для отмены текущего действия"""
    current_state = await state.get_state()

    if current_state is None:
        await message.answer("🤷‍♂️ Нечего отменять, вы не выполняете никаких действий.")
        return

    await state.clear()
    await message.answer("🔄 Действие отменено. Используйте /help для просмотра доступных команд.")


# Добавляем обработчик нажатия на кнопку "Пополнить баланс"
@router.callback_query(lambda c: c.data == "add_balance")
async def process_add_balance(callback: types.CallbackQuery):
    """Обрабатывает нажатие на кнопку пополнения баланса"""
    user_id = callback.from_user.id
    username = callback.from_user.username or "без имени"

    # Сообщаем пользователю, что запрос принят
    await callback.answer("Запрос на пополнение баланса отправлен")
    await callback.message.answer("✅ Запрос на пополнение баланса принят! Администратор скоро свяжется с вами.")

    # Импортируем модуль admin_notifications только здесь, чтобы избежать циклического импорта
    from .admin_notifications import notify_admins_about_payment

    try:
        # Получаем экземпляр бота из контекста callback
        bot = callback.bot

        # Отправляем сообщение администраторам, передавая бота как параметр
        await notify_admins_about_payment(bot, user_id, username)
        logger.info(f"Запрос на пополнение баланса от пользователя {user_id} отправлен администраторам")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления администраторам: {e}")


@router.message(Command("webapp"))
async def command_webapp(message: types.Message):
    """Показывает клавиатуру с Web App кнопками"""
    # Получаем URL из переменных окружения
    webapp_url = os.getenv("WEBAPP_URL", "https://localhost:3000")

    # Проверяем источник URL для логирования
    if 'pinggy.link' in webapp_url:
        logger.info(f"Используем Pinggy URL для фронтенда: {webapp_url}")
    elif 'ngrok-free.app' in webapp_url:
        logger.info(f"Используем ngrok URL для фронтенда: {webapp_url}")
    else:
        logger.info(f"Используем стандартный URL для фронтенда: {webapp_url}")

    # Создаем кнопочную клавиатуру с веб-приложениями
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="🖼 Обучить модель",
                    web_app=WebAppInfo(url=f"{webapp_url}/train")
                ),
                KeyboardButton(
                    text="👤 Личный кабинет",
                    web_app=WebAppInfo(url=f"{webapp_url}/cabinet")
                ),
            ],
            [
                KeyboardButton(
                    text="⚙️ Выбор настроек",
                    web_app=WebAppInfo(url=f"{webapp_url}/extra")
                )
            ]
        ],
        resize_keyboard=True,
        is_persistent=True
    )

    await message.answer("Выберите действие:", reply_markup=keyboard)
