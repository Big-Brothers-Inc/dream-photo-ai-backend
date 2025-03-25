from typing import Dict, List, Optional, Any, Tuple
import logging
from .base_repository import BaseRepository
from datetime import datetime

logger = logging.getLogger(__name__)

class UserRepository(BaseRepository):
    """
    Репозиторий для работы с таблицей пользователей
    """
    
    def get_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение пользователя по Telegram ID
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            Данные пользователя или None, если пользователь не найден
        """
        query = '''
        SELECT * FROM "User" WHERE user_id = %(user_id)s
        '''
        return self.execute_query_single(query, {"user_id": user_id})
    
    def get(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Алиас для метода get_by_id - получение пользователя по Telegram ID
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            Данные пользователя или None, если пользователь не найден
        """
        return self.get_by_id(user_id)
    
    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Получение пользователя по имени пользователя Telegram
        
        Args:
            username: Имя пользователя Telegram (без @)
            
        Returns:
            Данные пользователя или None, если пользователь не найден
        """
        query = '''
        SELECT * FROM "User" WHERE username = %(username)s
        '''
        return self.execute_query_single(query, {"username": username})
    
    def get_by_referral_code(self, referral_code: str) -> Optional[Dict[str, Any]]:
        """
        Получение пользователя по реферальному коду
        
        Args:
            referral_code: Реферальный код пользователя
            
        Returns:
            Данные пользователя или None, если пользователь не найден
        """
        query = '''
        SELECT * FROM "User" WHERE referral_code = %(referral_code)s
        '''
        return self.execute_query_single(query, {"referral_code": referral_code})
    
    def create(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Создание нового пользователя
        
        Args:
            user_data: Данные пользователя для создания
                user_id: Telegram ID пользователя
                username: Имя пользователя Telegram
                first_name: Имя пользователя
                last_name: Фамилия пользователя
                activation_date: Дата активации (опционально)
                tokens_left: Количество токенов (опционально)
                source_id: ID источника регистрации (опционально)
                referral_code: Реферальный код (опционально)
                referrer_id: ID пригласившего пользователя (опционально)
                language: Язык пользователя (опционально)
                
        Returns:
            Данные созданного пользователя или None в случае ошибки
        """
        fields = []
        values = []
        params = {}
        
        for key, value in user_data.items():
            if value is not None:
                fields.append(key)
                values.append(f"%({key})s")
                params[key] = value
        
        query = f'''
        INSERT INTO "User" ({", ".join(fields)})
        VALUES ({", ".join(values)})
        RETURNING *
        '''
        
        return self.execute_with_returning(query, params)
    
    def update(self, user_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Обновление данных пользователя
        
        Args:
            user_id: Telegram ID пользователя
            update_data: Данные для обновления
            
        Returns:
            Обновленные данные пользователя или None в случае ошибки
        """
        if not update_data:
            return self.get_by_id(user_id)
            
        set_clause = []
        params = {"user_id": user_id}
        
        for key, value in update_data.items():
            set_clause.append(f"{key} = %({key})s")
            params[key] = value
        
        query = f'''
        UPDATE "User"
        SET {", ".join(set_clause)}
        WHERE user_id = %(user_id)s
        RETURNING *
        '''
        
        return self.execute_with_returning(query, params)
    
    def delete(self, user_id: int) -> bool:
        """
        Удаление пользователя
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            True, если пользователь успешно удален, иначе False
        """
        query = '''
        DELETE FROM "User" WHERE user_id = %(user_id)s
        '''
        
        try:
            affected_rows = self.execute_non_query(query, {"user_id": user_id})
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Ошибка при удалении пользователя {user_id}: {e}")
            return False
    
    def update_tokens(self, user_id: int, amount: int) -> Optional[Dict[str, Any]]:
        """
        Обновление количества токенов пользователя
        
        Args:
            user_id: Telegram ID пользователя
            amount: Количество токенов для добавления (может быть отрицательным)
            
        Returns:
            Обновленные данные пользователя или None в случае ошибки
        """
        query = '''
        UPDATE "User"
        SET tokens_left = tokens_left + %(amount)s
        WHERE user_id = %(user_id)s
        RETURNING *
        '''
        
        return self.execute_with_returning(query, {"user_id": user_id, "amount": amount})
    
    def get_user_referrals(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Получение списка рефералов пользователя
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            Список пользователей, зарегистрированных по реферальной ссылке
        """
        query = '''
        SELECT * FROM "User" WHERE referrer_id = %(user_id)s
        '''
        
        return self.execute_query(query, {"user_id": user_id})
    
    def increment_generated_images(self, user_id: int, count: int = 1) -> Optional[Dict[str, Any]]:
        """
        Увеличение счетчика сгенерированных изображений пользователя
        
        Args:
            user_id: Telegram ID пользователя
            count: Количество изображений для добавления
            
        Returns:
            Обновленные данные пользователя или None в случае ошибки
        """
        query = '''
        UPDATE "User"
        SET images_generated = images_generated + %(count)s
        WHERE user_id = %(user_id)s
        RETURNING *
        '''
        
        return self.execute_with_returning(query, {"user_id": user_id, "count": count})
    
    def increment_trained_models(self, user_id: int, count: int = 1) -> Optional[Dict[str, Any]]:
        """
        Увеличение счетчика обученных моделей пользователя
        
        Args:
            user_id: Telegram ID пользователя
            count: Количество моделей для добавления
            
        Returns:
            Обновленные данные пользователя или None в случае ошибки
        """
        query = '''
        UPDATE "User"
        SET models_trained = models_trained + %(count)s
        WHERE user_id = %(user_id)s
        RETURNING *
        '''
        
        return self.execute_with_returning(query, {"user_id": user_id, "count": count})
    
    def update_user_state(self, user_id: int, state: str) -> Optional[Dict[str, Any]]:
        """
        Обновление состояния пользователя в боте
        
        Args:
            user_id: Telegram ID пользователя
            state: Новое состояние пользователя
            
        Returns:
            Обновленные данные пользователя или None в случае ошибки
        """
        query = '''
        UPDATE "User"
        SET user_state = %(state)s, last_active = NOW()
        WHERE user_id = %(user_id)s
        RETURNING *
        '''
        
        return self.execute_with_returning(query, {"user_id": user_id, "state": state})
    
    def get_users_by_state(self, state: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получение списка пользователей в определенном состоянии
        
        Args:
            state: Состояние пользователей
            limit: Максимальное количество пользователей
            
        Returns:
            Список пользователей в указанном состоянии
        """
        query = '''
        SELECT * FROM "User" 
        WHERE user_state = %(state)s
        ORDER BY last_active DESC
        LIMIT %(limit)s
        '''
        
        return self.execute_query(query, {"state": state, "limit": limit})
    
    def get_top_referrers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Получение топ рефереров по количеству приглашенных пользователей
        
        Args:
            limit: Максимальное количество пользователей
            
        Returns:
            Список пользователей с наибольшим количеством приглашенных
        """
        query = '''
        SELECT u.*, COUNT(r.user_id) as referrals_count 
        FROM "User" u
        LEFT JOIN "User" r ON r.referrer_id = u.user_id
        GROUP BY u.user_id
        HAVING COUNT(r.user_id) > 0
        ORDER BY referrals_count DESC
        LIMIT %(limit)s
        '''
        
        return self.execute_query(query, {"limit": limit})
    
    def find_users_by_criteria(self, criteria: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        """
        Поиск пользователей по различным критериям
        
        Args:
            criteria: Критерии поиска
                username: Имя пользователя (частичное совпадение)
                min_tokens: Минимальное количество токенов
                max_tokens: Максимальное количество токенов
                active_after: Активные после указанной даты
                active_before: Активные до указанной даты
                state: Состояние пользователя
                blocked: Заблокирован ли пользователь
            limit: Максимальное количество пользователей
            
        Returns:
            Список пользователей, соответствующих критериям
        """
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
        SELECT * FROM "User"
        WHERE {where_clause}
        ORDER BY last_active DESC
        LIMIT %(limit)s
        '''
        
        return self.execute_query(query, params) 