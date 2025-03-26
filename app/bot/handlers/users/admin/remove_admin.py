from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from app.repository.admin import AdminRepository
from app.utils.permissions import has_admin_permission
from app.config import config

router = Router()
repo = AdminRepository()


@router.message(Command("remove_admin"))
async def remove_admin_handler(message: Message):
    actor_id = message.from_user.id

    if not has_admin_permission(actor_id, "HR"):
        return await message.reply("❌ У вас нет прав для выполнения этой команды.")

    parts = message.text.strip().split()
    if len(parts) != 2:
        return await message.reply("⚠️ Использование: /remove_admin <code>admin_id</code>")

    try:
        admin_id = int(parts[1])
    except ValueError:
        return await message.reply("⚠️ admin_id должен быть числом")

    target_admin = repo.get_by_user_id(admin_id)
    if not target_admin or not target_admin["is_active"]:
        return await message.reply("⚠️ Администратор не найден или уже деактивирован")

    target_status = target_admin["status"]

    # HR не может удалять HR, CEO и суперадминов
    if target_status in ("HR", "CEO") or target_admin["user_id"] in config.ADMIN_USER_IDS:
        if not has_admin_permission(actor_id, "CEO"):
            return await message.reply("❌ Вы не можете удалить администратора с таким уровнем доступа.")

    result = repo.deactivate(admin_id)
    if result:
        return await message.reply(f"✅ Администратор <code>{admin_id}</code> деактивирован")
    else:
        return await message.reply("❌ Не удалось деактивировать администратора")
