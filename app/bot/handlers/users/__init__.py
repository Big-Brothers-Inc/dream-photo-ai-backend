
from .admin import register_admin_handlers
from .promo_codes import register_promo_code_handlers
from .user_commands import register_user_commands_handlers
from .lora import register_lora_handlers


def register_user_handlers(dp):
    register_user_commands_handlers(dp)
    register_admin_handlers(dp)
    register_promo_code_handlers(dp)
    register_lora_handlers(dp)
