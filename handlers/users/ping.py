from aiogram import Router, types
from aiogram.filters import Command

router = Router()


@router.message(Command("ping"))
async def ping_handler(message: types.Message):
    await message.answer("Pong! 🏓")
