from typing import Dict, List, Optional, Any, Tuple
import logging
from .db import BaseRepository

logger = logging.getLogger(__name__)

class PaymentRepository(BaseRepository):
    """
    Репозиторий для работы с таблицей платежей
    """
    
    def get_by_id(self, payment_id: int) -> Optional[Dict]:
        """
        Получение платежа по ID
        
        Args:
            payment_id: ID платежа
            
        Returns:
            Данные платежа или None, если платеж не найден
        """
        query = 'SELECT * FROM "Payment" WHERE payment_id = %s'
        return self.execute_query(query, (payment_id,), fetch_one=True)
    
    def get_by_external_id(self, external_id: str) -> Optional[Dict]:
        """
        Получение платежа по внешнему ID (ID платежа в платежной системе)
        
        Args:
            external_id: Внешний ID платежа
            
        Returns:
            Данные платежа или None, если платеж не найден
        """
        query = 'SELECT * FROM "Payment" WHERE external_id = %s'
        return self.execute_query(query, (external_id,), fetch_one=True)
    
    def get_by_user_id(self, user_id: int, limit: int = 10, offset: int = 0) -> List[Dict]:
        """
        Получение платежей пользователя
        
        Args:
            user_id: ID пользователя
            limit: Максимальное количество результатов
            offset: Смещение для пагинации
            
        Returns:
            Список платежей пользователя
        """
        query = """
            SELECT * FROM "Payment"
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        return self.execute_query(query, (user_id, limit, offset))
    
    def create(self, data: Dict) -> Optional[Dict]:
        """
        Создание новой записи о платеже
        
        Args:
            data: Данные платежа
            
        Returns:
            Данные созданного платежа или None в случае ошибки
        """
        # Формируем список полей и значений для вставки
        fields = []
        placeholders = []
        values = []
        
        for key, value in data.items():
            fields.append(key)
            placeholders.append(f'%s')
            values.append(value)
        
        fields_str = ', '.join(fields)
        placeholders_str = ', '.join(placeholders)
        
        query = f'INSERT INTO "Payment" ({fields_str}) VALUES ({placeholders_str}) RETURNING *'
        
        try:
            result = self.execute_query(query, tuple(values), fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"Ошибка при создании записи о платеже: {e}")
            return None
    
    def update(self, payment_id: int, data: Dict) -> Optional[Dict]:
        """
        Обновление данных платежа
        
        Args:
            payment_id: ID платежа
            data: Данные для обновления
            
        Returns:
            Обновленные данные платежа или None в случае ошибки
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
        values.append(payment_id)  # Добавляем ID платежа для WHERE
        
        query = f'UPDATE "Payment" SET {set_str} WHERE payment_id = %s RETURNING *'
        
        try:
            result = self.execute_query(query, tuple(values), fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"Ошибка при обновлении платежа: {e}")
            return None
    
    def delete(self, payment_id: int) -> bool:
        """
        Удаление платежа
        
        Args:
            payment_id: ID платежа
            
        Returns:
            True, если платеж успешно удален
        """
        query = 'DELETE FROM "Payment" WHERE payment_id = %s'
        
        try:
            self.execute_query(query, (payment_id,))
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении платежа: {e}")
            return False
    
    def update_status(self, payment_id: int, status: str) -> Optional[Dict]:
        """
        Обновление статуса платежа
        
        Args:
            payment_id: ID платежа
            status: Новый статус
            
        Returns:
            Обновленные данные платежа или None в случае ошибки
        """
        query = """
            UPDATE "Payment" 
            SET status = %s, 
                updated_at = NOW() 
            WHERE payment_id = %s 
            RETURNING *
        """
        
        try:
            result = self.execute_query(query, (status, payment_id), fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"Ошибка при обновлении статуса платежа: {e}")
            return None
    
    def complete_payment(self, payment_id: int, external_id: Optional[str] = None) -> Optional[Dict]:
        """
        Завершение платежа как успешного
        
        Args:
            payment_id: ID платежа
            external_id: Внешний ID платежа в платежной системе (опционально)
            
        Returns:
            Обновленные данные платежа или None в случае ошибки
        """
        data = {
            'status': 'completed',
            'completed_at': 'NOW()'
        }
        
        if external_id:
            data['external_id'] = external_id
        
        # Формируем строку SET для UPDATE
        set_values = []
        values = []
        
        for key, value in data.items():
            if key == 'completed_at':
                set_values.append(f'{key} = {value}')
            else:
                set_values.append(f'{key} = %s')
                values.append(value)
        
        # Добавляем обновление updated_at
        set_values.append('updated_at = NOW()')
        
        set_str = ', '.join(set_values)
        values.append(payment_id)  # Добавляем ID платежа для WHERE
        
        query = f'UPDATE "Payment" SET {set_str} WHERE payment_id = %s RETURNING *'
        
        try:
            result = self.execute_query(query, tuple(values), fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"Ошибка при завершении платежа: {e}")
            return None
    
    def get_user_payments_stats(self, user_id: int) -> Dict:
        """
        Получение статистики платежей пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Статистика платежей пользователя
        """
        query = """
            SELECT 
                COUNT(*) as total_payments,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_payments,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_payments,
                SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END) as total_amount,
                SUM(CASE WHEN status = 'completed' THEN tokens ELSE 0 END) as total_tokens
            FROM "Payment"
            WHERE user_id = %s
        """
        
        return self.execute_query(query, (user_id,), fetch_one=True)
    
    def get_pending_payments(self) -> List[Dict]:
        """
        Получение платежей в статусе ожидания
        
        Returns:
            Список платежей в статусе ожидания
        """
        query = """
            SELECT p.*, u.username, u.first_name, u.last_name
            FROM "Payment" p
            JOIN "User" u ON p.user_id = u.user_id
            WHERE p.status = 'pending'
            ORDER BY p.created_at ASC
        """
        
        return self.execute_query(query)
    
    def get_total_revenue(self) -> Dict:
        """
        Получение общей выручки по платежам
        
        Returns:
            Статистика общей выручки
        """
        query = """
            SELECT 
                COUNT(*) as total_payments,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_payments,
                SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END) as total_amount,
                SUM(CASE WHEN status = 'completed' THEN tokens ELSE 0 END) as total_tokens,
                MIN(CASE WHEN status = 'completed' THEN created_at END) as first_payment_date,
                MAX(CASE WHEN status = 'completed' THEN created_at END) as last_payment_date
            FROM "Payment"
        """
        
        return self.execute_query(query, fetch_one=True)
    
    def get_revenue_by_period(self, period_type: str, limit: int = 12) -> List[Dict]:
        """
        Получение выручки по периодам (дни, недели, месяцы)
        
        Args:
            period_type: Тип периода ('day', 'week', 'month')
            limit: Количество периодов
            
        Returns:
            Статистика выручки по периодам
        """
        time_format = {
            'day': 'YYYY-MM-DD',
            'week': 'YYYY-WW',
            'month': 'YYYY-MM'
        }
        
        if period_type not in time_format:
            period_type = 'day'
        
        query = f"""
            SELECT 
                TO_CHAR(created_at, '{time_format[period_type]}') as period,
                COUNT(*) as total_payments,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_payments,
                SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END) as total_amount,
                SUM(CASE WHEN status = 'completed' THEN tokens ELSE 0 END) as total_tokens
            FROM "Payment"
            WHERE created_at >= NOW() - INTERVAL '{limit} {period_type}s'
            GROUP BY period
            ORDER BY period DESC
            LIMIT %s
        """
        
        return self.execute_query(query, (limit,)) 