from aiogram import Router, F, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.repository.admin import AdminRepository
from app.utils.permissions import has_admin_permission
from app.config import config

router = Router()
repo = AdminRepository()


class AdminStatusState(StatesGroup):
    selecting_status = State()


ACCESS_LEVELS = [
    ("BASE", "Может смотреть статусы генераций по ID"),
    ("LORA", "BASE + Может добавлять модели"),
    ("BAN", "LORA + банить/разбанивать пользователей"),
    ("HR", "BAN + может менять статус админам"),
    ("CEO", "может всё выше + делать промо коды + смотреть статку детальную с бабками")
]


@router.message(Command("set_admin_status"))
async def set_admin_status_handler(message: Message, state: FSMContext):
    actor_id = message.from_user.id

    if not has_admin_permission(actor_id, "HR"):
        return await message.reply("❌ У вас нет прав для выполнения этой команды.")

    parts = message.text.strip().split()
    if len(parts) != 2:
        return await message.reply("⚠️ Использование: /set_admin_status <code>admin_id</code>")

    try:
        admin_id = int(parts[1])
    except ValueError:
        return await message.reply("⚠️ admin_id должен быть числом")

    target_admin = repo.get_by_user_id(admin_id)
    if not target_admin or not target_admin["is_active"]:
        return await message.reply("⚠️ Администратор не найден или деактивирован")

    # HR не может менять статус HR, CEO и суперадминов
    if target_admin["status"] in ("HR", "CEO") or target_admin["user_id"] in config.ADMIN_USER_IDS:
        if not has_admin_permission(actor_id, "CEO"):
            return await message.reply("❌ Вы не можете изменить статус этого администратора.")

    await state.set_state(AdminStatusState.selecting_status)
    await state.update_data(admin_id=admin_id)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{level} - {desc}", callback_data=f"status:{level}")]
        for level, desc in ACCESS_LEVELS
    ] + [[
        InlineKeyboardButton(text="✅ Готово", callback_data="status_done"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="status_cancel")
    ]])

    await message.answer(
        f"🛠 Изменение статуса администратора <code>{admin_id}</code>\nВыберите новый статус:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("status:"), AdminStatusState.selecting_status)
async def select_new_status(call: CallbackQuery, state: FSMContext):
    status = call.data.split(":")[1]
    await state.update_data(new_status=status)

    data = await state.get_data()
    admin = repo.get_by_user_id(data["admin_id"])
    admin_id = admin["user_id"]

    await call.message.edit_text(
        f"🛠 Изменение статуса администратора <code>{admin_id}</code>\nНовый статус: <b>{status}</b>",
        reply_markup=call.message.reply_markup
    )
    await call.answer()


@router.callback_query(F.data == "status_done", AdminStatusState.selecting_status)
async def finalize_status_update(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    admin = repo.get_by_user_id(data["admin_id"])
    admin_id = admin["user_id"]
    new_status = data.get("new_status")

    if not new_status:
        await call.answer("⚠️ Выберите статус перед подтверждением.", show_alert=True)
        return

    result = repo.update_status(admin["admin_id"], new_status)
    if result:
        await call.message.edit_text(
            f"✅ Статус администратора <code>{admin_id}</code> обновлён до <b>{new_status}</b>"
        )
    else:
        await call.message.edit_text("❌ Не удалось обновить статус администратора")

    await state.clear()
    await call.answer()


@router.callback_query(F.data == "status_cancel", AdminStatusState.selecting_status)
async def cancel_status_update(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    admin = repo.get_by_user_id(data["admin_id"])
    admin_id = admin["user_id"]

    await call.message.edit_text(f"🚫 Изменение статуса администратора <code>{admin_id}</code> отменено")
    await state.clear()
    await call.answer()
