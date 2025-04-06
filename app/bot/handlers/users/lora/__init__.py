# bot/handlers/users/lora/__init__.py

from .add import lora_add_router as add_lora_router
from .edit import lora_edit_router as edit_lora_router
from .lora_tag import lora_tag_router as lora_tag_router
# from .search_lora import router as search_lora_router
# from .list_loras import router as list_loras_router

lora_routers = [
    add_lora_router,
    edit_lora_router,
    lora_tag_router
#    search_lora_router,
#    list_loras_router
]


def register_lora_handlers(dp):
    for router in lora_routers:
        dp.include_router(router)
