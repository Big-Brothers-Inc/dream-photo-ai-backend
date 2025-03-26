from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from app.repository.lora import LoraRepository
from app.utils.permissions import has_admin_permission

router = Router()
repo = LoraRepository()


class LoraCreateState(StatesGroup):
    entering_name = State()
    configuring = State()
    editing_field = State()


PARAMETERS = ["description", "lora_url", "trigger_word", "default_weight", "prompt_text", "preview_url", "sex", "is_active"]
DEFAULTS = {
    "description": "",
    "lora_url": "",
    "trigger_word": "",
    "default_weight": 1.0,
    "prompt_text": "",
    "preview_url": "",
    "is_active": True,
    "sex": False
}

PARAM_MAP = {
    "lora_edit_desc": "description",
    "lora_edit_url": "lora_url",
    "lora_edit_trigger": "trigger_word",
    "lora_edit_weight": "default_weight",
    "lora_edit_prompt": "prompt_text",
    "lora_edit_preview": "preview_url",
    "lora_edit_sex": "sex",
    "lora_edit_active": "is_active"
}


def create_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Описание", callback_data="lora_edit_desc")],
        [InlineKeyboardButton(text="🌐 URL LoRA", callback_data="lora_edit_url")],
        [InlineKeyboardButton(text="🔤 Триггер-слово", callback_data="lora_edit_trigger")],
        [InlineKeyboardButton(text="⚖️ Вес по умолчанию", callback_data="lora_edit_weight")],
        [InlineKeyboardButton(text="🧠 Промпт", callback_data="lora_edit_prompt")],
        [InlineKeyboardButton(text="🖼 Превью", callback_data="lora_edit_preview")],
        [InlineKeyboardButton(text="🚻 Пол", callback_data="lora_edit_sex")],
        [InlineKeyboardButton(text="✅ Активна", callback_data="lora_edit_active")],
        [
            InlineKeyboardButton(text="✅ Готово", callback_data="done_lora"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_lora")
        ]
    ])


def format_config_text(data):
    def truncate(text, max_len=500):
        return text if len(text) <= max_len else text[:max_len] + "..."

    return (
        f"🆕 Создание LoRA:\n"
        f"🔤 Название: {data['name']}\n"
        f"📝 Описание: {data['description']}\n"
        f"🌐 URL: {data['lora_url']}\n"
        f"🔤 Триггер: {data['trigger_word']}\n"
        f"⚖️ Вес: {data['default_weight']}\n"
        f"🧠 Промпт: {truncate(data['prompt_text'])}\n"
        f"🖼 Превью: {data['preview_url']}\n"
        f"🚻 Пол: {'Мужской' if data['sex'] else 'Женский'}\n"
        f"✅ Активна: {'Да' if data['is_active'] else 'Нет'}\n\n"
        f"Выберите параметр для изменения или нажмите 'Готово'."
    )


@router.message(Command("add_lora"))
async def start_creation(message: Message, state: FSMContext):
    if not has_admin_permission(message.from_user.id, "CEO"):
        return await message.reply("❌ У вас нет прав для выполнения этой команды.")

    await message.answer("Введите название LoRA:")
    await state.set_state(LoraCreateState.entering_name)


@router.message(LoraCreateState.entering_name)
async def set_name(message: Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(name=name, user_id=message.from_user.id, **DEFAULTS)
    await state.set_state(LoraCreateState.configuring)
    sent = await message.answer(format_config_text(await state.get_data()), reply_markup=create_menu())
    await state.update_data(last_bot_msg_id=sent.message_id)


@router.callback_query(F.data.startswith("lora_edit_"))
async def start_edit(callback: CallbackQuery, state: FSMContext):
    short_param = callback.data.replace("lora_edit_", "")
    real_param = PARAM_MAP.get(callback.data)

    if not real_param:
        await callback.answer("Неизвестный параметр.", show_alert=True)
        return

    await state.update_data(editing_param=real_param)
    await state.set_state(LoraCreateState.editing_field)

    await callback.message.delete()
    prompt_text = "Введите значение (true/false)" if real_param in ["sex", "is_active"] else "Введите новое значение:"
    prompt = await callback.message.answer(prompt_text)
    await state.update_data(prompt_msg_id=prompt.message_id)


@router.message(LoraCreateState.editing_field)
async def receive_value(message: Message, state: FSMContext):
    data = await state.get_data()
    param = data.get("editing_param")
    text = message.text.strip()

    try:
        if param in ["sex", "is_active"]:
            value = text.lower() in ["true", "1", "да"]
        elif param == "default_weight":
            value = float(text)
        else:
            if len(text) > 5000:
                raise ValueError("Промпт слишком длинный (макс. 5000 символов).")
            value = text

        await state.update_data(**{param: value})
        await state.set_state(LoraCreateState.configuring)

        try:
            await message.delete()
            prompt_id = data.get("prompt_msg_id")
            if prompt_id:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=prompt_id)
        except Exception as e:
            print(f"[WARN] Не удалось удалить сообщение: {e}")

        updated_data = await state.get_data()
        sent = await message.answer(format_config_text(updated_data), reply_markup=create_menu())
        await state.update_data(last_bot_msg_id=sent.message_id)

    except Exception as e:
        print(f"[ERROR] Ошибка при вводе значения для {param}: {e}")
        await message.answer(f"⚠ Неверный формат. Попробуйте ещё раз.\n\n<b>Ошибка:</b> {e}", parse_mode="HTML")


@router.callback_query(F.data == "cancel_lora")
async def cancel_creation(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Создание LoRA отменено.")


@router.callback_query(F.data == "done_lora")
async def create_lora(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    # Допустимые поля для записи в БД
    allowed_keys = {
        "name", "description", "lora_url", "trigger_word", "default_weight",
        "prompt_text", "preview_url", "user_id", "is_active", "sex"
    }
    db_data = {k: v for k, v in data.items() if k in allowed_keys and v not in [None, ""]}

    # ⚠ Проверка: есть ли что сохранять?
    if not db_data or "name" not in db_data or "lora_url" not in db_data or "trigger_word" not in db_data:
        await callback.message.answer("❌ Заполните хотя бы название, URL и триггер-слово перед сохранением.")
        return

    print("👉 PROMPT SAVED TO DB:", db_data.get("prompt_text"))
    print("🧾 LENGTH:", len(db_data.get("prompt_text", "")))

    lora = repo.create(db_data)

    if lora:
        await callback.message.edit_text(
            f"✅ LoRA <b>{lora['name']}</b> создана!\n"
            f"ID: {lora['lora_id']}\n"
            f"🌐 URL: {lora['lora_url']}\n"
            f"🔤 Триггер: {lora['trigger_word']}\n"
            f"⚖️ Вес: {lora['default_weight']}",
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text("❌ Ошибка при создании LoRA.")

    await state.clear()


