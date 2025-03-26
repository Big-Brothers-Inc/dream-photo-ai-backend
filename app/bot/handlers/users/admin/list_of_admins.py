from aiogram import Router, F, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from app.repository.admin import AdminRepository
from app.utils.permissions import has_admin_permission

router = Router()
repo = AdminRepository()

ACCESS_LEVELS = [
    ("BASE", "Может смотреть статусы генераций по ID"),
    ("LORA", "BASE + Может добавлять модели"),
    ("BAN", "LORA + банить/разбанивать пользователей"),
    ("HR", "BAN + может менять статус админам"),
    ("CEO", "может всё выше + делать промо коды + смотреть статку детальную с бабками")
]


@router.message(Command("list_admins"))
async def list_admins_start(message: Message):
    if not has_admin_permission(message.from_user.id, "HR"):
        return await message.reply("❌ У вас нет прав для выполнения этой команды.")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{status} - {desc[:30]}...", callback_data=f"adminlist:{status}")]
        for status, desc in ACCESS_LEVELS
    ] + [
        [InlineKeyboardButton(text="📋 Все", callback_data="adminlist:ALL")],
        [InlineKeyboardButton(text="❌ Завершить", callback_data="adminlist:CANCEL")]
    ])

    await message.answer("Выберите статус админов для отображения:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("adminlist:"))
async def handle_adminlist_selection(callback: CallbackQuery):
    action = callback.data.split(":")[1]

    if action == "CANCEL":
        await callback.message.edit_text("✅ Команда завершена.")
        return await callback.answer()

    if action == "ALL":
        admins = repo.list_admins()
        title = "📋 Все админы"
    else:
        admins = repo.list_admins(status=action)
        title = f"📋 Админы со статусом: {action}"

    if not admins:
        await callback.message.edit_text(f"{title}\n\nПока что админов нет 🙈")
        return await callback.answer()

    admin_lines = [
        f"🆔 <code>{a['user_id']}</code> | Статус: <b>{a['status']}</b> | Активен: {'✅' if a['is_active'] else '❌'}"
        for a in admins
    ]

    text = f"{title}\n\n" + "\n".join(admin_lines)
    await callback.message.edit_text(text, reply_markup=callback.message.reply_markup)
    await callback.answer()
