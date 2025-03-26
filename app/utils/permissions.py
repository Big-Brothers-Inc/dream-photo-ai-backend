from app.repository.admin import AdminRepository
from app.config import config

# Иерархия ролей
ROLE_HIERARCHY = {
    "BASE": 0,
    "LORA": 1,
    "BAN": 2,
    "HR": 3,
    "CEO": 4
}

# ("BASE", "Может смотреть статусы генераций по ID"),
# ("LORA", "BASE + Может добавлять модели"),
# ("BAN", "LORA + банить/разбанивать пользователей"),
# ("HR", "BAN + может менять статус админам"),
# ("CEO", "может всё выше + делать промо коды + смотреть статку детальную с бабками")


def is_authorized_admin(user_id: int) -> bool:
    """
    Проверка, является ли пользователь админом с правами CEO или входит в список супер-админов.
    """
    repo = AdminRepository()
    admin = repo.get_by_user_id(user_id)
    if not admin:
        return False

    return admin["status"] == "CEO" or user_id in config.ADMIN_USER_IDS


def has_admin_permission(user_id: int, required_role: str) -> bool:
    """
    Проверка, имеет ли админ право выполнять действие, требующее определённый статус (или выше).

    Args:
        user_id: ID пользователя
        required_role: минимальный требуемый статус (например, "HR")

    Returns:
        True, если у пользователя есть необходимый статус или выше
    """
    repo = AdminRepository()
    admin = repo.get_by_user_id(user_id)

    # Суперадмины всегда имеют все права
    if user_id in config.ADMIN_USER_IDS:
        return True

    if not admin or not admin.get("is_active", True):
        return False

    user_status = admin.get("status")
    if user_status not in ROLE_HIERARCHY:
        return False


    return ROLE_HIERARCHY.get(user_status, -1) >= ROLE_HIERARCHY.get(required_role, 99)
