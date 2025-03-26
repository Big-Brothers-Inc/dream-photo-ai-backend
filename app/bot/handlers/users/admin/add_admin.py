from aiogram import Router, F, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.repository.admin import AdminRepository
from app.utils.permissions import has_admin_permission

router = Router()
repo = AdminRepository()


class AdminAddState(StatesGroup):
    selecting_access = State()


ACCESS_LEVELS = [
    ("BASE", "Может смотреть статусы генераций по ID"),
    ("LORA", "BASE + Может добавлять модели"),
    ("BAN", "LORA + банить/разбанивать пользователей"),
    ("HR", "BAN + может менять статус админам"),
    ("CEO", "может всё выше + делать промо коды + смотреть статку детальную с бабками")
]


@router.message(Command("add_admin"))
async def add_admin_handler(message: Message, state: FSMContext):
    # Только HR и выше могут добавить админа
    if not has_admin_permission(message.from_user.id, "HR"):
        return await message.reply("❌ У вас нет прав для выполнения этой команды.")

    parts = message.text.strip().split()
    if len(parts) != 2:
        return await message.reply("⚠️ Использование: /add_admin <code>user_id</code>")

    try:
        user_id = int(parts[1])
    except ValueError:
        return await message.reply("⚠️ user_id должен быть числом")

    existing_admin = repo.get_by_user_id(user_id)
    if existing_admin:
        if existing_admin["is_active"]:
            return await message.reply("⚠️ Этот пользователь уже является администратором. Используйте /set_admin_status для изменения.")
        else:
            repo.activate(existing_admin["admin_id"])

    await state.set_state(AdminAddState.selecting_access)
    await state.update_data(user_id=user_id, access_level=None, actor_id=message.from_user.id)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{level} - {desc}", callback_data=f"set_access:{level}")]
        for level, desc in ACCESS_LEVELS
    ] + [[
        InlineKeyboardButton(text="✅ Готово", callback_data="access_done"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="access_cancel")
    ]])

    await message.answer(
        f"👤 Добавление администратора User ID: <code>{user_id}</code>\nУровень доступа: <i>не выбран</i>",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("set_access:"), AdminAddState.selecting_access)
async def set_access_level(call: CallbackQuery, state: FSMContext):
    level = call.data.split(":")[1]
    data = await state.get_data()
    user_id = data["user_id"]
    actor_id = data["actor_id"]

    # HR и выше могут назначать BASE, LORA, BAN
    # Только CEO и ADMIN_USER_IDS могут назначать HR и CEO
    if level in ["HR", "CEO"] and not has_admin_permission(actor_id, "CEO"):
        await call.answer("❌ Только CEO может назначать HR и выше", show_alert=True)
        return

    await state.update_data(access_level=level)

    await call.message.edit_text(
        f"👤 Добавление администратора User ID: <code>{user_id}</code>\nУровень доступа: <b>{level}</b>",
        reply_markup=call.message.reply_markup
    )
    await call.answer()


@router.callback_query(F.data == "access_done", AdminAddState.selecting_access)
async def finalize_admin_creation(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data["user_id"]
    access_level = data.get("access_level")
    actor_id = data["actor_id"]

    if not access_level:
        await call.message.edit_text(
            f"👤 Добавление администратора User ID: <code>{user_id}</code>\n<b>Добавьте уровень доступа или отмените действие</b>",
            reply_markup=call.message.reply_markup
        )
        await call.answer()
        return

    # Повторная проверка при финализации
    if access_level in ["HR", "CEO"] and not has_admin_permission(actor_id, "CEO"):
        await call.answer("❌ Только CEO может назначать HR и выше", show_alert=True)
        return

    admin_record = repo.get_by_user_id(user_id)
    if admin_record:
        repo.update_status(admin_id=admin_record["admin_id"], new_status=access_level)
    else:
        repo.create(user_id=user_id, status=access_level)

    await call.message.edit_text(
        f"✅ Администратор <code>{user_id}</code> назначен со статусом <b>{access_level}</b>"
    )
    await state.clear()
    await call.answer()


@router.callback_query(F.data == "access_cancel", AdminAddState.selecting_access)
async def cancel_admin_creation(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data["user_id"]

    await call.message.edit_text(f"🚫 Админ <code>{user_id}</code> не добавлен")
    await state.clear()
    await call.answer()
