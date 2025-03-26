# app/repository/payment.py

from typing import Any, Dict, List, Optional
from app.repository.db import BaseRepository
from app.utils.logger import logger


class PaymentRepository(BaseRepository):
    def get_by_id(self, payment_id: int) -> Optional[Dict[str, Any]]:
        query = """
            SELECT * FROM payment WHERE payment_id = %(payment_id)s
        """
        return self.execute_query_single(query, {"payment_id": payment_id})

    def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        query = """
            INSERT INTO payment (user_id, amount, tokens, payment_method, transaction_id, status, promo_id)
            VALUES (%(user_id)s, %(amount)s, %(tokens)s, %(payment_method)s, %(transaction_id)s, %(status)s, %(promo_id)s)
            RETURNING *
        """
        return self.execute_with_returning(query, data)

    def update(self, payment_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        set_clauses = ", ".join([f"{key} = %({key})s" for key in data])
        query = f"""
            UPDATE payment SET {set_clauses}
            WHERE payment_id = %(payment_id)s
            RETURNING *
        """
        data["payment_id"] = payment_id
        return self.execute_with_returning(query, data)

    def delete(self, payment_id: int) -> bool:
        query = """
            DELETE FROM payment WHERE payment_id = %(payment_id)s
        """
        affected = self.execute_non_query(query, {"payment_id": payment_id})
        return affected > 0

    def get_by_user_id(self, user_id: int) -> List[Dict[str, Any]]:
        query = """
            SELECT * FROM payment WHERE user_id = %(user_id)s ORDER BY payment_dttm DESC
        """
        return self.execute_query(query, {"user_id": user_id})

    def get_all(self) -> List[Dict[str, Any]]:
        query = """
            SELECT * FROM payment ORDER BY payment_dttm DESC
        """
        return self.execute_query(query)

    def get_by_transaction_id(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        query = """
            SELECT * FROM payment WHERE transaction_id = %(transaction_id)s
        """
        return self.execute_query_single(query, {"transaction_id": transaction_id})
