from aiogram import Router, types
from aiogram.filters import Command
from aiogram.utils.markdown import hbold

router = Router()


@router.message(Command("help"))
async def command_help(message: types.Message):
    await message.answer(
        f"📚 {hbold('Доступные команды:')}\n\n"
        f"/start — Начать работу\n"
        f"/help — Помощь\n"
        f"/webapp — Открыть веб-приложение\n"
        f"/train — Обучить модель\n"
        f"/generate — Генерация изображений\n"
        f"/models — Мои модели\n"
        f"/settings — Настройки\n"
        f"/cancel — Отмена текущего действия. Очень сомнительный функционал. Надо понять, зачем это и поменять"
    )
