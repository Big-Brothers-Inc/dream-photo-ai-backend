from typing import Dict, List, Optional, Any, Tuple
import logging
from .db import BaseRepository

logger = logging.getLogger(__name__)


class GenerationRepository(BaseRepository):
    """
    Репозиторий для работы с таблицей генераций изображений
    """
    
    def get_by_id(self, generation_id: int) -> Optional[Dict]:
        """
        Получение генерации по ID
        
        Args:
            generation_id: ID генерации
            
        Returns:
            Данные генерации или None, если генерация не найдена
        """
        query = 'SELECT * FROM "Generation" WHERE generation_id = %s'
        return self.execute_query(query, (generation_id,), fetch_one=True)
    
    def get_by_external_id(self, external_id: str) -> Optional[Dict]:
        """
        Получение генерации по внешнему ID (ID генерации в API)
        
        Args:
            external_id: Внешний ID генерации
            
        Returns:
            Данные генерации или None, если генерация не найдена
        """
        query = 'SELECT * FROM "Generation" WHERE external_id = %s'
        return self.execute_query(query, (external_id,), fetch_one=True)
    
    def get_by_user_id(self, user_id: int, limit: int = 10, offset: int = 0) -> List[Dict]:
        """
        Получение генераций пользователя
        
        Args:
            user_id: ID пользователя
            limit: Максимальное количество результатов
            offset: Смещение для пагинации
            
        Returns:
            Список генераций пользователя
        """
        query = """
            SELECT g.*, m.name as model_name, m.trigger_word
            FROM "Generation" g
            LEFT JOIN "Model" m ON g.model_id = m.model_id
            WHERE g.user_id = %s
            ORDER BY g.created_at DESC
            LIMIT %s OFFSET %s
        """
        return self.execute_query(query, (user_id, limit, offset))
    
    def create(self, data: Dict) -> Optional[Dict]:
        """
        Создание новой записи о генерации
        
        Args:
            data: Данные генерации
            
        Returns:
            Данные созданной генерации или None в случае ошибки
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
        
        query = f'INSERT INTO "Generation" ({fields_str}) VALUES ({placeholders_str}) RETURNING *'
        
        try:
            result = self.execute_query(query, tuple(values), fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"Ошибка при создании записи о генерации: {e}")
            return None
    
    def update(self, generation_id: int, data: Dict) -> Optional[Dict]:
        """
        Обновление данных генерации
        
        Args:
            generation_id: ID генерации
            data: Данные для обновления
            
        Returns:
            Обновленные данные генерации или None в случае ошибки
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
        values.append(generation_id)  # Добавляем ID генерации для WHERE
        
        query = f'UPDATE "Generation" SET {set_str} WHERE generation_id = %s RETURNING *'
        
        try:
            result = self.execute_query(query, tuple(values), fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"Ошибка при обновлении генерации: {e}")
            return None
    
    def delete(self, generation_id: int) -> bool:
        """
        Удаление генерации
        
        Args:
            generation_id: ID генерации
            
        Returns:
            True, если генерация успешно удалена
        """
        query = 'DELETE FROM "Generation" WHERE generation_id = %s'
        
        try:
            self.execute_query(query, (generation_id,))
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении генерации: {e}")
            return False
    
    def update_status(self, generation_id: int, status: str) -> Optional[Dict]:
        """
        Обновление статуса генерации
        
        Args:
            generation_id: ID генерации
            status: Новый статус
            
        Returns:
            Обновленные данные генерации или None в случае ошибки
        """
        query = """
            UPDATE "Generation" 
            SET status = %s, 
                updated_at = NOW() 
            WHERE generation_id = %s 
            RETURNING *
        """
        
        try:
            result = self.execute_query(query, (status, generation_id), fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"Ошибка при обновлении статуса генерации: {e}")
            return None
    
    def update_result(self, generation_id: int, image_url: str, status: str = 'completed') -> Optional[Dict]:
        """
        Обновление результата генерации
        
        Args:
            generation_id: ID генерации
            image_url: URL сгенерированного изображения
            status: Новый статус (по умолчанию 'completed')
            
        Returns:
            Обновленные данные генерации или None в случае ошибки
        """
        query = """
            UPDATE "Generation" 
            SET image_url = %s,
                status = %s,
                completed_at = NOW(),
                updated_at = NOW() 
            WHERE generation_id = %s 
            RETURNING *
        """
        
        try:
            result = self.execute_query(query, (image_url, status, generation_id), fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"Ошибка при обновлении результата генерации: {e}")
            return None
    
    def update_mark(self, generation_id: int, mark: int) -> Optional[Dict]:
        """
        Обновление оценки генерации
        
        Args:
            generation_id: ID генерации
            mark: Оценка (1-5)
            
        Returns:
            Обновленные данные генерации или None в случае ошибки
        """
        query = """
            UPDATE "Generation" 
            SET mark = %s,
                updated_at = NOW() 
            WHERE generation_id = %s 
            RETURNING *
        """
        
        try:
            result = self.execute_query(query, (mark, generation_id), fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"Ошибка при обновлении оценки генерации: {e}")
            return None
    
    def get_generations_in_progress(self) -> List[Dict]:
        """
        Получение генераций, находящихся в процессе
        
        Returns:
            Список генераций в процессе
        """
        query = """
            SELECT g.*, u.username, u.first_name, u.last_name,
                  m.name as model_name, m.trigger_word
            FROM "Generation" g
            JOIN "User" u ON g.user_id = u.user_id
            LEFT JOIN "Model" m ON g.model_id = m.model_id
            WHERE g.status = 'processing'
            ORDER BY g.created_at ASC
        """
        
        return self.execute_query(query)
    
    def get_user_generations_stats(self, user_id: int) -> Dict:
        """
        Получение статистики генераций пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Статистика генераций пользователя
        """
        query = """
            SELECT 
                COUNT(*) as total_generations,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_generations,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_generations,
                AVG(CASE WHEN mark IS NOT NULL THEN mark END) as avg_mark,
                SUM(token_cost) as total_tokens_spent
            FROM "Generation"
            WHERE user_id = %s
        """
        
        return self.execute_query(query, (user_id,), fetch_one=True)
    
    def get_last_generations(self, limit: int = 10) -> List[Dict]:
        """
        Получение последних генераций
        
        Args:
            limit: Максимальное количество результатов
            
        Returns:
            Список последних генераций
        """
        query = """
            SELECT g.*, u.username, u.first_name, u.last_name,
                  m.name as model_name, m.trigger_word
            FROM "Generation" g
            JOIN "User" u ON g.user_id = u.user_id
            LEFT JOIN "Model" m ON g.model_id = m.model_id
            WHERE g.status = 'completed' AND g.image_url IS NOT NULL
            ORDER BY g.created_at DESC
            LIMIT %s
        """
        
        return self.execute_query(query, (limit,))
    
    def get_top_rated_generations(self, limit: int = 10) -> List[Dict]:
        """
        Получение топ генераций по оценкам
        
        Args:
            limit: Максимальное количество результатов
            
        Returns:
            Список топ генераций
        """
        query = """
            SELECT g.*, u.username, u.first_name, u.last_name,
                  m.name as model_name, m.trigger_word
            FROM "Generation" g
            JOIN "User" u ON g.user_id = u.user_id
            LEFT JOIN "Model" m ON g.model_id = m.model_id
            WHERE g.status = 'completed' AND g.image_url IS NOT NULL AND g.mark IS NOT NULL
            ORDER BY g.mark DESC, g.created_at DESC
            LIMIT %s
        """
        
        return self.execute_query(query, (limit,)) 