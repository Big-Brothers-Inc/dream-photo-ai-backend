# app/utils/set_bot_commands.py

from aiogram import Bot
from aiogram.types import BotCommand


async def set_default_commands(bot: Bot) -> None:
    await bot.set_my_commands([
        BotCommand(command="start", description="🚀 Запуск / Перезапуск бота"),
        BotCommand(command="help", description="📖 Помощь по командам"),
        BotCommand(command="webapp", description="🌐 Открыть веб-приложение"),
        BotCommand(command="cancel", description="❌ Отменить текущее действие"),

    ])
