from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandObject, Command
from app.repository.promo_code import PromoCodeRepository
from app.utils.permissions import has_admin_permission

router = Router()
repo = PromoCodeRepository()


@router.message(Command("list_promos"))
async def list_all_promos(message: Message, command: CommandObject):
    if not has_admin_permission(message.from_user.id, "CEO"):
        return await message.answer("❌ У вас нет прав для выполнения этой команды.")

    arg = command.args.strip().lower() if command.args else None
    is_active = None
    if arg == "active":
        is_active = True

    promos = repo.list_all(is_active=is_active)
    if not promos:
        return await message.answer("🔍 Промо-коды не найдены.")

    lines = []
    for promo in promos:
        status = "🟢 Активен" if promo["is_active"] else "🔴 Неактивен"
        lines.append(
            f"\n<b>{promo['code']}</b> | ID: {promo['promo_id']}\n"
            f"🎟 Токены: {promo['tokens_amount']}, 💸 Скидка: {promo['discount_percent']}%\n"
            f"📅 {promo['valid_from']} — {promo['valid_to']} | ♾ Использований: {promo['max_usages']}\n"
            f"{status}"
        )

    await message.answer("\n".join(lines))
