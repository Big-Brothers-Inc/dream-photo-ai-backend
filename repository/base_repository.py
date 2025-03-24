import logging
import psycopg2
import psycopg2.extras
from psycopg2 import pool
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union

# Настройка логирования
logger = logging.getLogger(__name__)

class BaseRepository(ABC):
    """Абстрактный базовый класс для работы с PostgreSQL"""
    
    # Глобальный пул соединений, инициализируется при запуске приложения
    _connection_pool = None
    
    @classmethod
    def initialize_pool(cls, dbname: str, user: str, password: str, host: str, port: str,
                    min_connections: int = 1, max_connections: int = 10) -> pool.ThreadedConnectionPool:
        """
        Инициализирует пул соединений с базой данных
        
        Args:
            dbname: Имя базы данных
            user: Имя пользователя
            password: Пароль
            host: Хост базы данных
            port: Порт
            min_connections: Минимальное количество соединений в пуле
            max_connections: Максимальное количество соединений в пуле
            
        Returns:
            Пул соединений ThreadedConnectionPool
        """
        try:
            cls._connection_pool = pool.ThreadedConnectionPool(
                minconn=min_connections,
                maxconn=max_connections,
                dsn=f"dbname={dbname} user={user} password={password} host={host} port={port}"
            )
            logger.info(f"Пул соединений инициализирован (min={min_connections}, max={max_connections})")
            return cls._connection_pool
        except Exception as e:
            logger.error(f"Ошибка при инициализации пула соединений: {e}")
            raise
    
    @classmethod
    def get_connection(cls):
        """
        Получает соединение из пула
        
        Returns:
            Соединение с базой данных
        
        Raises:
            Exception: Если пул не инициализирован или не удалось получить соединение
        """
        if cls._connection_pool is None:
            logger.error("Пул соединений не инициализирован")
            raise Exception("Пул соединений не инициализирован")
        
        try:
            return cls._connection_pool.getconn()
        except Exception as e:
            logger.error(f"Ошибка при получении соединения из пула: {e}")
            raise
    
    @classmethod
    def release_connection(cls, conn):
        """
        Возвращает соединение в пул
        
        Args:
            conn: Соединение для возврата в пул
        """
        if cls._connection_pool is not None:
            try:
                cls._connection_pool.putconn(conn)
            except Exception as e:
                logger.error(f"Ошибка при возврате соединения в пул: {e}")
    
    # Абстрактные методы, которые должны быть реализованы в дочерних классах
    @abstractmethod
    def get_by_id(self, id_value: Any) -> Optional[Dict[str, Any]]:
        """
        Получение записи по ID
        
        Args:
            id_value: Значение ID
            
        Returns:
            Запись в виде словаря или None, если запись не найдена
        """
        pass
    
    @abstractmethod
    def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Создание новой записи
        
        Args:
            data: Данные для создания записи
            
        Returns:
            Созданная запись в виде словаря или None в случае ошибки
        """
        pass
    
    @abstractmethod
    def update(self, id_value: Any, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Обновление записи
        
        Args:
            id_value: Значение ID записи для обновления
            data: Данные для обновления
            
        Returns:
            Обновленная запись в виде словаря или None в случае ошибки
        """
        pass
    
    @abstractmethod
    def delete(self, id_value: Any) -> bool:
        """
        Удаление записи
        
        Args:
            id_value: Значение ID записи для удаления
            
        Returns:
            True, если запись успешно удалена, иначе False
        """
        pass
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None, fetch_one: bool = False) -> Union[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Выполняет SQL-запрос и возвращает результат в виде списка словарей
        
        Args:
            query: SQL-запрос
            params: Параметры запроса
            fetch_one: Если True, возвращает только первую запись
            
        Returns:
            Список словарей с результатами запроса или одна запись, если fetch_one=True
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, params or {})
                if fetch_one:
                    result = cursor.fetchone()
                    return dict(result) if result else None
                else:
                    result = cursor.fetchall()
                    return list(result)
        except Exception as e:
            logger.error(f"Ошибка при выполнении запроса: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self.release_connection(conn)
    
    def execute_query_single(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Выполняет SQL-запрос и возвращает одну запись
        
        Args:
            query: SQL-запрос
            params: Параметры запроса
            
        Returns:
            Запись в виде словаря или None, если запись не найдена
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, params or {})
                result = cursor.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"Ошибка при выполнении запроса (single): {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self.release_connection(conn)
    
    def execute_query_scalar(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Выполняет SQL-запрос и возвращает скалярное значение
        
        Args:
            query: SQL-запрос
            params: Параметры запроса
            
        Returns:
            Скалярное значение результата запроса
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(query, params or {})
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Ошибка при выполнении запроса (scalar): {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self.release_connection(conn)
    
    def execute_non_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> int:
        """
        Выполняет SQL-запрос без возврата результата (INSERT, UPDATE, DELETE)
        
        Args:
            query: SQL-запрос
            params: Параметры запроса
            
        Returns:
            Количество затронутых строк
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(query, params or {})
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Ошибка при выполнении запроса (non-query): {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self.release_connection(conn)
    
    def execute_batch(self, query: str, params_list: List[Dict[str, Any]]) -> int:
        """
        Выполняет пакетный SQL-запрос
        
        Args:
            query: SQL-запрос
            params_list: Список параметров запроса
            
        Returns:
            Количество обработанных параметров
        """
        if not params_list:
            return 0
            
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                psycopg2.extras.execute_batch(cursor, query, params_list)
                conn.commit()
                return len(params_list)
        except Exception as e:
            logger.error(f"Ошибка при выполнении пакетного запроса: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self.release_connection(conn)
    
    def execute_with_returning(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Выполняет SQL-запрос с RETURNING и возвращает одну запись
        
        Args:
            query: SQL-запрос с RETURNING
            params: Параметры запроса
            
        Returns:
            Запись в виде словаря или None в случае ошибки
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, params or {})
                conn.commit()
                result = cursor.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"Ошибка при выполнении запроса с RETURNING: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self.release_connection(conn)
    
    def execute_transaction(self, queries_with_params: List[Tuple[str, Dict[str, Any]]]) -> bool:
        """
        Выполняет несколько SQL-запросов в одной транзакции
        
        Args:
            queries_with_params: Список кортежей (запрос, параметры)
            
        Returns:
            True, если транзакция выполнена успешно, иначе False
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                for query, params in queries_with_params:
                    cursor.execute(query, params or {})
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка при выполнении транзакции: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self.release_connection(conn) 