# app/repository/promo_usage.py

from typing import Any, Dict, List, Optional
from app.repository.db import BaseRepository


class PromoUsageRepository(BaseRepository):
    def get_by_id(self, usage_id: int) -> Optional[Dict[str, Any]]:
        query = """
            SELECT * FROM promo_usage WHERE usage_id = %(usage_id)s
        """
        return self.execute_query_single(query, {"usage_id": usage_id})

    def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        query = """
            INSERT INTO promo_usage (promo_id, user_id, payment_id)
            VALUES (%(promo_id)s, %(user_id)s, %(payment_id)s)
            RETURNING *
        """
        return self.execute_with_returning(query, data)

    def update(self, usage_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        set_clauses = ", ".join([f"{key} = %({key})s" for key in data])
        query = f"""
            UPDATE promo_usage SET {set_clauses}
            WHERE usage_id = %(usage_id)s
            RETURNING *
        """
        data["usage_id"] = usage_id
        return self.execute_with_returning(query, data)

    def delete(self, usage_id: int) -> bool:
        query = """
            DELETE FROM promo_usage WHERE usage_id = %(usage_id)s
        """
        affected = self.execute_non_query(query, {"usage_id": usage_id})
        return affected > 0

    def has_user_used_promo(self, user_id: int, promo_id: int) -> bool:
        query = """
            SELECT 1 FROM promo_usage
            WHERE user_id = %(user_id)s AND promo_id = %(promo_id)s
            LIMIT 1
        """
        result = self.execute_query_single(query, {"user_id": user_id, "promo_id": promo_id})
        return result is not None

    def get_by_user_id(self, user_id: int) -> List[Dict[str, Any]]:
        query = """
            SELECT * FROM promo_usage
            WHERE user_id = %(user_id)s
            ORDER BY usage_dttm DESC
        """
        return self.execute_query(query, {"user_id": user_id})

    def get_by_promo_id(self, promo_id: int) -> List[Dict[str, Any]]:
        query = """
            SELECT * FROM promo_usage
            WHERE promo_id = %(promo_id)s
            ORDER BY usage_dttm DESC
        """
        return self.execute_query(query, {"promo_id": promo_id})

    def count_usages_by_promo(self, promo_id: int) -> int:
        query = """
            SELECT COUNT(*) FROM promo_usage WHERE promo_id = %(promo_id)s
        """
        return self.execute_query_scalar(query, {"promo_id": promo_id})
