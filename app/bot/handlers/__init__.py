from .users import register_user_handlers


def register_all_handlers(dp):
    register_user_handlers(dp)
