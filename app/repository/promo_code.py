from typing import Dict, Optional, Any, List
from app.repository.db import BaseRepository
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PromoCodeRepository(BaseRepository):
    def is_valid_for_use(self, promo_id: int) -> bool:
        query = '''
            SELECT 
                pc.promo_id,
                pc.is_active,
                pc.valid_to,
                pc.max_usages,
                COUNT(pu.usage_id) AS usage_count
            FROM promo_code pc
            LEFT JOIN promo_usage pu ON pu.promo_id = pc.promo_id
            WHERE pc.promo_id = %(promo_id)s
            GROUP BY pc.promo_id
            '''
        promo = self.execute_query_single(query, {"promo_id": promo_id})
        if not promo:
            return False

        if not promo["is_active"]:
            return False

        if promo["valid_to"] and promo["valid_to"] < datetime.utcnow():
            return False

        if promo["max_usages"] is not None and promo["usage_count"] >= promo["max_usages"]:
            return False

        return True

    def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        query = '''
        INSERT INTO "promo_code" 
            (code, discount_percent, tokens_amount, valid_from, valid_to, max_usages, created_by, is_active)
        VALUES 
            (%(code)s, %(discount_percent)s, %(tokens_amount)s, %(valid_from)s, %(valid_to)s, %(max_usages)s, %(created_by)s, %(is_active)s)
        RETURNING *
        '''
        return self.execute_with_returning(query, data)

    def update(self, promo_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        set_clauses = []
        params = {"promo_id": promo_id}

        for key, value in data.items():
            set_clauses.append(f"{key} = %({key})s")
            params[key] = value

        set_clause = ", ".join(set_clauses)
        query = f'''
        UPDATE "promo_code"
        SET {set_clause}
        WHERE promo_id = %(promo_id)s
        RETURNING *
        '''
        return self.execute_with_returning(query, params)

    def get_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        query = 'SELECT * FROM "promo_code" WHERE code = %(code)s'
        return self.execute_query_single(query, {"code": code})

    def get_by_id(self, promo_id: int) -> Optional[Dict[str, Any]]:
        query = 'SELECT * FROM "promo_code" WHERE promo_id = %(promo_id)s'
        return self.execute_query_single(query, {"promo_id": promo_id})

    def delete(self, promo_id: int) -> Optional[Dict[str, Any]]:
        query = '''
        UPDATE "promo_code"
        SET is_active = FALSE
        WHERE promo_id = %(promo_id)s
        RETURNING *
        '''
        return self.execute_with_returning(query, {"promo_id": promo_id})

    def list_all(self, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        params = {}
        condition = ""
        if is_active is not None:
            condition = "WHERE is_active = %(is_active)s"
            params["is_active"] = is_active

        query = f'SELECT * FROM "promo_code" {condition} ORDER BY promo_id DESC'
        return self.execute_query(query, params)
