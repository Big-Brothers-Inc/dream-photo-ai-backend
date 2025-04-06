from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from app.repository.lora import LoraRepository
from app.repository.lora_tag import LoraTagRepository
from app.repository.lora_tag_relation import LoraTagRelationRepository
from app.utils.permissions import has_admin_permission

lora_edit_router = Router()
repo = LoraRepository()
tag_repo = LoraTagRepository()
relation_repo = LoraTagRelationRepository()


class LoraEditState(StatesGroup):
    selecting_lora = State()
    configuring = State()
    editing_field = State()
    editing_tags = State()



PARAMETERS = ["description", "lora_url", "trigger_word", "default_weight", "prompt_text", "preview_url", "sex", "is_active"]

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
        [InlineKeyboardButton(text="🏷 Изменить теги", callback_data="lora_tags_edit")],
        [
            InlineKeyboardButton(text="✅ Готово", callback_data="done_edit_lora"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_edit_lora")
        ]
    ])


def format_config_text(data):
    def truncate(text, max_len=500):
        if not text:
            return "—"
        return text if len(text) <= max_len else text[:max_len] + "..."

    tag_repo = LoraTagRepository()
    tags = data.get("selected_tags", [])
    tag_names = []

    for tag_id in tags:
        tag = tag_repo.get_by_id(tag_id)
        if tag:
            tag_names.append(tag["name"])

    tags_text = ", ".join(tag_names) if tag_names else "(нет)"

    return (
        f"✏️ Редактирование LoRA:\n"
        f"🔤 Название: {data['name']}\n"
        f"📝 Описание: {data['description']}\n"
        f"🌐 URL: {data['lora_url']}\n"
        f"🔤 Триггер: {data['trigger_word']}\n"
        f"⚖️ Вес: {data['default_weight']}\n"
        f"🧠 Промпт: {truncate(data.get('prompt_text'))}\n"
        f"🖼 Превью: {data['preview_url']}\n"
        f"🚻 Пол: {'Мужской' if data['sex'] else 'Женский'}\n"
        f"✅ Активна: {'Да' if data['is_active'] else 'Нет'}\n"
        f"🏷 Теги: {tags_text}\n\n"
        f"Выберите параметр для изменения или нажмите 'Готово'."
    )


@lora_edit_router.message(Command("edit_lora"))
async def start_editing(message: Message, state: FSMContext):
    if not has_admin_permission(message.from_user.id, "CEO"):
        return await message.reply("❌ У вас нет прав для выполнения этой команды.")

    # Получение всех активных LoRA
    loras = repo.get_all()
    if not loras:
        await message.answer("❌ Нет доступных LoRA для редактирования.")
        return

    # Формируем список всех моделей для вывода
    lora_list = "\n".join(
        [f"🔹 <b>{i + 1}. {l['name']}</b> (ID: <code>{l['lora_id']}</code>)" for i, l in enumerate(loras[:50])])

    sent_msg = await message.answer(
        f"📝 Введите ID LoRA для редактирования:\n\n{lora_list}",
        parse_mode="HTML"
    )

    await state.update_data(list_msg_id=sent_msg.message_id)
    await state.set_state(LoraEditState.selecting_lora)


@lora_edit_router.message(LoraEditState.selecting_lora)
async def load_lora(message: Message, state: FSMContext):
    lora_id = message.text.strip()
    data = await state.get_data()

    if not lora_id.isdigit():
        await message.answer("❌ Неверный формат ID. Введите числовое значение.")
        return

    lora = repo.get_by_id(int(lora_id))
    if not lora:
        await message.answer(f"❌ LoRA с ID {lora_id} не найдена.")
        return

    # Удаляем сообщение с ID и список моделей
    try:
        await message.delete()
        if "list_msg_id" in data:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=data["list_msg_id"])
    except Exception as e:
        print(f"[WARN] Не удалось удалить сообщение: {e}")

    lora_id_int = int(lora_id)

    # Загружаем теги из таблицы связей
    related_tags = relation_repo.get_tags_for_lora(lora_id_int)
    tag_ids = [tag["tag_id"] for tag in related_tags]

    # Убираем lora_id из словаря, чтобы не конфликтовать
    lora.pop("lora_id", None)

    await state.update_data(lora_id=lora_id_int, selected_tags=tag_ids, **lora)
    await state.set_state(LoraEditState.configuring)

    sent = await message.answer(format_config_text(await state.get_data()), reply_markup=create_menu())
    await state.update_data(last_bot_msg_id=sent.message_id)


@lora_edit_router.callback_query(F.data.startswith("lora_edit_"))
async def start_edit(callback: CallbackQuery, state: FSMContext):
    short_param = callback.data.replace("lora_edit_", "")
    real_param = PARAM_MAP.get(callback.data)

    if not real_param:
        await callback.answer("Неизвестный параметр.", show_alert=True)
        return

    await state.update_data(editing_param=real_param)
    await state.set_state(LoraEditState.editing_field)

    await callback.message.delete()
    prompt_text = "Введите значение (true/false)" if real_param in ["sex", "is_active"] else "Введите новое значение:"
    prompt = await callback.message.answer(prompt_text)
    await state.update_data(prompt_msg_id=prompt.message_id)


@lora_edit_router.message(LoraEditState.editing_field)
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
        await state.set_state(LoraEditState.configuring)

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


@lora_edit_router.callback_query(F.data == "cancel_edit_lora")
async def cancel_edit(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Редактирование LoRA отменено.")


@lora_edit_router.callback_query(F.data == "done_edit_lora")
async def save_lora(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lora_id = data.get("lora_id")

    # Поля, которые сохраняем в таблицу lora
    allowed_keys = {
        "description", "lora_url", "trigger_word", "default_weight",
        "prompt_text", "preview_url", "is_active", "sex"
    }
    db_data = {k: v for k, v in data.items() if k in allowed_keys and v is not None}

    # Обновляем модель
    lora = repo.update(lora_id, db_data)

    # 🔧 Получаем теги из selected_tags, а не tags
    tags = data.get("selected_tags", [])

    # Обновляем связи в таблице
    relation_repo.delete_all_for_lora(lora_id)
    for tag_id in tags:
        relation_repo.create({"lora_id": lora_id, "tag_id": tag_id})

    # Получаем названия тегов
    tag_names = []
    for tag_id in tags:
        tag = tag_repo.get_by_id(tag_id)
        if tag:
            tag_names.append(tag["name"])

    if lora:
        tags_text = ", ".join(tag_names) if tag_names else "(нет)"
        await callback.message.edit_text(
            f"✅ LoRA <b>{lora['name']}</b> успешно обновлена!\n"
            f"🏷 Теги: {tags_text}",
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text("❌ Ошибка при обновлении LoRA.")

    await state.clear()


@lora_edit_router.callback_query(F.data == "lora_tags_edit")
async def edit_tags(callback: CallbackQuery, state: FSMContext):
    tags = tag_repo.get_all()
    data = await state.get_data()
    selected = data.get("selected_tags", [])

    buttons = []
    for tag in tags:
        is_selected = tag["tag_id"] in selected
        buttons.append([
            InlineKeyboardButton(text=tag["name"], callback_data="noop"),
            InlineKeyboardButton(text="✅" if is_selected else "➕", callback_data=f"lora_tag_add_{tag['tag_id']}"),
            InlineKeyboardButton(text="❌", callback_data=f"lora_tag_remove_{tag['tag_id']}")
        ])

    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="lora_back_to_main")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text("🏷 Добавить или удалить теги:", reply_markup=keyboard)
    await state.set_state(LoraEditState.editing_tags)


@lora_edit_router.callback_query(F.data.startswith("lora_tag_add_"))
async def tag_add(callback: CallbackQuery, state: FSMContext):
    tag_id = int(callback.data.split("_")[-1])
    data = await state.get_data()
    selected = set(data.get("selected_tags", []))
    selected.add(tag_id)
    await state.update_data(selected_tags=list(selected))
    await edit_tags(callback, state)


@lora_edit_router.callback_query(F.data.startswith("lora_tag_remove_"))
async def tag_remove(callback: CallbackQuery, state: FSMContext):
    tag_id = int(callback.data.split("_")[-1])
    data = await state.get_data()
    selected = set(data.get("selected_tags", []))
    selected.discard(tag_id)
    await state.update_data(selected_tags=list(selected))
    await edit_tags(callback, state)


@lora_edit_router.callback_query(F.data == "lora_back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(LoraEditState.configuring)
    await callback.message.edit_text(format_config_text(data), reply_markup=create_menu())
