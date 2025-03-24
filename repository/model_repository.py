from typing import Dict, List, Optional, Any, Tuple
import logging
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)

class ModelRepository(BaseRepository):
    """
    Репозиторий для работы с таблицей моделей
    """
    
    def get_by_id(self, model_id: int) -> Optional[Dict]:
        """
        Получение модели по ID
        
        Args:
            model_id: ID модели
            
        Returns:
            Данные модели или None, если модель не найдена
        """
        query = 'SELECT * FROM "Model" WHERE model_id = %s'
        return self.execute_query(query, (model_id,), fetch_one=True)
    
    def get_by_training_id(self, training_id: str) -> Optional[Dict]:
        """
        Получение модели по ID тренировки в Replicate API
        
        Args:
            training_id: ID тренировки в Replicate API
            
        Returns:
            Данные модели или None, если модель не найдена
        """
        query = 'SELECT * FROM "Model" WHERE training_id = %s'
        return self.execute_query(query, (training_id,), fetch_one=True)
    
    def get_by_user_id(self, user_id: int) -> List[Dict]:
        """
        Получение моделей пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Список моделей пользователя
        """
        query = 'SELECT * FROM "Model" WHERE user_id = %s ORDER BY created_at DESC'
        return self.execute_query(query, (user_id,))
    
    def get_ready_models_by_user_id(self, user_id: int) -> List[Dict]:
        """
        Получение готовых моделей пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Список готовых моделей пользователя
        """
        query = 'SELECT * FROM "Model" WHERE user_id = %s AND status = %s ORDER BY created_at DESC'
        return self.execute_query(query, (user_id, 'ready'))
    
    def create(self, data: Dict) -> Optional[Dict]:
        """
        Создание новой модели
        
        Args:
            data: Данные модели
            
        Returns:
            Данные созданной модели или None в случае ошибки
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
        
        query = f'INSERT INTO "Model" ({fields_str}) VALUES ({placeholders_str}) RETURNING *'
        
        try:
            result = self.execute_query(query, tuple(values), fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"Ошибка при создании модели: {e}")
            return None
    
    def update(self, model_id: int, data: Dict) -> Optional[Dict]:
        """
        Обновление данных модели
        
        Args:
            model_id: ID модели
            data: Данные для обновления
            
        Returns:
            Обновленные данные модели или None в случае ошибки
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
        values.append(model_id)  # Добавляем ID модели для WHERE
        
        query = f'UPDATE "Model" SET {set_str} WHERE model_id = %s RETURNING *'
        
        try:
            result = self.execute_query(query, tuple(values), fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"Ошибка при обновлении модели: {e}")
            return None
    
    def delete(self, model_id: int) -> bool:
        """
        Удаление модели
        
        Args:
            model_id: ID модели
            
        Returns:
            True, если модель успешно удалена
        """
        query = 'DELETE FROM "Model" WHERE model_id = %s'
        
        try:
            self.execute_query(query, (model_id,))
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении модели: {e}")
            return False
    
    def update_status(self, model_id: int, status: str) -> Optional[Dict]:
        """
        Обновление статуса модели
        
        Args:
            model_id: ID модели
            status: Новый статус
            
        Returns:
            Обновленные данные модели или None в случае ошибки
        """
        query = """
            UPDATE "Model" 
            SET status = %s, 
                updated_at = NOW() 
            WHERE model_id = %s 
            RETURNING *
        """
        
        try:
            result = self.execute_query(query, (status, model_id), fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"Ошибка при обновлении статуса модели: {e}")
            return None
    
    def increment_usage_count(self, model_id: int) -> Optional[Dict]:
        """
        Увеличение счетчика использования модели
        
        Args:
            model_id: ID модели
            
        Returns:
            Обновленные данные модели или None в случае ошибки
        """
        query = """
            UPDATE "Model" 
            SET usage_count = usage_count + 1, 
                updated_at = NOW() 
            WHERE model_id = %s 
            RETURNING *
        """
        
        try:
            result = self.execute_query(query, (model_id,), fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"Ошибка при обновлении счетчика использования модели: {e}")
            return None
    
    def get_public_models(self, limit: int = 10, offset: int = 0) -> List[Dict]:
        """
        Получение публичных моделей
        
        Args:
            limit: Максимальное количество результатов
            offset: Смещение для пагинации
            
        Returns:
            Список публичных моделей
        """
        query = """
            SELECT m.*, u.username, u.first_name, u.last_name
            FROM "Model" m
            JOIN "User" u ON m.user_id = u.user_id
            WHERE m.is_public = TRUE AND m.status = 'ready'
            ORDER BY m.usage_count DESC, m.created_at DESC
            LIMIT %s OFFSET %s
        """
        
        return self.execute_query(query, (limit, offset))
    
    def get_top_models(self, limit: int = 10) -> List[Dict]:
        """
        Получение топ моделей по частоте использования
        
        Args:
            limit: Максимальное количество результатов
            
        Returns:
            Список топ моделей
        """
        query = """
            SELECT m.*, u.username, u.first_name, u.last_name,
                   COUNT(g.generation_id) as generation_count,
                   AVG(CASE WHEN g.mark IS NOT NULL THEN g.mark ELSE NULL END) as avg_rating
            FROM "Model" m
            JOIN "User" u ON m.user_id = u.user_id
            LEFT JOIN "Generation" g ON m.model_id = g.model_id
            WHERE m.status = 'ready'
            GROUP BY m.model_id, u.username, u.first_name, u.last_name
            ORDER BY m.usage_count DESC, avg_rating DESC NULLS LAST
            LIMIT %s
        """
        
        return self.execute_query(query, (limit,))
    
    def search_models(self, search_term: str, limit: int = 10) -> List[Dict]:
        """
        Поиск моделей по имени или описанию
        
        Args:
            search_term: Поисковый запрос
            limit: Максимальное количество результатов
            
        Returns:
            Список найденных моделей
        """
        search_pattern = f"%{search_term}%"
        query = """
            SELECT m.*, u.username, u.first_name, u.last_name
            FROM "Model" m
            JOIN "User" u ON m.user_id = u.user_id
            WHERE (m.name ILIKE %s OR m.trigger_word ILIKE %s) AND m.status = 'ready'
            ORDER BY m.usage_count DESC, m.created_at DESC
            LIMIT %s
        """
        
        return self.execute_query(query, (search_pattern, search_pattern, limit))
    
    def get_models_in_training(self) -> List[Dict]:
        """
        Получение моделей, находящихся в процессе обучения
        
        Returns:
            Список моделей в процессе обучения
        """
        query = """
            SELECT m.*, u.username, u.first_name, u.last_name
            FROM "Model" m
            JOIN "User" u ON m.user_id = u.user_id
            WHERE m.status = 'training'
            ORDER BY m.created_at ASC
        """
        
        return self.execute_query(query)
    
    def update_training_info(self, model_id: int, training_duration: int, training_cost: int) -> Optional[Dict]:
        """
        Обновление информации об обучении модели
        
        Args:
            model_id: ID модели
            training_duration: Длительность обучения в секундах
            training_cost: Стоимость обучения в токенах
            
        Returns:
            Обновленные данные модели или None в случае ошибки
        """
        query = """
            UPDATE "Model" 
            SET training_duration = %s, 
                training_cost = %s,
                updated_at = NOW() 
            WHERE model_id = %s 
            RETURNING *
        """
        
        try:
            result = self.execute_query(query, (training_duration, training_cost, model_id), fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"Ошибка при обновлении информации об обучении модели: {e}")
            return None
    
    def get_models_by_user(self, user_id: int, status: str = None) -> List[Dict]:
        """
        Получает список моделей пользователя, опционально фильтруя по статусу
        
        Args:
            user_id: ID пользователя
            status: Статус модели (например, 'ready', 'training', 'failed')
            
        Returns:
            List[Dict]: Список моделей пользователя
        """
        try:
            conn = self.get_connection()
            try:
                with conn.cursor() as cursor:
                    query = 'SELECT * FROM "Model" WHERE user_id = %s'
                    params = [user_id]
                    
                    if status:
                        query += ' AND status = %s'
                        params.append(status)
                        
                    query += ' ORDER BY created_at DESC'
                    
                    cursor.execute(query, params)
                    models = cursor.fetchall()
                    
                    if not models:
                        self.logger.info(f"Модели пользователя {user_id} не найдены" + 
                                        (f" со статусом '{status}'" if status else ""))
                        return []
                    
                    result = []
                    for model in models:
                        result.append({
                            'model_id': model[0],
                            'user_id': model[1],
                            'name': model[2],
                            'description': model[3],
                            'status': model[4],
                            'created_at': model[5],
                            'updated_at': model[6],
                            'model_type': model[7],
                            'image_count': model[8],
                            'training_params': model[9],
                            'model_path': model[10] if len(model) > 10 else None,
                            'preview_url': model[11] if len(model) > 11 else None
                        })
                    
                    self.logger.info(f"Найдено {len(result)} моделей пользователя {user_id}" + 
                                   (f" со статусом '{status}'" if status else ""))
                    return result
            finally:
                self.release_connection(conn)
        except Exception as e:
            self.logger.error(f"Ошибка при получении моделей пользователя {user_id}: {e}")
            return [] 