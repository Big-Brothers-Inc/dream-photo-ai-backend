from .commands import router as commands_router
from .ping import router as ping_router
from .start import router as start_router
from .help import router as help_router
from .cancel import router as cancel_router
from .balance import router as balance_router
from .webapp import router as webapp_router


def register_user_handlers(dp):
#    dp.include_router(commands_router)
    dp.include_router(ping_router)
    dp.include_router(start_router)
    dp.include_router(help_router)
    dp.include_router(cancel_router)
    dp.include_router(balance_router)
    dp.include_router(webapp_router)
