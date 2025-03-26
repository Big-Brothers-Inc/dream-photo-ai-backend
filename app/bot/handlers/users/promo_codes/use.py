from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from app.repository.user import UserRepository
from app.repository.promo_code import PromoCodeRepository
from app.repository.promo_usage import PromoUsageRepository
from app.repository.enrollment import EnrollmentRepository

router = Router()


@router.message(F.text.regexp(r"^/promo\s+(\w+)$"))
async def apply_promo(message: types.Message, state: FSMContext):
    promo_code_input = message.text.split(maxsplit=1)[1].strip()
    user_id = message.from_user.id

    promo_repo = PromoCodeRepository()
    usage_repo = PromoUsageRepository()
    user_repo = UserRepository()
    enrollment_repo = EnrollmentRepository()

    # Получаем промокод
    promo = promo_repo.get_by_code(promo_code_input)
    if not promo:
        await message.answer("❌ Промокод не существует")
        return

    if not promo_repo.is_valid_for_use(promo["promo_id"]):
        await message.answer("❌ Промокод больше не действителен")
        return

    if usage_repo.has_user_used_promo(user_id, promo["promo_id"]):
        await message.answer("❌ Промокод больше не действителен")
        return

    tokens = promo["tokens_amount"]

    # Шаг 1: записываем promo_usage
    usage = usage_repo.create({
        "promo_id": promo["promo_id"],
        "user_id": user_id,
        "payment_id": None
    })

    if not usage:
        await message.answer("❌ Не удалось применить промокод. Повторите позже.")
        return

    # Шаг 2: обновляем баланс пользователя
    updated = user_repo.increment_tokens(user_id=user_id, tokens=tokens)
    if not updated:
        await message.answer("❌ Ошибка при обновлении баланса.")
        return

    # Шаг 3: создаём запись о зачислении
    enrollment = enrollment_repo.create_with_promo(
        user_id=user_id,
        promo_id=promo["promo_id"],
        amount=tokens
    )

    if not enrollment:
        await message.answer("⚠️ Баланс обновлён, но зачисление не зафиксировано.")
        return

    # Итог: успешный результат
    user = user_repo.get_by_id(user_id)
    balance = user["tokens_left"]

    await message.answer(
        f"✅ <b>Промокод активирован!</b>\n"
        f"🎁 Начислено <b>{tokens}</b> токенов.\n"
        f"💰 Ваш текущий баланс: <b>{balance}</b>",
        parse_mode="HTML"
    )
