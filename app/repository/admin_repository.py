from typing import Dict, List, Optional, Any, Tuple
import logging
from .db import BaseRepository
import json
import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)

class AdminRepository(BaseRepository):
    """
    Репозиторий для административной части проекта
    """
    
    def get_by_id(self, id_value: Any) -> Optional[Dict[str, Any]]:
        """
        Получение администратора по ID
        
        Args:
            id_value: ID администратора
            
        Returns:
            Данные администратора или None, если не найден
        """
        query = 'SELECT * FROM "User" WHERE user_id = %(id)s AND is_admin = TRUE'
        return self.execute_query_single(query, {"id": id_value})
    
    def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Метод не используется для AdminRepository, но должен быть реализован
        из-за наследования от BaseRepository
        """
        # Админы создаются через обновление обычных пользователей
        logger.warning("Метод create не поддерживается для AdminRepository")
        return None
    
    def update(self, id_value: Any, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Обновление данных администратора
        
        Args:
            id_value: ID администратора
            data: Данные для обновления
            
        Returns:
            Обновленные данные администратора или None в случае ошибки
        """
        # Формируем строку SET для UPDATE
        set_clauses = []
        params = {"id": id_value}
        
        for key, value in data.items():
            set_clauses.append(f"{key} = %({key})s")
            params[key] = value
        
        # Если нет данных для обновления
        if not set_clauses:
            logger.warning("Нет данных для обновления администратора")
            return self.get_by_id(id_value)
        
        set_clause = ", ".join(set_clauses)
        
        query = f'UPDATE "User" SET {set_clause} WHERE user_id = %(id)s AND is_admin = TRUE RETURNING *'
        
        return self.execute_with_returning(query, params)
    
    def delete(self, id_value: Any) -> bool:
        """
        Метод не используется для AdminRepository, но должен быть реализован
        из-за наследования от BaseRepository
        """
        # Администраторы не удаляются, а деактивируются
        logger.warning("Метод delete не поддерживается для AdminRepository, используйте deactivate_admin")
        return False
    
    def log_admin_action(self, admin_id: int, action_type: str, entity_type: str, 
                         entity_id: Optional[int] = None, description: Optional[str] = None) -> Optional[Dict]:
        """
        Логирование административного действия
        
        Args:
            admin_id: ID администратора
            action_type: Тип действия (create, update, delete, etc.)
            entity_type: Тип сущности (user, model, payment, etc.)
            entity_id: ID сущности (опционально)
            description: Описание действия (опционально)
            
        Returns:
            Данные созданной записи или None в случае ошибки
        """
        query = """
            INSERT INTO "AdminAction" 
                (admin_id, action_type, target_table, target_id, details)
            VALUES
                (%s, %s, %s, %s, %s)
            RETURNING *
        """
        
        details = {"description": description} if description else {}
        
        try:
            result = self.execute_query(query, (admin_id, action_type, entity_type, entity_id, json.dumps(details)), fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"Ошибка при логировании административного действия: {e}")
            return None
    
    def get_admin_actions(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Получение истории административных действий
        
        Args:
            limit: Максимальное количество результатов
            offset: Смещение для пагинации
            
        Returns:
            Список административных действий
        """
        query = """
            SELECT a.*, u.username, u.first_name, u.last_name
            FROM "AdminAction" a
            JOIN "User" u ON a.admin_id = u.user_id
            ORDER BY a.created_at DESC
            LIMIT %s OFFSET %s
        """
        return self.execute_query(query, (limit, offset))
    
    def get_admin_actions_by_admin(self, admin_id: int, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Получение истории действий конкретного администратора
        
        Args:
            admin_id: ID администратора
            limit: Максимальное количество результатов
            offset: Смещение для пагинации
            
        Returns:
            Список административных действий
        """
        query = """
            SELECT a.*, u.username, u.first_name, u.last_name
            FROM "AdminAction" a
            JOIN "User" u ON a.admin_id = u.user_id
            WHERE a.admin_id = %s
            ORDER BY a.created_at DESC
            LIMIT %s OFFSET %s
        """
        return self.execute_query(query, (admin_id, limit, offset))
    
    def get_admin_actions_by_entity(self, entity_type: str, entity_id: int, limit: int = 100) -> List[Dict]:
        """
        Получение истории действий над конкретной сущностью
        
        Args:
            entity_type: Тип сущности
            entity_id: ID сущности
            limit: Максимальное количество результатов
            
        Returns:
            Список административных действий
        """
        query = """
            SELECT a.*, u.username, u.first_name, u.last_name
            FROM "AdminAction" a
            JOIN "User" u ON a.admin_id = u.user_id
            WHERE a.entity_type = %s AND a.entity_id = %s
            ORDER BY a.created_at DESC
            LIMIT %s
        """
        return self.execute_query(query, (entity_type, entity_id, limit))
    
    def create_promo_code(self, data: Dict) -> Optional[Dict]:
        """
        Создание нового промо-кода
        
        Args:
            data: Данные промо-кода
            
        Returns:
            Данные созданного промо-кода или None в случае ошибки
        """
        # Формируем список полей и значений для вставки
        fields = []
        placeholders = []
        values = []
        
        # Специальная обработка для valid_to, если оно содержит SQL выражение с INTERVAL
        valid_to_sql = None
        if 'valid_to' in data and isinstance(data['valid_to'], str) and "INTERVAL" in data['valid_to']:
            valid_to_sql = data.pop('valid_to')
        
        for key, value in data.items():
            fields.append(key)
            placeholders.append(f'%s')
            values.append(value)
        
        # Добавляем valid_to с SQL выражением, если оно было
        if valid_to_sql:
            fields.append('valid_to')
            placeholders.append(valid_to_sql)
        
        fields_str = ', '.join(fields)
        placeholders_str = ', '.join(placeholders)
        
        query = f'INSERT INTO "PromoCode" ({fields_str}) VALUES ({placeholders_str}) RETURNING *'
        
        logger.info(f"SQL запрос для создания промо-кода: {query}")
        logger.info(f"Значения: {values}")
        
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, tuple(values))
                result = cursor.fetchone()
                conn.commit()
                logger.info(f"Промо-код успешно создан: {result}")
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"Ошибка при создании промо-кода: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                self.release_connection(conn)
    
    def update_promo_code(self, promo_id: int, data: Dict) -> Optional[Dict]:
        """
        Обновление данных промо-кода
        
        Args:
            promo_id: ID промо-кода
            data: Данные для обновления
            
        Returns:
            Обновленные данные промо-кода или None в случае ошибки
        """
        # Формируем строку SET для UPDATE
        set_values = []
        values = []
        
        for key, value in data.items():
            set_values.append(f'{key} = %s')
            values.append(value)
        
        # Больше не добавляем обновление updated_at
        
        set_str = ', '.join(set_values)
        values.append(promo_id)  # Добавляем ID промо-кода для WHERE
        
        query = f'UPDATE "PromoCode" SET {set_str} WHERE promo_id = %s RETURNING *'
        
        try:
            result = self.execute_query(query, tuple(values), fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"Ошибка при обновлении промо-кода: {e}")
            return None
    
    def delete_promo_code(self, promo_id: int) -> bool:
        """
        Удаление промо-кода
        
        Args:
            promo_id: ID промо-кода
            
        Returns:
            True, если промо-код успешно удален
        """
        query = 'DELETE FROM "PromoCode" WHERE promo_id = %s'
        
        try:
            self.execute_query(query, (promo_id,))
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении промо-кода: {e}")
            return False
    
    def get_promo_code(self, code: str) -> Optional[Dict]:
        """
        Получение промо-кода по значению кода
        
        Args:
            code: Значение промо-кода
            
        Returns:
            Данные промо-кода или None, если промо-код не найден
        """
        query = 'SELECT * FROM "PromoCode" WHERE code = %s'
        return self.execute_query(query, (code,), fetch_one=True)
    
    def get_promo_code_by_id(self, promo_id: int) -> Optional[Dict]:
        """
        Получение промо-кода по ID
        
        Args:
            promo_id: ID промо-кода
            
        Returns:
            Данные промо-кода или None, если промо-код не найден
        """
        query = 'SELECT * FROM "PromoCode" WHERE promo_id = %s'
        return self.execute_query(query, (promo_id,), fetch_one=True)
    
    def get_all_promo_codes(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Получение всех промо-кодов
        
        Args:
            limit: Максимальное количество результатов
            offset: Смещение для пагинации
            
        Returns:
            Список промо-кодов
        """
        query = """
            SELECT p.*, 
                (SELECT COUNT(*) FROM "PromoUsage" pu WHERE pu.promo_id = p.promo_id) as usage_count
            FROM "PromoCode" p
            ORDER BY p.promo_id DESC
            LIMIT %s OFFSET %s
        """
        
        logger.info(f"Выполняется запрос на получение промо-кодов с limit={limit}, offset={offset}")
        
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, (limit, offset))
                results = cursor.fetchall()
                logger.info(f"Найдено промо-кодов: {len(results)}")
                if not results:
                    logger.info("Список промо-кодов пуст")
                else:
                    logger.info(f"Первый промо-код: {results[0]}")
                return list(results)
        except Exception as e:
            logger.error(f"Ошибка при получении списка промо-кодов: {e}")
            return []
        finally:
            if conn:
                self.release_connection(conn)
    
    def get_active_promo_codes(self) -> List[Dict]:
        """
        Получение активных промо-кодов
        
        Returns:
            Список активных промо-кодов
        """
        query = """
            SELECT p.*, 
                (SELECT COUNT(*) FROM "PromoUsage" pu WHERE pu.promo_id = p.promo_id) as usage_count
            FROM "PromoCode" p
            WHERE p.is_active = TRUE
                AND (p.valid_to IS NULL OR p.valid_to > NOW())
                AND (p.max_usages IS NULL OR (SELECT COUNT(*) FROM "PromoUsage" pu WHERE pu.promo_id = p.promo_id) < p.max_usages)
            ORDER BY p.promo_id DESC
        """
        return self.execute_query(query)
    
    def record_promo_usage(self, promo_id: int, user_id: int, tokens_awarded: int) -> Optional[Dict]:
        """
        Запись использования промо-кода пользователем
        
        Args:
            promo_id: ID промо-кода
            user_id: ID пользователя
            tokens_awarded: Количество начисленных токенов
            
        Returns:
            Данные записи использования промо-кода или None в случае ошибки
        """
        query = """
            INSERT INTO "PromoUsage" 
                (promo_id, user_id, tokens_awarded, usage_date)
            VALUES
                (%s, %s, %s, NOW())
            RETURNING *
        """
        
        try:
            result = self.execute_query(query, (promo_id, user_id, tokens_awarded), fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"Ошибка при записи использования промо-кода: {e}")
            return None
    
    def check_promo_usage(self, promo_id: int, user_id: int) -> bool:
        """
        Проверка использования промо-кода пользователем
        
        Args:
            promo_id: ID промо-кода
            user_id: ID пользователя
            
        Returns:
            True, если пользователь уже использовал промо-код
        """
        query = """
            SELECT EXISTS(
                SELECT 1 FROM "PromoUsage"
                WHERE promo_id = %s AND user_id = %s
            ) as used
        """
        result = self.execute_query(query, (promo_id, user_id), fetch_one=True)
        return result.get('used', False) if result else False
    
    def update_system_config(self, key: str, value: Any) -> Optional[Dict]:
        """
        Обновление системной конфигурации
        
        Args:
            key: Ключ конфигурации
            value: Значение конфигурации
            
        Returns:
            Обновленные данные конфигурации или None в случае ошибки
        """
        query = """
            INSERT INTO "SystemConfig" (config_key, config_value)
            VALUES (%s, %s)
            ON CONFLICT (config_key) DO UPDATE
            SET config_value = %s
            RETURNING *
        """
        
        try:
            result = self.execute_query(query, (key, value, value), fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"Ошибка при обновлении системной конфигурации: {e}")
            return None
    
    def get_system_config(self, key: str) -> Optional[Dict]:
        """
        Получение системной конфигурации
        
        Args:
            key: Ключ конфигурации
            
        Returns:
            Данные конфигурации или None, если конфигурация не найдена
        """
        query = 'SELECT * FROM "SystemConfig" WHERE config_key = %s'
        return self.execute_query(query, (key,), fetch_one=True)
    
    def get_all_system_configs(self) -> List[Dict]:
        """
        Получение всех системных конфигураций
        
        Returns:
            Список системных конфигураций
        """
        query = 'SELECT * FROM "SystemConfig" ORDER BY config_key'
        return self.execute_query(query)
    
    def get_system_stats(self) -> Dict:
        """
        Получение системной статистики
        
        Returns:
            Системная статистика
        """
        query = 'SELECT * FROM "GlobalStats" LIMIT 1'
        
        logger.info("Выполняется запрос на получение системной статистики")
        
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query)
                result = cursor.fetchone()
                if result:
                    logger.info(f"Получена статистика системы: {result}")
                    return dict(result)
                else:
                    logger.info("Таблица GlobalStats пуста, создаем начальную запись")
                    # Создаем базовую статистику, если нет записей
                    init_query = """
                        INSERT INTO "GlobalStats" 
                        (total_users, active_users, new_users, total_generations, 
                        total_tokens_spent, total_revenue, total_gifts_sent, total_models_trained)
                        VALUES (0, 0, 0, 0, 0, 0, 0, 0)
                        RETURNING *
                    """
                    cursor.execute(init_query)
                    conn.commit()
                    result = cursor.fetchone()
                    logger.info(f"Создана начальная запись статистики: {result}")
                    return dict(result)
        except Exception as e:
            logger.error(f"Ошибка при получении системной статистики: {e}")
            return {}
        finally:
            if conn:
                self.release_connection(conn)
    
    def update_system_stats(self, data: Dict) -> Optional[Dict]:
        """
        Обновление системной статистики
        
        Args:
            data: Данные для обновления
            
        Returns:
            Обновленные данные статистики или None в случае ошибки
        """
        # Проверяем, существует ли запись
        stats = self.get_system_stats()
        
        logger.info(f"Обновление статистики системы с данными: {data}")
        
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                if stats:
                    # Обновляем существующую запись
                    set_values = []
                    values = []
                    
                    for key, value in data.items():
                        set_values.append(f'{key} = %s')
                        values.append(value)
                    
                    set_str = ', '.join(set_values)
                    
                    query = f'UPDATE "GlobalStats" SET {set_str} RETURNING *'
                    
                    cursor.execute(query, tuple(values))
                else:
                    # Создаем новую запись
                    fields = []
                    placeholders = []
                    values = []
                    
                    for key, value in data.items():
                        fields.append(key)
                        placeholders.append(f'%s')
                        values.append(value)
                    
                    fields_str = ', '.join(fields)
                    placeholders_str = ', '.join(placeholders)
                    
                    query = f'INSERT INTO "GlobalStats" ({fields_str}) VALUES ({placeholders_str}) RETURNING *'
                    
                    cursor.execute(query, tuple(values))
                
                conn.commit()
                result = cursor.fetchone()
                logger.info(f"Статистика успешно обновлена: {result}")
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"Ошибка при обновлении системной статистики: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                self.release_connection(conn) 