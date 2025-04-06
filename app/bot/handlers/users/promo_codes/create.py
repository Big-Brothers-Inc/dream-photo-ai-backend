from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from app.repository.promo_code import PromoCodeRepository
from app.utils.permissions import has_admin_permission

create_promo_router = Router()
repo = PromoCodeRepository()


class PromoCodeCreateState(StatesGroup):
    entering_name = State()
    configuring = State()
    editing_field = State()


PARAMETERS = ["tokens_amount", "discount_percent", "valid_to", "max_usages"]
DEFAULTS = {
    "tokens_amount": 10,
    "discount_percent": 0,
    "valid_to": datetime.utcnow(),
    "max_usages": 1,
    "is_active": True
}

PARAM_MAP = {
    "tokens": "tokens_amount",
    "discount": "discount_percent",
    "days": "valid_to",
    "max": "max_usages"
}


def create_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎟 Токены", callback_data="edit_tokens")],
        [InlineKeyboardButton(text="💸 Скидка", callback_data="edit_discount")],
        [InlineKeyboardButton(text="⏳ Срок действия", callback_data="edit_days")],
        [InlineKeyboardButton(text="♾ Макс. использований", callback_data="edit_max")],
        [
            InlineKeyboardButton(text="✅ Готово", callback_data="done"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")
        ]
    ])


def format_config_text(data):
    return (
        f"📦 Создание промо-кода:\n"
        f"🔤 Название: {data['code']}\n"
        f"🎟 Токены: {data['tokens_amount']}\n"
        f"💸 Скидка: {data['discount_percent']}%\n"
        f"⏳ Срок до: {data['valid_to'].strftime('%d.%m.%Y')}\n"
        f"♾ Макс. использований: {data['max_usages']}\n\n"
        f"Выберите параметр для изменения или нажмите 'Готово'."
    )


@create_promo_router.message(Command("create_promo"))
async def start_creation(message: Message, state: FSMContext):
    if not has_admin_permission(message.from_user.id, "CEO"):
        return await message.reply("❌ У вас нет прав для выполнения этой команды.")

    await message.answer("Введите название промо-кода:")
    await state.set_state(PromoCodeCreateState.entering_name)


@create_promo_router.message(PromoCodeCreateState.entering_name)
async def set_name(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    if repo.get_by_code(code):
        return await message.answer("⚠️ Промо-код с таким именем уже существует. Введите другое имя.")

    await state.update_data(code=code, **DEFAULTS)
    await state.set_state(PromoCodeCreateState.configuring)
    sent = await message.answer(format_config_text(await state.get_data()), reply_markup=create_menu())
    await state.update_data(last_bot_msg_id=sent.message_id)


@create_promo_router.callback_query(F.data.startswith("edit_"))
async def start_edit(callback: CallbackQuery, state: FSMContext):
    short_param = callback.data.replace("edit_", "")
    real_param = PARAM_MAP[short_param]
    await state.update_data(editing_param=real_param)
    await state.set_state(PromoCodeCreateState.editing_field)

    await callback.message.delete()
    prompt_text = (
        "Введите дату окончания в формате: дд.мм.гггг"
        if real_param == "valid_to"
        else f"Введите новое значение для: {real_param.replace('_', ' ').title()}"
    )
    prompt = await callback.message.answer(prompt_text)
    await state.update_data(prompt_msg_id=prompt.message_id)


@create_promo_router.message(PromoCodeCreateState.editing_field)
async def receive_value(message: Message, state: FSMContext):
    data = await state.get_data()
    param = data.get("editing_param")
    text = message.text.strip()

    try:
        if param == "valid_to":
            value = datetime.strptime(text, "%d.%m.%Y")
        else:
            value = int(text)

        await state.update_data(**{param: value})
        await state.set_state(PromoCodeCreateState.configuring)

        await message.delete()
        if prompt_id := data.get("prompt_msg_id"):
            await message.bot.delete_message(chat_id=message.chat.id, message_id=prompt_id)

        updated_data = await state.get_data()
        sent = await message.answer(format_config_text(updated_data), reply_markup=create_menu())
        await state.update_data(last_bot_msg_id=sent.message_id)

    except Exception:
        await message.answer("⚠ Неверный формат. Попробуйте ещё раз.")


@create_promo_router.callback_query(F.data == "cancel")
async def cancel_creation(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Создание промо-кода отменено.")


@create_promo_router.callback_query(F.data == "done")
async def create_promo(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    promo = repo.create({
        "code": data["code"],
        "tokens_amount": data["tokens_amount"],
        "discount_percent": data["discount_percent"],
        "valid_from": datetime.utcnow(),
        "valid_to": data["valid_to"],
        "max_usages": data["max_usages"],
        "created_by": callback.from_user.id,
        "is_active": True
    })

    if promo:
        await callback.message.edit_text(
            f"✅ Промо-код <b>{promo['code']}</b> создан!\n"
            f"ID: {promo['promo_id']}\n"
            f"🎟 Токены: {promo['tokens_amount']}\n"
            f"💸 Скидка: {promo['discount_percent']}%\n"
            f"📅 Срок: {promo['valid_from']} — {promo['valid_to']}\n"
            f"♾ Макс. использований: {promo['max_usages']}",
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text("❌ Ошибка при создании промо-кода.")

    await state.clear()
