from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def get_start_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для стартового сообщения
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("💰 Оплатить токены", callback_data="pay"),
        InlineKeyboardButton("📸 Загрузить фотографии", callback_data="upload")
    )
    return keyboard


def get_payment_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для меню оплаты
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("👨‍💼 Связаться с администратором", url="https://t.me/admin_username"),
        InlineKeyboardButton("📱 Написать в поддержку", url="https://t.me/support_username"),
        InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")
    )
    return keyboard


def get_back_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с кнопкой "Назад"
    """
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")
    )
    return keyboard


def get_models_keyboard(models: list) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру со списком моделей пользователя
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for model in models:
        keyboard.add(
            InlineKeyboardButton(
                f"🔮 {model['name']} ({model['status']})",
                callback_data=f"model_{model['id']}"
            )
        )
    
    keyboard.add(
        InlineKeyboardButton("🌐 Открыть веб-интерфейс", web_app={"url": "https://web-app-url.com"})
    )
    
    keyboard.add(
        InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")
    )
    
    return keyboard


def get_upload_finish_keyboard() -> ReplyKeyboardMarkup:
    """
    Создает клавиатуру для завершения загрузки фотографий
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(
        KeyboardButton("Завершить загрузку")
    )
    return keyboard 