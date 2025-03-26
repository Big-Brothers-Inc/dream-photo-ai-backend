from typing import Dict, List, Optional, Any
from app.repository.db import BaseRepository
import logging

logger = logging.getLogger(__name__)


class LoraRepository(BaseRepository):
    """
    Репозиторий для работы с таблицей lora
    """

    def get_by_id(self, lora_id: int) -> Optional[Dict[str, Any]]:
        query = 'SELECT * FROM "lora" WHERE lora_id = %(lora_id)s'
        return self.execute_query_single(query, {"lora_id": lora_id})

    def get_all_active(self) -> List[Dict[str, Any]]:
        query = 'SELECT * FROM "lora" WHERE is_active = TRUE'
        return self.execute_query(query)

    def get_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        query = 'SELECT * FROM "lora" WHERE user_id = %(user_id)s'
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
        INSERT INTO "lora" ({", ".join(fields)})
        VALUES ({", ".join(values)})
        RETURNING *
        '''
        return self.execute_with_returning(query, params)

    def update(self, lora_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not data:
            return self.get_by_id(lora_id)

        set_clause = []
        params = {"lora_id": lora_id}

        for key, value in data.items():
            set_clause.append(f"{key} = %({key})s")
            params[key] = value

        query = f'''
        UPDATE "lora"
        SET {", ".join(set_clause)}, create_dttm = NOW()
        WHERE lora_id = %(lora_id)s
        RETURNING *
        '''
        return self.execute_with_returning(query, params)

    def delete(self, lora_id: int) -> bool:
        query = 'DELETE FROM "lora" WHERE lora_id = %(lora_id)s'
        try:
            affected_rows = self.execute_non_query(query, {"lora_id": lora_id})
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Ошибка при удалении LoRA {lora_id}: {e}")
            return False

    def find_by_trigger_word(self, trigger_word: str) -> List[Dict[str, Any]]:
        query = 'SELECT * FROM "lora" WHERE trigger_word = %(trigger_word)s'
        return self.execute_query(query, {"trigger_word": trigger_word})
