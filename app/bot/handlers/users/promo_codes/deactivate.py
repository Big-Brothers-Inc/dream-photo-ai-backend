from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from app.repository.promo_code import PromoCodeRepository
from app.utils.permissions import has_admin_permission

router = Router()
repo = PromoCodeRepository()


@router.message(Command("deactivate_promo"))
async def deactivate_promo(message: Message):
    if not has_admin_permission(message.from_user.id, "CEO"):
        return await message.reply("❌ У вас нет прав для выполнения этой команды.")

    parts = message.text.strip().split()
    if len(parts) != 2:
        return await message.reply("⚠️ Используйте команду в формате: /deactivate_promo <code>promo_code</code>")

    code = parts[1].strip().upper()
    promo = repo.get_by_code(code)
    if not promo:
        return await message.reply("❌ Промо-код с таким названием не найден.")

    if not promo.get("is_active", True):
        return await message.reply("⚠️ Этот промо-код уже деактивирован.")

    deactivated = repo.delete(promo["promo_id"])
    if deactivated:
        await message.reply(f"✅ Промо-код <b>{promo['code']}</b> деактивирован.", parse_mode="HTML")
    else:
        await message.reply("❌ Не удалось деактивировать промо-код.")