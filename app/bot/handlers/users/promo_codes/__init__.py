from .create import create_promo_router as create_promo_router
from .deactivate import deacrivate_promo_router as deactivate_promo_router
from .list_promos import list_promos_router as list_promos_promos_router
from .edit_promo_code import edit_promo_router as edit_promo_router
from .activate import activate_promo_router as activate_promo_router
from .use import promo_router as use_promo_router
# from .rename import router as rename_promo_router
# from .search import router as search_promo_router
# from .by_admin import router as by_admin_router

promo_code_routers = [
    create_promo_router,
    deactivate_promo_router,
    list_promos_promos_router,
    edit_promo_router,
    activate_promo_router,
    use_promo_router
]


def register_promo_code_handlers(dp):
    for router in promo_code_routers:
        dp.include_router(router)
