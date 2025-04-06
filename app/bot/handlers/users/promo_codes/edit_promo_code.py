from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from app.repository.promo_code import PromoCodeRepository
from app.utils.permissions import has_admin_permission

edit_promo_router = Router()
repo = PromoCodeRepository()


class PromoCodeEditState(StatesGroup):
    entering_code = State()
    configuring = State()
    editing_field = State()


PARAM_MAP = {
    "tokens": "tokens_amount",
    "discount": "discount_percent",
    "days": "valid_to",
    "max": "max_usages"
}


def edit_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎟 Токены", callback_data="promo_edit_tokens")],
        [InlineKeyboardButton(text="💸 Скидка", callback_data="promo_edit_discount")],
        [InlineKeyboardButton(text="⏳ Срок действия", callback_data="promo_edit_days")],
        [InlineKeyboardButton(text="♾ Макс. использований", callback_data="promo_edit_max")],
        [InlineKeyboardButton(text="✅ Сохранить", callback_data="promo_save_edit")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="promo_cancel_edit")]
    ])


def format_edit_text(promo):
    return (
        f"✏ Редактирование промо-кода <b>{promo['code']}</b>\n"
        f"🎟 Токены: {promo.get('tokens_amount', '—')}\n"
        f"💸 Скидка: {promo.get('discount_percent', '—')}%\n"
        f"⏳ Срок до: {promo.get('valid_to').strftime('%d.%m.%Y') if promo.get('valid_to') else '—'}\n"
        f"♾ Макс. использований: {promo.get('max_usages', '—')}\n\n"
        f"Выберите параметр для изменения."
    )


@edit_promo_router.message(Command("edit_promo"))
async def ask_promo_code(message: Message, state: FSMContext):
    if not has_admin_permission(message.from_user.id, "CEO"):
        return await message.answer("❌ Недостаточно прав.")

    await state.set_state(PromoCodeEditState.entering_code)
    await message.answer("Введите название промо-кода, который хотите отредактировать:")


@edit_promo_router.message(PromoCodeEditState.entering_code)
async def receive_code(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    promo = repo.get_by_code(code)
    if not promo:
        return await message.answer("⚠️ Промо-код не найден. Попробуйте ещё раз.")

    await state.set_state(PromoCodeEditState.configuring)
    await state.update_data(**promo)

    sent = await message.answer(
        format_edit_text(promo), reply_markup=edit_menu_keyboard(), parse_mode="HTML"
    )
    await state.update_data(last_bot_msg_id=sent.message_id)


@edit_promo_router.callback_query(F.data.startswith("promo_edit_"))
async def begin_edit(callback: CallbackQuery, state: FSMContext):
    short_param = callback.data.replace("promo_edit_", "")
    real_param = PARAM_MAP.get(short_param)

    await state.update_data(editing_param=real_param)
    await state.set_state(PromoCodeEditState.editing_field)

    # удаляем старое сообщение с меню
    await callback.message.delete()

    text = (
        "Введите дату окончания в формате: дд.мм.гггг"
        if real_param == "valid_to"
        else f"Введите новое значение для: {real_param.replace('_', ' ').title()}"
    )
    prompt = await callback.message.answer(text)
    await state.update_data(prompt_msg_id=prompt.message_id)


@edit_promo_router.message(PromoCodeEditState.editing_field)
async def receive_new_value(message: Message, state: FSMContext):
    data = await state.get_data()
    param = data.get("editing_param")
    value_text = message.text.strip()

    try:
        if param == "valid_to":
            value = datetime.strptime(value_text, "%d.%m.%Y")
        else:
            value = int(value_text)

        await state.update_data(**{param: value})
        await state.set_state(PromoCodeEditState.configuring)

        updated = await state.get_data()

        # удаляем ввод пользователя и сообщение с инструкцией
        await message.delete()
        if prompt_id := updated.get("prompt_msg_id"):
            await message.bot.delete_message(chat_id=message.chat.id, message_id=prompt_id)

        sent = await message.answer(
            format_edit_text(updated), reply_markup=edit_menu_keyboard(), parse_mode="HTML"
        )
        await state.update_data(last_bot_msg_id=sent.message_id)

    except Exception:
        await message.answer("⚠ Неверный формат. Попробуйте ещё раз.")


@edit_promo_router.callback_query(F.data == "promo_cancel_edit")
async def cancel_editing(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Редактирование промо-кода отменено.")


@edit_promo_router.callback_query(F.data == "promo_save_edit")
async def save_edit(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    updated = repo.update(data["promo_id"], {
        "tokens_amount": data.get("tokens_amount"),
        "discount_percent": data.get("discount_percent"),
        "max_usages": data.get("max_usages"),
        "valid_to": data.get("valid_to")
    })
    if updated:
        await callback.message.edit_text("✅ Промо-код обновлён")
    else:
        await callback.message.edit_text("❌ Ошибка при обновлении промо-кода")
    await state.clear()
