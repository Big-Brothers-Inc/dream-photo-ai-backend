### handlers/users/admin/__init__.py
from .add_admin import router as add_admin_router
from .remove_admin import router as remove_admin_router
from .set_admin_status import router as set_admin_status_router
from .list_of_admins import router as list_of_admins
from .give_tokens import router as give_tokens

admin_routers = [
    add_admin_router,
    remove_admin_router,
    set_admin_status_router,
    list_of_admins,
    give_tokens
]


def register_admin_handlers(dp):
    for router in admin_routers:
        dp.include_router(router)