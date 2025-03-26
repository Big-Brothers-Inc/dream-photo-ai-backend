# handlers/users/admin/give_tokens.py

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.utils.logger import logger
from app.utils.permissions import has_admin_permission
from app.repository.user import UserRepository
from app.repository.enrollment import EnrollmentRepository
from app.repository.admin import AdminRepository
from app.repository.model import ModelRepository

router = Router()


@router.message(Command("add_tokens"))
async def cmd_add_tokens(message: Message):
    """
    Добавление токенов пользователю вручную (от имени админа)
    """
    try:
        # Проверка прав администратора
        if not has_admin_permission(message.from_user.id, required_role="CEO"):
            await message.answer(
                "❌ <b>Недостаточно прав для выполнения этой команды.</b>",
                parse_mode="HTML"
            )
            return

        args = message.text.strip().split()[1:]
        if len(args) != 2:
            await message.answer(
                "❌ Используйте формат: <code>/add_tokens user_id amount</code>",
                parse_mode="HTML"
            )
            return

        try:
            user_id = int(args[0])
            amount = int(args[1])
        except ValueError:
            await message.answer(
                "❌ <b>ID пользователя</b> и <b>количество токенов</b> должны быть числами.",
                parse_mode="HTML"
            )
            return

        user_repo = UserRepository()
        enrollment_repo = EnrollmentRepository()
        admin_repo = AdminRepository()

        user = user_repo.get_by_id(user_id)
        if not user:
            await message.answer("❌ Пользователь не найден.", parse_mode="HTML")
            return

        if user_repo.increment_tokens(user_id, amount):
            enrollment_repo.create({
                "user_id": user_id,
                "amount": amount
            })

            username = user.get('username') or str(user_id)
            await message.answer(
                f"✅ <b>Пользователю {username}</b> добавлено <b>{amount}</b> токенов.",
                parse_mode="HTML"
            )

            '''
            admin = admin_repo.get_by_user_id(message.from_user.id)
            if admin:
                admin_repo.log_admin_action(
                    admin_id=admin["admin_id"],
                    action="add_tokens",
                    user_id=user_id
                )
            '''

            try:
                await message.bot.send_message(
                    user_id,
                    f"💎 <b>Пополнение баланса</b>\n\n"
                    f"На ваш счет зачислено <b>{amount} токенов</b>!\n"
                    f"💰 Текущий баланс: <b>{user['tokens_left'] + amount} токенов</b>",
                    parse_mode="HTML"
                )

                model_repo = ModelRepository()
                models = model_repo.get_models_by_user(user_id, status="ready")
                if not models:
                    builder = InlineKeyboardBuilder()
                    builder.button(text="🧠 Обучить модель", callback_data="start_training")
                    builder.button(text="❓ Как выбрать фотографии", callback_data="training_guide")

                    await message.bot.send_message(
                        user_id,
                        "🤖 <b>Создайте свою персональную модель!</b>\n\n"
                        "Мы заметили, что у вас еще нет обученной модели. "
                        "Создайте свою уникальную модель для генерации фотографий в вашем стиле!\n\n"
                        "💸 Стоимость обучения: <b>300 токенов</b>",
                        reply_markup=builder.as_markup(),
                        parse_mode="HTML"
                    )

            except Exception as e:
                logger.warning(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
        else:
            await message.answer("❌ Не удалось обновить токены пользователя.", parse_mode="HTML")

    except Exception as e:
        logger.error(f"Ошибка в хэндлере /add_tokens: {e}")
        await message.answer(f"❌ Произошла ошибка: {str(e)}", parse_mode="HTML")
