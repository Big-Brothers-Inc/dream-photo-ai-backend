from typing import Dict, List, Optional, Any, Tuple
import logging
from .db import BaseRepository

logger = logging.getLogger(__name__)

class ReferralRepository(BaseRepository):
    """
    Репозиторий для работы с реферальной системой
    """
    
    def get_invite_by_id(self, invite_id: int) -> Optional[Dict]:
        """
        Получение пригласительного кода по ID
        
        Args:
            invite_id: ID пригласительного кода
            
        Returns:
            Данные пригласительного кода или None, если код не найден
        """
        query = 'SELECT * FROM "ReferralInvite" WHERE invite_id = %s'
        return self.execute_query(query, (invite_id,), fetch_one=True)
    
    def get_invite_by_code(self, invite_code: str) -> Optional[Dict]:
        """
        Получение пригласительного кода по значению кода
        
        Args:
            invite_code: Значение пригласительного кода
            
        Returns:
            Данные пригласительного кода или None, если код не найден
        """
        query = 'SELECT * FROM "ReferralInvite" WHERE invite_code = %s'
        return self.execute_query(query, (invite_code,), fetch_one=True)
    
    def get_user_invites(self, user_id: int) -> List[Dict]:
        """
        Получение списка пригласительных кодов пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Список пригласительных кодов пользователя
        """
        query = """
            SELECT r.*, 
                  (SELECT COUNT(*) FROM "User" u WHERE u.invited_by_code = r.invite_code) as used_count,
                  (SELECT SUM(token_reward) FROM "User" u WHERE u.invited_by_code = r.invite_code) as total_tokens_rewarded
            FROM "ReferralInvite" r
            WHERE r.user_id = %s
            ORDER BY r.created_at DESC
        """
        return self.execute_query(query, (user_id,))
    
    def create_invite(self, user_id: int, invite_code: str, description: Optional[str] = None) -> Optional[Dict]:
        """
        Создание нового пригласительного кода
        
        Args:
            user_id: ID пользователя
            invite_code: Значение пригласительного кода
            description: Описание пригласительного кода
            
        Returns:
            Данные созданного пригласительного кода или None в случае ошибки
        """
        query = """
            INSERT INTO "ReferralInvite" 
                (user_id, invite_code, description, created_at, updated_at)
            VALUES
                (%s, %s, %s, NOW(), NOW())
            RETURNING *
        """
        
        try:
            result = self.execute_query(query, (user_id, invite_code, description), fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"Ошибка при создании пригласительного кода: {e}")
            return None
    
    def update_invite(self, invite_id: int, data: Dict) -> Optional[Dict]:
        """
        Обновление данных пригласительного кода
        
        Args:
            invite_id: ID пригласительного кода
            data: Данные для обновления
            
        Returns:
            Обновленные данные пригласительного кода или None в случае ошибки
        """
        # Формируем строку SET для UPDATE
        set_values = []
        values = []
        
        for key, value in data.items():
            set_values.append(f'{key} = %s')
            values.append(value)
        
        # Добавляем обновление updated_at
        set_values.append('updated_at = NOW()')
        
        set_str = ', '.join(set_values)
        values.append(invite_id)  # Добавляем ID кода для WHERE
        
        query = f'UPDATE "ReferralInvite" SET {set_str} WHERE invite_id = %s RETURNING *'
        
        try:
            result = self.execute_query(query, tuple(values), fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"Ошибка при обновлении пригласительного кода: {e}")
            return None
    
    def delete_invite(self, invite_id: int) -> bool:
        """
        Удаление пригласительного кода
        
        Args:
            invite_id: ID пригласительного кода
            
        Returns:
            True, если код успешно удален
        """
        query = 'DELETE FROM "ReferralInvite" WHERE invite_id = %s'
        
        try:
            self.execute_query(query, (invite_id,))
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении пригласительного кода: {e}")
            return False
    
    def get_users_by_invite_code(self, invite_code: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        Получение списка пользователей, зарегистрированных по пригласительному коду
        
        Args:
            invite_code: Пригласительный код
            limit: Максимальное количество результатов
            offset: Смещение для пагинации
            
        Returns:
            Список пользователей
        """
        query = """
            SELECT u.*
            FROM "User" u
            WHERE u.invited_by_code = %s
            ORDER BY u.created_at DESC
            LIMIT %s OFFSET %s
        """
        return self.execute_query(query, (invite_code, limit, offset))
    
    def count_users_by_invite_code(self, invite_code: str) -> int:
        """
        Подсчет количества пользователей, зарегистрированных по пригласительному коду
        
        Args:
            invite_code: Пригласительный код
            
        Returns:
            Количество пользователей
        """
        query = """
            SELECT COUNT(*) as count
            FROM "User"
            WHERE invited_by_code = %s
        """
        result = self.execute_query(query, (invite_code,), fetch_one=True)
        return result.get('count', 0) if result else 0
    
    def get_token_gift_by_id(self, gift_id: int) -> Optional[Dict]:
        """
        Получение подарка токенов по ID
        
        Args:
            gift_id: ID подарка токенов
            
        Returns:
            Данные подарка токенов или None, если подарок не найден
        """
        query = """
            SELECT g.*, 
                  u_from.username as sender_username, 
                  u_to.username as recipient_username
            FROM "TokenGift" g
            JOIN "User" u_from ON g.from_user_id = u_from.user_id
            JOIN "User" u_to ON g.to_user_id = u_to.user_id
            WHERE g.gift_id = %s
        """
        return self.execute_query(query, (gift_id,), fetch_one=True)
    
    def get_outgoing_gifts(self, user_id: int, limit: int = 10, offset: int = 0) -> List[Dict]:
        """
        Получение исходящих подарков токенов пользователя
        
        Args:
            user_id: ID пользователя
            limit: Максимальное количество результатов
            offset: Смещение для пагинации
            
        Returns:
            Список исходящих подарков токенов
        """
        query = """
            SELECT g.*, u.username as recipient_username, u.first_name, u.last_name
            FROM "TokenGift" g
            JOIN "User" u ON g.to_user_id = u.user_id
            WHERE g.from_user_id = %s
            ORDER BY g.created_at DESC
            LIMIT %s OFFSET %s
        """
        return self.execute_query(query, (user_id, limit, offset))
    
    def get_incoming_gifts(self, user_id: int, limit: int = 10, offset: int = 0) -> List[Dict]:
        """
        Получение входящих подарков токенов пользователя
        
        Args:
            user_id: ID пользователя
            limit: Максимальное количество результатов
            offset: Смещение для пагинации
            
        Returns:
            Список входящих подарков токенов
        """
        query = """
            SELECT g.*, u.username as sender_username, u.first_name, u.last_name
            FROM "TokenGift" g
            JOIN "User" u ON g.from_user_id = u.user_id
            WHERE g.to_user_id = %s
            ORDER BY g.created_at DESC
            LIMIT %s OFFSET %s
        """
        return self.execute_query(query, (user_id, limit, offset))
    
    def create_token_gift(self, from_user_id: int, to_user_id: int, tokens: int, message: Optional[str] = None) -> Optional[Dict]:
        """
        Создание нового подарка токенов
        
        Args:
            from_user_id: ID отправителя
            to_user_id: ID получателя
            tokens: Количество токенов
            message: Сообщение
            
        Returns:
            Данные созданного подарка токенов или None в случае ошибки
        """
        query = """
            INSERT INTO "TokenGift" 
                (from_user_id, to_user_id, tokens, message, created_at)
            VALUES
                (%s, %s, %s, %s, NOW())
            RETURNING *
        """
        
        try:
            result = self.execute_query(query, (from_user_id, to_user_id, tokens, message), fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"Ошибка при создании подарка токенов: {e}")
            return None
    
    def get_top_referrers(self, limit: int = 10) -> List[Dict]:
        """
        Получение топ рефереров по количеству приглашенных пользователей
        
        Args:
            limit: Максимальное количество результатов
            
        Returns:
            Список топ рефереров
        """
        query = """
            SELECT 
                u.user_id,
                u.username,
                u.first_name,
                u.last_name,
                COUNT(DISTINCT r.invite_code) as invite_codes_count,
                COUNT(DISTINCT u2.user_id) as invited_users_count,
                SUM(u2.token_reward) as total_reward
            FROM "User" u
            JOIN "ReferralInvite" r ON u.user_id = r.user_id
            JOIN "User" u2 ON u2.invited_by_code = r.invite_code
            GROUP BY u.user_id, u.username, u.first_name, u.last_name
            ORDER BY invited_users_count DESC, total_reward DESC
            LIMIT %s
        """
        
        return self.execute_query(query, (limit,))
    
    def get_top_referral_sources(self, limit: int = 10) -> List[Dict]:
        """
        Получение топ источников регистрации по количеству пользователей
        
        Args:
            limit: Максимальное количество результатов
            
        Returns:
            Список топ источников регистрации
        """
        query = """
            SELECT 
                s.source_name,
                COUNT(u.user_id) as users_count,
                AVG(u.tokens) as avg_tokens_per_user,
                SUM(u.tokens) as total_tokens,
                MIN(u.created_at) as first_registration,
                MAX(u.created_at) as last_registration
            FROM "User" u
            JOIN "Source" s ON u.source_id = s.source_id
            GROUP BY s.source_name
            ORDER BY users_count DESC
            LIMIT %s
        """
        
        return self.execute_query(query, (limit,)) 