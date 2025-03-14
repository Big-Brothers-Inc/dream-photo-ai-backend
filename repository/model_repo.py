import logging
from sqlalchemy.orm import Session
import sys
import os

# Добавляем родительскую директорию в sys.path для импорта из других модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SessionLocal
from db.models import Model


def create_model(user_id: int, name: str, trigger_word: str):
    """
    Создает новую модель
    
    Args:
        user_id (int): ID пользователя в Telegram
        name (str): Название модели
        trigger_word (str): Триггер-слово для модели
        
    Returns:
        int: ID созданной модели
    """
    with SessionLocal() as db:
        new_model = Model(
            user_id=user_id,
            name=name,
            trigger_word=trigger_word,
            status="created"
        )
        
        db.add(new_model)
        db.commit()
        db.refresh(new_model)
        
        return new_model.model_id


def update_model_status(model_id: int, status: str, training_id: str = None):
    """
    Обновляет статус модели
    
    Args:
        model_id (int): ID модели
        status (str): Новый статус (created, training, ready, error)
        training_id (str, optional): ID тренировки в API Replicate
        
    Returns:
        bool: True, если операция успешна, иначе False
    """
    with SessionLocal() as db:
        model = db.query(Model).filter(Model.model_id == model_id).first()
        
        if not model:
            return False
        
        model.status = status
        
        if training_id:
            model.training_id = training_id
            
        db.commit()
        
        return True


def update_model_preview(model_id: int, preview_url: str):
    """
    Обновляет URL превью модели
    
    Args:
        model_id (int): ID модели
        preview_url (str): URL превью
        
    Returns:
        bool: True, если операция успешна, иначе False
    """
    with SessionLocal() as db:
        model = db.query(Model).filter(Model.model_id == model_id).first()
        
        if not model:
            return False
        
        model.preview_url = preview_url
        db.commit()
        
        return True


def get_model(model_id: int):
    """
    Получает модель по ID
    
    Args:
        model_id (int): ID модели
        
    Returns:
        Model: Объект модели или None, если модель не найдена
    """
    with SessionLocal() as db:
        return db.query(Model).filter(Model.model_id == model_id).first()


def get_model_by_training_id(training_id: str):
    """
    Получает модель по ID тренировки
    
    Args:
        training_id (str): ID тренировки в API Replicate
        
    Returns:
        Model: Объект модели или None, если модель не найдена
    """
    with SessionLocal() as db:
        return db.query(Model).filter(Model.training_id == training_id).first()


def get_user_models(user_id: int):
    """
    Получает все модели пользователя
    
    Args:
        user_id (int): ID пользователя в Telegram
        
    Returns:
        list: Список моделей пользователя
    """
    with SessionLocal() as db:
        models = db.query(Model).filter(Model.user_id == user_id).all()
        
        # Преобразуем объекты Model в словари для удобства использования
        result = []
        for model in models:
            result.append({
                "id": model.model_id,
                "name": model.name,
                "trigger_word": model.trigger_word,
                "status": model.status,
                "preview_url": model.preview_url
            })
            
        return result


def delete_model(model_id: int):
    """
    Удаляет модель
    
    Args:
        model_id (int): ID модели
        
    Returns:
        bool: True, если операция успешна, иначе False
    """
    with SessionLocal() as db:
        model = db.query(Model).filter(Model.model_id == model_id).first()
        
        if not model:
            return False
        
        db.delete(model)
        db.commit()
        
        return True 