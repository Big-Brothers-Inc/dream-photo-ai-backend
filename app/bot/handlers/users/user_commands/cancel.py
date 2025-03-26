from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

router = Router()


@router.message(Command("cancel"))
async def command_cancel(message: types.Message, state: FSMContext):
    if await state.get_state() is None:
        await message.answer("🤷‍♂️ Нет активных действий для отмены.")
        return
    await state.clear()
    await message.answer("🔄 Действие отменено. Используйте /help для справки.")
