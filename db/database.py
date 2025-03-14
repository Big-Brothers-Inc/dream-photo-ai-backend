from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sys
import os

# Добавляем родительскую директорию в sys.path для импорта из других модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import DB_URL

# Создаем движок SQLAlchemy для работы с PostgreSQL
engine = create_engine(DB_URL)

# Создаем класс сессии
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создаем базовый класс для моделей
Base = declarative_base()

# Метаданные для работы с таблицами
metadata = MetaData()


def get_db():
    """
    Функция-генератор для получения сессии базы данных
    
    Yields:
        Session: SQLAlchemy сессия для работы с базой данных
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Создаем все таблицы при запуске, если они не существуют
def create_tables():
    """
    Создает все таблицы в базе данных, если они не существуют
    """
    Base.metadata.create_all(bind=engine) 