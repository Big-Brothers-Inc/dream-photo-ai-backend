from typing import Dict, List, Optional, Any
from app.repository.db import BaseRepository
import logging

logger = logging.getLogger(__name__)


class LoraTagRelationRepository(BaseRepository):
    """
    Репозиторий для работы с таблицей lora_tag_relation
    """

    def get_by_id(self, relation_id: int) -> Optional[Dict[str, Any]]:
        query = 'SELECT * FROM "lora_tag_relation" WHERE relation_id = %(relation_id)s'
        return self.execute_query_single(query, {"relation_id": relation_id})

    def get_all(self) -> List[Dict[str, Any]]:
        query = 'SELECT * FROM "lora_tag_relation"'
        return self.execute_query(query)

    def get_tags_for_lora(self, lora_id: int) -> List[Dict[str, Any]]:
        query = '''
        SELECT r.*, t.name, t.description
        FROM "lora_tag_relation" r
        JOIN "lora_tag" t ON r.tag_id = t.tag_id
        WHERE r.lora_id = %(lora_id)s
        '''
        return self.execute_query(query, {"lora_id": lora_id})

    def get_loras_for_tag(self, tag_id: int) -> List[Dict[str, Any]]:
        query = '''
        SELECT r.*, l.name as lora_name
        FROM "lora_tag_relation" r
        JOIN "lora" l ON r.lora_id = l.lora_id
        WHERE r.tag_id = %(tag_id)s
        '''
        return self.execute_query(query, {"tag_id": tag_id})

    def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        query = '''
        INSERT INTO "lora_tag_relation" (lora_id, tag_id)
        VALUES (%(lora_id)s, %(tag_id)s)
        RETURNING *
        '''
        return self.execute_with_returning(query, data)

    def update(self, relation_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not data:
            return self.get_by_id(relation_id)

        set_clause = []
        params = {"relation_id": relation_id}

        for key, value in data.items():
            set_clause.append(f"{key} = %({key})s")
            params[key] = value

        query = f'''
        UPDATE "lora_tag_relation"
        SET {", ".join(set_clause)}
        WHERE relation_id = %(relation_id)s
        RETURNING *
        '''
        return self.execute_with_returning(query, params)

    def delete(self, relation_id: int) -> bool:
        query = 'DELETE FROM "lora_tag_relation" WHERE relation_id = %(relation_id)s'
        try:
            affected_rows = self.execute_non_query(query, {"relation_id": relation_id})
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Ошибка при удалении связи {relation_id}: {e}")
            return False

    def delete_by_lora_and_tag(self, lora_id: int, tag_id: int) -> bool:
        query = 'DELETE FROM "lora_tag_relation" WHERE lora_id = %(lora_id)s AND tag_id = %(tag_id)s'
        try:
            affected_rows = self.execute_non_query(query, {"lora_id": lora_id, "tag_id": tag_id})
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Ошибка при удалении связи LoRA <-> Tag: {e}")
            return False

    def delete_all_for_lora(self, lora_id: int) -> bool:
        query = 'DELETE FROM "lora_tag_relation" WHERE lora_id = %(lora_id)s'
        try:
            self.execute_non_query(query, {"lora_id": lora_id})
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении всех тегов для LoRA {lora_id}: {e}")
            return False

