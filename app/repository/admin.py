from typing import Dict, Optional, Any, List
import logging
from app.repository.db import BaseRepository

logger = logging.getLogger(__name__)


class AdminRepository(BaseRepository):
    """
    Репозиторий для работы с таблицей администраторов
    """

    def get_by_id(self, admin_id: int) -> Optional[Dict[str, Any]]:
        query = 'SELECT * FROM "admin" WHERE admin_id = %(admin_id)s'
        return self.execute_query_single(query, {"admin_id": admin_id})

    def get_by_user_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        query = 'SELECT * FROM "admin" WHERE user_id = %(user_id)s'
        return self.execute_query_single(query, {"user_id": user_id})

    def create(self, user_id: int, status: str = 'BASE') -> Optional[Dict[str, Any]]:
        query = '''
        INSERT INTO "admin" (user_id, status)
        VALUES (%(user_id)s, %(status)s)
        RETURNING *
        '''
        return self.execute_with_returning(query, {
            "user_id": user_id,
            "status": status
        })

    def update_status(self, admin_id: int, new_status: str) -> Optional[Dict[str, Any]]:
        """
        Обновление статуса администратора

        Args:
            admin_id: ID администратора
            new_status: Новый статус

        Returns:
            Обновлённые данные администратора
        """
        query = '''
        UPDATE "admin"
        SET status = %(status)s
        WHERE admin_id = %(admin_id)s
        RETURNING *
        '''
        return self.execute_with_returning(query, {
            "admin_id": admin_id,
            "status": new_status
        })

    def deactivate(self, admin_id: int) -> Optional[Dict[str, Any]]:
        """
        Деактивация администратора (is_active = FALSE)

        Args:
            admin_id: ID администратора

        Returns:
            Обновлённые данные администратора
        """
        query = '''
        UPDATE "admin"
        SET is_active = FALSE
        WHERE admin_id = %(admin_id)s
        RETURNING *
        '''
        return self.execute_with_returning(query, {"admin_id": admin_id})

    def activate(self, admin_id: int) -> Optional[Dict[str, Any]]:
        """
        Активация администратора (is_active = TRUE)

        Args:
            admin_id: ID администратора

        Returns:
            Обновлённые данные администратора
        """
        query = '''
        UPDATE "admin"
        SET is_active = TRUE
        WHERE admin_id = %(admin_id)s
        RETURNING *
        '''
        return self.execute_with_returning(query, {"admin_id": admin_id})

    def list_admins(self, status: Optional[str] = None, active_only: bool = False) -> List[Dict[str, Any]]:
        """
        Получение списка администраторов с фильтрацией по статусу и активности

        Args:
            status: Статус (опционально)
            active_only: Только активные админы

        Returns:
            Список администраторов
        """
        conditions = []
        params: Dict[str, Any] = {}

        if status:
            conditions.append("status = %(status)s")
            params["status"] = status

        if active_only:
            conditions.append("is_active = TRUE")

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f'SELECT * FROM "admin" {where_clause} ORDER BY admin_id'

        return self.execute_query(query, params)

    # Заглушки для соблюдения интерфейса BaseRepository
    def update(self, id_value: Any, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        logger.warning("Метод update не используется для AdminRepository")
        return None

    def delete(self, id_value: Any) -> bool:
        logger.warning("Метод delete не используется для AdminRepository — используйте deactivate()")
        return False
