from app.bot.handlers.users.user_commands.ping import router as ping_router
from app.bot.handlers.users.user_commands.start import router as start_router
from app.bot.handlers.users.user_commands.help import router as help_router
from app.bot.handlers.users.user_commands.cancel import router as cancel_router
from app.bot.handlers.users.user_commands.balance import router as balance_router
from app.bot.handlers.users.user_commands.webapp import router as webapp_router

user_commands_routers = [
    ping_router,
    start_router,
    help_router,
    cancel_router,
    balance_router,
    webapp_router
]


def register_user_commands_handlers(dp):
    for router in user_commands_routers:
        dp.include_router(router)