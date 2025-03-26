# bot/handlers/users/lora/__init__.py

from .add import router as add_lora_router
# from .edit_lora import router as edit_lora_router
# from .search_lora import router as search_lora_router
# from .list_loras import router as list_loras_router

lora_routers = [
    add_lora_router,
#    edit_lora_router,
#    search_lora_router,
#    list_loras_router
]


def register_lora_handlers(dp):
    for router in lora_routers:
        dp.include_router(router)
