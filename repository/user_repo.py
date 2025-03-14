import logging
import uuid
from sqlalchemy.orm import Session
import sys
import os

# Добавляем родительскую директорию в sys.path для импорта из других модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SessionLocal
from db.models import User


def get_user(user_id: int):
    """
    Получает пользователя по ID
    
    Args:
        user_id (int): ID пользователя в Telegram
        
    Returns:
        User: Объект пользователя или None, если пользователь не найден
    """
    with SessionLocal() as db:
        return db.query(User).filter(User.user_id == user_id).first()


def create_user(user_id: int, username: str = None):
    """
    Создает нового пользователя
    
    Args:
        user_id (int): ID пользователя в Telegram
        username (str, optional): Имя пользователя
        
    Returns:
        User: Созданный объект пользователя
    """
    # Генерируем уникальный реферальный код
    referral_code = f"ref_{uuid.uuid4().hex[:8]}"
    
    with SessionLocal() as db:
        # Проверяем, существует ли пользователь
        existing_user = db.query(User).filter(User.user_id == user_id).first()
        
        if existing_user:
            return existing_user
        
        # Создаем нового пользователя
        new_user = User(
            user_id=user_id,
            tokens_left=0,
            referral_code=referral_code
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user


def update_user_tokens(user_id: int, tokens: int):
    """
    Обновляет количество токенов пользователя
    
    Args:
        user_id (int): ID пользователя в Telegram
        tokens (int): Количество токенов (может быть отрицательным для списания)
        
    Returns:
        bool: True, если операция успешна, иначе False
    """
    with SessionLocal() as db:
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return False
        
        user.tokens_left += tokens
        
        # Убеждаемся, что количество токенов не стало отрицательным
        if user.tokens_left < 0:
            user.tokens_left = 0
            
        db.commit()
        
        return True


def get_user_tokens(user_id: int):
    """
    Получает количество токенов пользователя
    
    Args:
        user_id (int): ID пользователя в Telegram
        
    Returns:
        int: Количество токенов или 0, если пользователь не найден
    """
    with SessionLocal() as db:
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return 0
        
        return user.tokens_left


def update_user_language(user_id: int, language: str):
    """
    Обновляет язык пользователя
    
    Args:
        user_id (int): ID пользователя в Telegram
        language (str): Код языка (например, "ru", "en")
        
    Returns:
        bool: True, если операция успешна, иначе False
    """
    with SessionLocal() as db:
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return False
        
        user.language = language
        db.commit()
        
        return True


def block_user(user_id: int, blocked: bool = True):
    """
    Блокирует или разблокирует пользователя
    
    Args:
        user_id (int): ID пользователя в Telegram
        blocked (bool, optional): Статус блокировки. По умолчанию True.
        
    Returns:
        bool: True, если операция успешна, иначе False
    """
    with SessionLocal() as db:
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return False
        
        user.blocked = blocked
        db.commit()
        
        return True


def is_user_blocked(user_id: int):
    """
    Проверяет, заблокирован ли пользователь
    
    Args:
        user_id (int): ID пользователя в Telegram
        
    Returns:
        bool: True, если пользователь заблокирован, иначе False
    """
    with SessionLocal() as db:
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return False
        
        return user.blocked 