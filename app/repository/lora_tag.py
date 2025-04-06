from typing import Dict, List, Optional, Any
from app.repository.db import BaseRepository
import logging

logger = logging.getLogger(__name__)


class LoraTagRepository(BaseRepository):
    """
    Репозиторий для работы с таблицей lora_tag
    """

    def get_by_id(self, tag_id: int) -> Optional[Dict[str, Any]]:
        query = 'SELECT * FROM "lora_tag" WHERE tag_id = %(tag_id)s'
        return self.execute_query_single(query, {"tag_id": tag_id})

    def get_all(self) -> List[Dict[str, Any]]:
        query = 'SELECT * FROM "lora_tag" ORDER BY name ASC'
        return self.execute_query(query)

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
        INSERT INTO "lora_tag" ({", ".join(fields)})
        VALUES ({", ".join(values)})
        RETURNING *
        '''
        return self.execute_with_returning(query, params)

    def update(self, tag_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not data:
            return self.get_by_id(tag_id)

        set_clause = []
        params = {"tag_id": tag_id}

        for key, value in data.items():
            set_clause.append(f"{key} = %({key})s")
            params[key] = value

        query = f'''
        UPDATE "lora_tag"
        SET {", ".join(set_clause)}
        WHERE tag_id = %(tag_id)s
        RETURNING *
        '''
        return self.execute_with_returning(query, params)

    def delete(self, tag_id: int) -> bool:
        query = 'DELETE FROM "lora_tag" WHERE tag_id = %(tag_id)s'
        try:
            affected_rows = self.execute_non_query(query, {"tag_id": tag_id})
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Ошибка при удалении тега {tag_id}: {e}")
            return False

    def find_by_name(self, name: str) -> List[Dict[str, Any]]:
        query = 'SELECT * FROM "lora_tag" WHERE LOWER(name) = LOWER(%(name)s)'
        return self.execute_query(query, {"name": name})
