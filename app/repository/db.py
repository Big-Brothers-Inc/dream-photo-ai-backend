import psycopg2
import psycopg2.extras
from psycopg2 import pool
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union
from app.config import config
from app.utils.logger import logger


class BaseRepository(ABC):
    _connection_pool = None

    @classmethod
    def initialize_pool(
            cls,
            database: str,
            user: str,
            password: str,
            host: str,
            port: int,
            min_connections: int = 1,
            max_connections: int = 10
    ) -> pool.ThreadedConnectionPool:
        """
        Инициализирует пул соединений с базой данных
        """
        try:
            cls._connection_pool = pool.ThreadedConnectionPool(
                minconn=min_connections,
                maxconn=max_connections,
                dsn=f"dbname={database} user={user} password={password} host={host} port={port}"
            )
            logger.info(f"Пул соединений инициализирован (min={min_connections}, max={max_connections})")
            return cls._connection_pool
        except Exception as e:
            logger.error(f"Ошибка при инициализации пула соединений: {e}")
            raise

    @classmethod
    def get_connection(cls):
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
        if cls._connection_pool is not None:
            try:
                cls._connection_pool.putconn(conn)
            except Exception as e:
                logger.error(f"Ошибка при возврате соединения в пул: {e}")

    @abstractmethod
    def get_by_id(self, id_value: Any) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def update(self, id_value: Any, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def delete(self, id_value: Any) -> bool:
        pass

    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None, fetch_one: bool = False) -> Union[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, params or {})
                if fetch_one:
                    result = cursor.fetchone()
                    return dict(result) if result else None
                else:
                    return list(cursor.fetchall())
        except Exception as e:
            logger.error(f"Ошибка при выполнении запроса: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self.release_connection(conn)

    def execute_query_single(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        return self.execute_query(query, params, fetch_one=True)

    def execute_query_scalar(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
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
