from .commands import router as commands_router
from .ping import router as ping_router


def register_user_handlers(dp):
    dp.include_router(commands_router)
    dp.include_router(ping_router)
