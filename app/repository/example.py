#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Пример использования репозиториев для работы с БД
"""

import logging
import sys
from typing import Optional, Dict, List

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Импорт репозиториев
from . import (
    init_db, close_db, 
    get_user_repository, get_model_repository, 
    get_generation_repository, get_payment_repository,
    get_referral_repository, get_admin_repository
)

def example_users():
    """
    Пример работы с репозиторием пользователей
    """
    logger.info("Пример работы с репозиторием пользователей")
    
    # Получаем репозиторий пользователей
    user_repo = get_user_repository()
    if user_repo is None:
        logger.error("Не удалось получить репозиторий пользователей")
        return
    
    # Пример создания пользователя
    user_data = {
        'user_id': 123456789,
        'username': 'example_user',
        'first_name': 'Иван',
        'last_name': 'Иванов',
        'language_code': 'ru',
        'is_active': True,
        'is_premium': False,
        'tokens': 100,
        'source_id': 1
    }
    
    try:
        new_user = user_repo.create(user_data)
        if new_user:
            logger.info(f"Пользователь создан: {new_user}")
        
        # Получение пользователя по ID
        user = user_repo.get_by_id(123456789)
        if user:
            logger.info(f"Получен пользователь: {user}")
        
        # Обновление пользователя
        update_data = {
            'tokens': 200,
            'is_premium': True
        }
        updated_user = user_repo.update(123456789, update_data)
        if updated_user:
            logger.info(f"Пользователь обновлен: {updated_user}")
        
        # Удаление пользователя
        if user_repo.delete(123456789):
            logger.info(f"Пользователь удален: 123456789")
    except Exception as e:
        logger.error(f"Ошибка при работе с репозиторием пользователей: {e}")

def example_models():
    """
    Пример работы с репозиторием моделей
    """
    logger.info("Пример работы с репозиторием моделей")
    
    # Получаем репозиторий моделей
    model_repo = get_model_repository()
    if model_repo is None:
        logger.error("Не удалось получить репозиторий моделей")
        return
    
    # Пример создания модели
    model_data = {
        'user_id': 123456789,
        'name': 'Пример модели',
        'trigger_word': 'example_model',
        'status': 'training',
        'training_id': 'tr-123456',
        'is_public': True
    }
    
    try:
        new_model = model_repo.create(model_data)
        if new_model:
            logger.info(f"Модель создана: {new_model}")
            model_id = new_model.get('model_id')
            
            # Обновление статуса модели
            updated_model = model_repo.update_status(model_id, 'ready')
            if updated_model:
                logger.info(f"Статус модели обновлен: {updated_model}")
            
            # Увеличение счетчика использования
            updated_model = model_repo.increment_usage_count(model_id)
            if updated_model:
                logger.info(f"Счетчик использования модели обновлен: {updated_model}")
            
            # Получение моделей пользователя
            user_models = model_repo.get_by_user_id(123456789)
            logger.info(f"Модели пользователя: {user_models}")
            
            # Удаление модели
            if model_repo.delete(model_id):
                logger.info(f"Модель удалена: {model_id}")
    except Exception as e:
        logger.error(f"Ошибка при работе с репозиторием моделей: {e}")

def main():
    """
    Основная функция примера
    """
    logger.info("Запуск примера использования репозиториев")
    
    # Инициализация базы данных
    if not init_db():
        logger.error("Не удалось инициализировать базу данных")
        return
    
    # Примеры работы с репозиториями
    example_users()
    example_models()
    
    # Закрытие соединения с базой данных
    close_db()
    
    logger.info("Пример использования репозиториев завершен")

if __name__ == "__main__":
    main() 