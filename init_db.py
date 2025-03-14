import sys
import os

# Добавляем текущую директорию в sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импортируем необходимые модули
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.config import DB_URL
from db.models import Base, User, Source, Payment, Message, Action, Admin, Generation, Model, Subscription, AnalyticsEvent

def main():
    print("Инициализация базы данных...")
    
    # Создаем движок и подключение
    engine = create_engine(DB_URL)
    
    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)
    print("Таблицы успешно созданы!")
    
    # Создаем сессию
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Создаем источник регистрации по умолчанию, если его еще нет
        source = db.query(Source).filter(Source.name == "telegram").first()
        if not source:
            print("Создаем источник регистрации по умолчанию...")
            default_source = Source(name="telegram")
            db.add(default_source)
            db.commit()
            print("Источник регистрации 'telegram' успешно создан!")
        else:
            print("Источник регистрации 'telegram' уже существует.")
    except Exception as e:
        print(f"Ошибка при создании источника регистрации: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main() 