import psycopg2
from contextlib import contextmanager
from app.config import config
from app.utils.logger import logger

# Глобальное подключение
connection = None


def init_connection():
    """
    Инициализация подключения к PostgreSQL
    """
    global connection
    if connection is None:
        try:
            connection = psycopg2.connect(**config.DB_CONFIG)
            logger.info("Подключение к базе данных успешно установлено.")
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Ошибка подключения к базе данных: {error}")


def close_connection():
    """
    Закрытие подключения к PostgreSQL
    """
    global connection
    if connection is not None:
        connection.close()
        logger.info("Подключение к базе данных закрыто.")
        connection = None


@contextmanager
def get_cursor():
    """
    Контекстный менеджер для курсора.
    Гарантирует commit/rollback и автоматическое закрытие курсора.
    """
    global connection
    if connection is None:
        init_connection()

    cursor = connection.cursor()
    try:
        yield cursor
        connection.commit()
    except Exception as e:
        connection.rollback()
        logger.error(f"Ошибка во время выполнения запроса: {e}")
        raise
    finally:
        cursor.close()
