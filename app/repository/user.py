from typing import Dict, List, Optional, Any, Tuple
import logging
from app.repository.db import BaseRepository
from datetime import datetime

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """
    Репозиторий для работы с таблицей пользователей
    """

    def get_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        query = 'SELECT * FROM "user" WHERE user_id = %(user_id)s'
        return self.execute_query_single(query, {"user_id": user_id})

    def get(self, user_id: int) -> Optional[Dict[str, Any]]:
        return self.get_by_id(user_id)

    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        query = 'SELECT * FROM "user" WHERE username = %(username)s'
        return self.execute_query_single(query, {"username": username})

    def get_by_referral_code(self, referral_code: str) -> Optional[Dict[str, Any]]:
        query = 'SELECT * FROM "user" WHERE referral_code = %(referral_code)s'
        return self.execute_query_single(query, {"referral_code": referral_code})

    def create(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        fields = []
        values = []
        params = {}

        for key, value in user_data.items():
            if value is not None:
                fields.append(key)
                values.append(f"%({key})s")
                params[key] = value

        query = f'''
        INSERT INTO "user" ({", ".join(fields)})
        VALUES ({", ".join(values)})
        RETURNING *
        '''

        return self.execute_with_returning(query, params)

    def update(self, user_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not update_data:
            return self.get_by_id(user_id)

        set_clause = []
        params = {"user_id": user_id}

        for key, value in update_data.items():
            set_clause.append(f"{key} = %({key})s")
            params[key] = value

        query = f'''
        UPDATE "user"
        SET {", ".join(set_clause)}
        WHERE user_id = %(user_id)s
        RETURNING *
        '''

        return self.execute_with_returning(query, params)

    def delete(self, user_id: int) -> bool:
        query = 'DELETE FROM "user" WHERE user_id = %(user_id)s'
        try:
            affected_rows = self.execute_non_query(query, {"user_id": user_id})
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Ошибка при удалении пользователя {user_id}: {e}")
            return False

    def update_tokens(self, user_id: int, amount: int) -> Optional[Dict[str, Any]]:
        query = '''
        UPDATE "user"
        SET tokens_left = tokens_left + %(amount)s
        WHERE user_id = %(user_id)s
        RETURNING *
        '''
        return self.execute_with_returning(query, {"user_id": user_id, "amount": amount})

    def get_user_referrals(self, user_id: int) -> List[Dict[str, Any]]:
        query = 'SELECT * FROM "user" WHERE referrer_id = %(user_id)s'
        return self.execute_query(query, {"user_id": user_id})

    def update_user_state(self, user_id: int, state: str) -> Optional[Dict[str, Any]]:
        query = '''
        UPDATE "user"
        SET user_state = %(state)s, last_active = NOW()
        WHERE user_id = %(user_id)s
        RETURNING *
        '''
        return self.execute_with_returning(query, {"user_id": user_id, "state": state})

    def get_users_by_state(self, state: str, limit: int = 100) -> List[Dict[str, Any]]:
        query = '''
        SELECT * FROM "user" 
        WHERE user_state = %(state)s
        ORDER BY last_active DESC
        LIMIT %(limit)s
        '''
        return self.execute_query(query, {"state": state, "limit": limit})

    def get_top_referrers(self, limit: int = 10) -> List[Dict[str, Any]]:
        query = '''
        SELECT u.*, COUNT(r.user_id) as referrals_count 
        FROM "user" u
        LEFT JOIN "user" r ON r.referrer_id = u.user_id
        GROUP BY u.user_id
        HAVING COUNT(r.user_id) > 0
        ORDER BY referrals_count DESC
        LIMIT %(limit)s
        '''
        return self.execute_query(query, {"limit": limit})

    def find_users_by_criteria(self, criteria: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        where_clauses = []
        params = {"limit": limit}

        if "username" in criteria:
            where_clauses.append("username ILIKE %(username)s")
            params["username"] = f"%{criteria['username']}%"

        if "min_tokens" in criteria:
            where_clauses.append("tokens_left >= %(min_tokens)s")
            params["min_tokens"] = criteria["min_tokens"]

        if "max_tokens" in criteria:
            where_clauses.append("tokens_left <= %(max_tokens)s")
            params["max_tokens"] = criteria["max_tokens"]

        if "active_after" in criteria:
            where_clauses.append("last_active >= %(active_after)s")
            params["active_after"] = criteria["active_after"]

        if "active_before" in criteria:
            where_clauses.append("last_active <= %(active_before)s")
            params["active_before"] = criteria["active_before"]

        if "state" in criteria:
            where_clauses.append("user_state = %(state)s")
            params["state"] = criteria["state"]

        if "blocked" in criteria:
            where_clauses.append("blocked = %(blocked)s")
            params["blocked"] = criteria["blocked"]

        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = f'''
        SELECT * FROM "user"
        WHERE {where_clause}
        ORDER BY last_active DESC
        LIMIT %(limit)s
        '''
        return self.execute_query(query, params)