import logging
from sqlalchemy.orm import Session
import sys
import os

# Добавляем родительскую директорию в sys.path для импорта из других модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SessionLocal
from db.models import Admin


def get_admin_ids():
    """
    Получает список ID администраторов
    
    Returns:
        list: Список ID администраторов
    """
    with SessionLocal() as db:
        admins = db.query(Admin).all()
        return [admin.user_id for admin in admins]


def is_admin(user_id: int):
    """
    Проверяет, является ли пользователь администратором
    
    Args:
        user_id (int): ID пользователя в Telegram
        
    Returns:
        bool: True, если пользователь является администратором, иначе False
    """
    with SessionLocal() as db:
        admin = db.query(Admin).filter(Admin.user_id == user_id).first()
        return admin is not None


def add_admin(user_id: int):
    """
    Добавляет пользователя в список администраторов
    
    Args:
        user_id (int): ID пользователя в Telegram
        
    Returns:
        bool: True, если операция успешна, иначе False
    """
    with SessionLocal() as db:
        # Проверяем, является ли пользователь уже администратором
        if is_admin(user_id):
            return True
        
        # Добавляем пользователя в список администраторов
        new_admin = Admin(user_id=user_id)
        db.add(new_admin)
        db.commit()
        
        return True


def remove_admin(user_id: int):
    """
    Удаляет пользователя из списка администраторов
    
    Args:
        user_id (int): ID пользователя в Telegram
        
    Returns:
        bool: True, если операция успешна, иначе False
    """
    with SessionLocal() as db:
        admin = db.query(Admin).filter(Admin.user_id == user_id).first()
        
        if not admin:
            return False
        
        db.delete(admin)
        db.commit()
        
        return True 