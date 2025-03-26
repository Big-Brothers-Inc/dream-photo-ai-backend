from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandObject, Command
from app.repository.promo_code import PromoCodeRepository
from app.utils.permissions import has_admin_permission

router = Router()
repo = PromoCodeRepository()


@router.message(Command("activate_promo"))
async def activate_promo(message: Message, command: CommandObject):
    if not has_admin_permission(message.from_user.id, "CEO"):
        return await message.reply("❌ У вас нет прав для выполнения этой команды.")

    code = command.args.strip().upper() if command.args else None
    if not code:
        return await message.reply("⚠️ Используйте команду в формате: /activate_promo <code>promo_code</code>")

    promo = repo.get_by_code(code)
    if not promo:
        return await message.reply(f"❌ Промо-код <code>{code}</code> не найден.", parse_mode="HTML")

    if promo["is_active"]:
        return await message.reply(f"🔄 Промо-код <code>{code}</code> уже активен.", parse_mode="HTML")

    updated = repo.update(promo["promo_id"], {"is_active": True})
    if updated:
        await message.reply(f"✅ Промо-код <code>{code}</code> успешно активирован.", parse_mode="HTML")
    else:
        await message.reply("❌ Не удалось активировать промо-код.")
