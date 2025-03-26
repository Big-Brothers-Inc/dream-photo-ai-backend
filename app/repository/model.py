from typing import Dict, List, Optional, Any
from app.repository.db import BaseRepository
import logging

logger = logging.getLogger(__name__)


class ModelRepository(BaseRepository):
    """
    Репозиторий для работы с таблицей model
    """

    def get_by_id(self, model_id: int) -> Optional[Dict[str, Any]]:
        query = 'SELECT * FROM "model" WHERE model_id = %(model_id)s'
        return self.execute_query_single(query, {"model_id": model_id})

    def get_models_by_user(self, user_id: int, status: Optional[str] = None) -> List[Dict[str, Any]]:
        if status:
            query = 'SELECT * FROM "model" WHERE user_id = %(user_id)s AND status = %(status)s'
            return self.execute_query(query, {"user_id": user_id, "status": status})
        else:
            query = 'SELECT * FROM "model" WHERE user_id = %(user_id)s'
            return self.execute_query(query, {"user_id": user_id})

    def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        fields = []
        values = []
        params = {}

        for key, value in data.items():
            if value is not None:
                fields.append(key)
                values.append(f"%({key})s")
                params[key] = value

        query = f'''
        INSERT INTO "model" ({", ".join(fields)})
        VALUES ({", ".join(values)})
        RETURNING *
        '''
        return self.execute_with_returning(query, params)

    def update(self, model_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not data:
            return self.get_by_id(model_id)

        set_clause = []
        params = {"model_id": model_id}

        for key, value in data.items():
            set_clause.append(f"{key} = %({key})s")
            params[key] = value

        query = f'''
        UPDATE "model"
        SET {", ".join(set_clause)}, update_dttm = NOW()
        WHERE model_id = %(model_id)s
        RETURNING *
        '''
        return self.execute_with_returning(query, params)

    def delete(self, model_id: int) -> bool:
        query = 'DELETE FROM "model" WHERE model_id = %(model_id)s'
        try:
            affected_rows = self.execute_non_query(query, {"model_id": model_id})
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Ошибка при удалении модели {model_id}: {e}")
            return False

    def find_by_status(self, status: str) -> List[Dict[str, Any]]:
        query = 'SELECT * FROM "model" WHERE status = %(status)s'
        return self.execute_query(query, {"status": status})
