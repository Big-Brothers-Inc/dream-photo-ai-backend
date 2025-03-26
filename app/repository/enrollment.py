# app/repository/enrollment.py

from typing import Any, Dict, List, Optional
from app.repository.db import BaseRepository
from app.utils.logger import logger


class EnrollmentRepository(BaseRepository):
    def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        query = """
            INSERT INTO enrollment (user_id, amount)
            VALUES (%(user_id)s, %(amount)s)
            RETURNING *
        """
        return self.execute_with_returning(query, data)

    def get_by_id(self, enrollment_id: int) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM enrollment WHERE enrollment_id = %(enrollment_id)s"
        return self.execute_query_single(query, {"enrollment_id": enrollment_id})

    def create_with_payment(self, user_id: int, payment_id: int, amount: int) -> Optional[Dict[str, Any]]:
        query = """
            INSERT INTO enrollment (user_id, payment_id, amount)
            VALUES (%(user_id)s, %(payment_id)s, %(amount)s)
            RETURNING *
        """
        return self.execute_with_returning(query, {
            "user_id": user_id,
            "payment_id": payment_id,
            "amount": amount
        })

    def create_with_promo(self, user_id: int, promo_id: int, amount: int) -> Optional[Dict[str, Any]]:
        query = """
            INSERT INTO enrollment (user_id, promo_id, amount)
            VALUES (%(user_id)s, %(promo_id)s, %(amount)s)
            RETURNING *
        """
        return self.execute_with_returning(query, {
            "user_id": user_id,
            "promo_id": promo_id,
            "amount": amount
        })

    def update(self, enrollment_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        set_clauses = ", ".join([f"{key} = %({key})s" for key in data])
        query = f"""
            UPDATE enrollment SET {set_clauses}
            WHERE enrollment_id = %(enrollment_id)s
            RETURNING *
        """
        data["enrollment_id"] = enrollment_id
        return self.execute_with_returning(query, data)

    def delete(self, enrollment_id: int) -> bool:
        query = "DELETE FROM enrollment WHERE enrollment_id = %(enrollment_id)s"
        affected = self.execute_non_query(query, {"enrollment_id": enrollment_id})
        return affected > 0

    def get_all(self) -> List[Dict[str, Any]]:
        query = "SELECT * FROM enrollment ORDER BY enrollment_dttm DESC"
        return self.execute_query(query)

    def get_by_user_id(self, user_id: int) -> List[Dict[str, Any]]:
        query = """
            SELECT * FROM enrollment
            WHERE user_id = %(user_id)s
            ORDER BY enrollment_dttm DESC
        """
        return self.execute_query(query, {"user_id": user_id})

    def get_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        query = """
            SELECT * FROM enrollment
            WHERE enrollment_dttm BETWEEN %(start)s AND %(end)s
            ORDER BY enrollment_dttm
        """
        return self.execute_query(query, {"start": start_date, "end": end_date})

    def get_total_amount(self) -> int:
        query = "SELECT COALESCE(SUM(amount), 0) FROM enrollment"
        return self.execute_query_scalar(query)

    def get_total_amount_by_user(self, user_id: int) -> int:
        query = "SELECT COALESCE(SUM(amount), 0) FROM enrollment WHERE user_id = %(user_id)s"
        return self.execute_query_scalar(query, {"user_id": user_id})

    def get_stats_grouped_by_day(self) -> List[Dict[str, Any]]:
        query = """
            SELECT
                DATE(enrollment_dttm) AS day,
                COUNT(*) AS enrollments,
                SUM(amount) AS total_amount
            FROM enrollment
            GROUP BY day
            ORDER BY day
        """
        return self.execute_query(query)
