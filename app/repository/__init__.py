import logging
from typing import Optional, Any, Dict
import os
import dotenv
from .db import BaseRepository
from .user import UserRepository
from .model_repository import ModelRepository
from .generation_repository import GenerationRepository
from .payment_repository import PaymentRepository
from .referral_repository import ReferralRepository
from .admin_repository import AdminRepository

logger = logging.getLogger(__name__)

# Загрузка переменных окружения из .env файла
dotenv.load_dotenv(override=True)

# Проверка статуса DISABLE_DB_CHECK
DISABLE_DB_CHECK = os.getenv("DISABLE_DB_CHECK", "false").lower() in ('true', '1', 't')
print(f"[repository/__init__.py] DISABLE_DB_CHECK из окружения: {os.getenv('DISABLE_DB_CHECK')}")
print(f"[repository/__init__.py] DISABLE_DB_CHECK после обработки: {DISABLE_DB_CHECK}")

# Получение параметров подключения к БД из переменных окружения
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "dream_photo")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_MIN_CONN = int(os.getenv("DB_MIN_CONN", "1"))
DB_MAX_CONN = int(os.getenv("DB_MAX_CONN", "10"))

# Глобальный пул соединений
connection_pool = None

def init_db() -> bool:
    """
    Инициализация подключения к базе данных
    Возвращает True, если инициализация прошла успешно
    """
    global connection_pool
    
    try:
        # Параметры подключения к базе данных
        db_params = {
            'dbname': os.getenv('DB_NAME', 'dream_photo'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres'),
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432')
        }
        
        # Параметры пула соединений
        min_connections = int(os.getenv('DB_MIN_CONN', '1'))
        max_connections = int(os.getenv('DB_MAX_CONN', '10'))
        
        # Инициализация пула соединений
        connection_pool = BaseRepository.initialize_pool(
            dbname=db_params['dbname'],
            user=db_params['user'],
            password=db_params['password'],
            host=db_params['host'],
            port=db_params['port'],
            min_connections=min_connections,
            max_connections=max_connections
        )
        
        logger.info(f"База данных инициализирована: {db_params['dbname']} на {db_params['host']}:{db_params['port']}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при инициализации БД: {e}")
        return False

def close_db() -> bool:
    """
    Закрытие соединения с базой данных
    Возвращает True, если закрытие прошло успешно
    """
    global connection_pool
    
    try:
        if connection_pool:
            connection_pool.closeall()
            connection_pool = None
            logger.info("Соединение с базой данных закрыто")
        return True
    except Exception as e:
        logger.error(f"Ошибка при закрытии соединения с БД: {e}")
        return False

# Функции-фабрики для создания экземпляров репозиториев

def get_user_repository() -> Optional[UserRepository]:
    """Возвращает репозиторий пользователей"""
    try:
        return UserRepository()
    except Exception as e:
        logger.error(f"Ошибка при создании репозитория пользователей: {e}")
        return None

def get_model_repository() -> Optional[ModelRepository]:
    """Возвращает репозиторий моделей"""
    try:
        return ModelRepository()
    except Exception as e:
        logger.error(f"Ошибка при создании репозитория моделей: {e}")
        return None

def get_generation_repository() -> Optional[GenerationRepository]:
    """Возвращает репозиторий генераций"""
    try:
        return GenerationRepository()
    except Exception as e:
        logger.error(f"Ошибка при создании репозитория генераций: {e}")
        return None

def get_payment_repository() -> Optional[PaymentRepository]:
    """Возвращает репозиторий платежей"""
    try:
        return PaymentRepository()
    except Exception as e:
        logger.error(f"Ошибка при создании репозитория платежей: {e}")
        return None

def get_referral_repository() -> Optional[ReferralRepository]:
    """Возвращает репозиторий рефералов"""
    try:
        return ReferralRepository()
    except Exception as e:
        logger.error(f"Ошибка при создании репозитория рефералов: {e}")
        return None

def get_admin_repository() -> Optional[AdminRepository]:
    """Возвращает репозиторий администратора"""
    try:
        return AdminRepository()
    except Exception as e:
        logger.error(f"Ошибка при создании репозитория администратора: {e}")
        return None

__all__ = [
    'BaseRepository',
    'UserRepository',
    'ModelRepository',
    'GenerationRepository',
    'PaymentRepository',
    'ReferralRepository',
    'AdminRepository',
    'init_db',
    'close_db',
    'get_user_repository',
    'get_model_repository',
    'get_generation_repository',
    'get_payment_repository',
    'get_referral_repository',
    'get_admin_repository'
] 