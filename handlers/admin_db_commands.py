from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

import logging
import json
import os
from typing import Dict, List, Any, Optional

# Импорт репозиториев
from repository import (
    init_db, close_db, 
    get_user_repository, get_model_repository, 
    get_generation_repository, get_payment_repository,
    get_referral_repository, get_admin_repository
)

# Создаем логгер
logger = logging.getLogger(__name__)

# Создаем роутер для админских команд
admin_router = Router()

# Список ID администраторов из переменной окружения
admin_ids_str = os.getenv("ADMIN_USER_IDS", "")
ADMIN_IDS = [int(id_str) for id_str in admin_ids_str.split(",") if id_str.strip().isdigit()]

logger.info(f"Загружены ID администраторов: {ADMIN_IDS}")

def is_admin(user_id: int) -> bool:
    """
    Проверка, является ли пользователь администратором
    """
    return user_id in ADMIN_IDS

# Фильтр для админских команд
async def admin_filter(message: Message) -> bool:
    return is_admin(message.from_user.id)

# Регистрация модиля админа с фильтром
admin_router.message.filter(admin_filter)

@admin_router.message(Command("init_db"))
async def cmd_init_db(message: Message):
    """
    Инициализация базы данных
    """
    try:
        if init_db():
            await message.answer("✅ База данных успешно инициализирована.")
        else:
            await message.answer("❌ Ошибка при инициализации базы данных.")
    except Exception as e:
        logger.error(f"Ошибка в команде init_db: {e}")
        await message.answer(f"❌ Произошла ошибка: {str(e)}")

@admin_router.message(Command("close_db"))
async def cmd_close_db(message: Message):
    """
    Закрытие соединения с базой данных
    """
    try:
        if close_db():
            await message.answer("✅ Соединение с базой данных закрыто.")
        else:
            await message.answer("❌ Ошибка при закрытии соединения с базой данных.")
    except Exception as e:
        logger.error(f"Ошибка в команде close_db: {e}")
        await message.answer(f"❌ Произошла ошибка: {str(e)}")

@admin_router.message(Command("db_stats"))
async def cmd_db_stats(message: Message):
    """
    Получение общей статистики из базы данных
    """
    try:
        admin_repo = get_admin_repository()
        if admin_repo is None:
            await message.answer("❌ Не удалось получить репозиторий администратора.")
            return
            
        stats = admin_repo.get_system_stats()
        if stats:
            stats_text = "📊 Статистика системы:\n\n"
            stats_text += f"👤 Всего пользователей: {stats.get('total_users', 0)}\n"
            stats_text += f"👥 Активных пользователей: {stats.get('active_users', 0)}\n"
            stats_text += f"🆕 Новых пользователей: {stats.get('new_users', 0)}\n"
            stats_text += f"🖼 Всего генераций: {stats.get('total_generations', 0)}\n"
            stats_text += f"🪙 Всего потрачено токенов: {stats.get('total_tokens_spent', 0)}\n"
            stats_text += f"💰 Общий доход: {stats.get('total_revenue', 0)/100} руб.\n"
            stats_text += f"🎁 Отправлено подарков: {stats.get('total_gifts_sent', 0)}\n"
            stats_text += f"🧠 Обучено моделей: {stats.get('total_models_trained', 0)}\n"
            
            await message.answer(stats_text)
        else:
            await message.answer("❌ Не удалось получить статистику системы.")
    except Exception as e:
        logger.error(f"Ошибка в команде db_stats: {e}")
        await message.answer(f"❌ Произошла ошибка: {str(e)}")

@admin_router.message(Command("get_user"))
async def cmd_get_user(message: Message, command: CommandObject):
    """
    Получение информации о пользователе по ID или имени пользователя
    """
    try:
        if not command.args:
            await message.answer("❌ Укажите ID пользователя или имя пользователя. Например: /get_user 123456789 или /get_user @username")
            return
            
        user_repo = get_user_repository()
        if user_repo is None:
            await message.answer("❌ Не удалось получить репозиторий пользователей.")
            return
            
        arg = command.args.strip()
        user = None
        
        if arg.startswith("@"):
            # Поиск по имени пользователя
            username = arg[1:]
            user = user_repo.get_by_username(username)
        else:
            try:
                # Поиск по ID
                user_id = int(arg)
                user = user_repo.get_by_id(user_id)
            except ValueError:
                await message.answer("❌ Некорректный ID пользователя. Используйте числовой ID или имя пользователя с @.")
                return
                
        if user:
            user_text = "👤 Информация о пользователе:\n\n"
            user_text += f"ID: {user.get('user_id')}\n"
            user_text += f"Имя пользователя: @{user.get('username', 'Нет')}\n"
            user_text += f"Имя: {user.get('first_name', 'Нет')}\n"
            user_text += f"Фамилия: {user.get('last_name', 'Нет')}\n"
            user_text += f"Дата активации: {user.get('activation_date', 'Нет')}\n"
            user_text += f"Токенов: {user.get('tokens_left', 0)}\n"
            user_text += f"Потрачено токенов: {user.get('tokens_spent', 0)}\n"
            user_text += f"Заблокирован: {'Да' if user.get('blocked', False) else 'Нет'}\n"
            user_text += f"Язык: {user.get('language', 'ru')}\n"
            user_text += f"Состояние: {user.get('user_state', 'new')}\n"
            user_text += f"Сгенерировано изображений: {user.get('images_generated', 0)}\n"
            user_text += f"Обучено моделей: {user.get('models_trained', 0)}\n"
            
            # Создаем инлайн-кнопки для действий с пользователем
            builder = InlineKeyboardBuilder()
            builder.button(text="Заблокировать" if not user.get('blocked', False) else "Разблокировать", 
                          callback_data=f"toggle_block_user:{user.get('user_id')}")
            builder.button(text="Добавить токены", callback_data=f"add_tokens:{user.get('user_id')}")
            builder.button(text="Модели пользователя", callback_data=f"user_models:{user.get('user_id')}")
            builder.button(text="Генерации пользователя", callback_data=f"user_generations:{user.get('user_id')}")
            builder.adjust(2)
            
            await message.answer(user_text, reply_markup=builder.as_markup())
        else:
            await message.answer("❌ Пользователь не найден.")
    except Exception as e:
        logger.error(f"Ошибка в команде get_user: {e}")
        await message.answer(f"❌ Произошла ошибка: {str(e)}")

@admin_router.callback_query(lambda c: c.data.startswith("toggle_block_user:"))
async def callback_toggle_block_user(callback: CallbackQuery):
    """
    Блокировка/разблокировка пользователя
    """
    try:
        user_id = int(callback.data.split(":")[1])
        
        user_repo = get_user_repository()
        if user_repo is None:
            await callback.answer("❌ Не удалось получить репозиторий пользователей.")
            return
            
        user = user_repo.get_by_id(user_id)
        if not user:
            await callback.answer("❌ Пользователь не найден.")
            return
            
        # Меняем статус блокировки на противоположный
        blocked = not user.get('blocked', False)
        
        update_data = {
            'blocked': blocked
        }
        
        updated_user = user_repo.update(user_id, update_data)
        if updated_user:
            action = "заблокирован" if blocked else "разблокирован"
            await callback.answer(f"✅ Пользователь {action}.")
            
            # Обновляем информацию о пользователе
            user_text = "👤 Информация о пользователе:\n\n"
            user_text += f"ID: {updated_user.get('user_id')}\n"
            user_text += f"Имя пользователя: @{updated_user.get('username', 'Нет')}\n"
            user_text += f"Имя: {updated_user.get('first_name', 'Нет')}\n"
            user_text += f"Фамилия: {updated_user.get('last_name', 'Нет')}\n"
            user_text += f"Дата активации: {updated_user.get('activation_date', 'Нет')}\n"
            user_text += f"Токенов: {updated_user.get('tokens_left', 0)}\n"
            user_text += f"Потрачено токенов: {updated_user.get('tokens_spent', 0)}\n"
            user_text += f"Заблокирован: {'Да' if updated_user.get('blocked', False) else 'Нет'}\n"
            user_text += f"Язык: {updated_user.get('language', 'ru')}\n"
            user_text += f"Состояние: {updated_user.get('user_state', 'new')}\n"
            user_text += f"Сгенерировано изображений: {updated_user.get('images_generated', 0)}\n"
            user_text += f"Обучено моделей: {updated_user.get('models_trained', 0)}\n"
            
            # Создаем инлайн-кнопки для действий с пользователем
            builder = InlineKeyboardBuilder()
            builder.button(text="Заблокировать" if not updated_user.get('blocked', False) else "Разблокировать", 
                          callback_data=f"toggle_block_user:{updated_user.get('user_id')}")
            builder.button(text="Добавить токены", callback_data=f"add_tokens:{updated_user.get('user_id')}")
            builder.button(text="Модели пользователя", callback_data=f"user_models:{updated_user.get('user_id')}")
            builder.button(text="Генерации пользователя", callback_data=f"user_generations:{updated_user.get('user_id')}")
            builder.adjust(2)
            
            await callback.message.edit_text(user_text, reply_markup=builder.as_markup())
        else:
            await callback.answer("❌ Не удалось обновить данные пользователя.")
    except Exception as e:
        logger.error(f"Ошибка в callback toggle_block_user: {e}")
        await callback.answer(f"❌ Произошла ошибка.")

@admin_router.message(Command("add_tokens"))
async def cmd_add_tokens(message: Message, command: CommandObject):
    """
    Добавление токенов пользователю
    """
    try:
        if not command.args:
            await message.answer("❌ Используйте формат: /add_tokens user_id amount")
            return
            
        args = command.args.strip().split()
        if len(args) != 2:
            await message.answer("❌ Используйте формат: /add_tokens user_id amount")
            return
            
        try:
            user_id = int(args[0])
            amount = int(args[1])
        except ValueError:
            await message.answer("❌ ID пользователя и количество токенов должны быть числами.")
            return
            
        user_repo = get_user_repository()
        if user_repo is None:
            await message.answer("❌ Не удалось получить репозиторий пользователей.")
            return
            
        user = user_repo.get_by_id(user_id)
        if not user:
            await message.answer("❌ Пользователь не найден.")
            return
            
        updated_user = user_repo.update_tokens(user_id, amount)
        if updated_user:
            username = user.get('username', str(user_id))
            await message.answer(f"✅ Пользователю {username} добавлено {amount} токенов.\nТеперь у пользователя {updated_user.get('tokens_left', 0)} токенов.")
            
            # Логируем действие администратора
            admin_repo = get_admin_repository()
            if admin_repo:
                admin_repo.log_admin_action(
                    admin_id=message.from_user.id,
                    action_type="add_tokens",
                    entity_type="user",
                    entity_id=user_id,
                    description=f"Добавлено {amount} токенов"
                )
            
            # Отправляем уведомление пользователю о пополнении баланса
            try:
                bot = message.bot
                notification_text = f"💎 *Пополнение баланса*\n\n"
                notification_text += f"На ваш счет зачислено *{amount} токенов*!\n"
                notification_text += f"Текущий баланс: *{updated_user.get('tokens_left', 0)} токенов*\n\n"
                notification_text += f"Теперь вы можете использовать все возможности бота. Приятного использования!"
                
                await bot.send_message(user_id, notification_text, parse_mode="Markdown")
                logger.info(f"Уведомление о пополнении баланса отправлено пользователю {user_id}")
                
                # После пополнения баланса проверяем, есть ли у пользователя обученная модель
                model_repo = get_model_repository()
                if model_repo is None:
                    logger.error(f"Не удалось получить репозиторий моделей.")
                    return
                
                # Получаем список моделей пользователя в статусе "ready" (обученные и готовые к использованию)
                user_models = model_repo.get_models_by_user(user_id, status="ready")
                
                # Если у пользователя нет обученных моделей, предлагаем создать
                if not user_models:
                    logger.info(f"У пользователя {user_id} нет обученных моделей. Предлагаем обучить модель.")
                    
                    # Создаем сообщение с инструкцией по обучению модели
                    train_message = f"🤖 *Создайте свою персональную модель!*\n\n"
                    train_message += f"Мы заметили, что у вас еще нет обученной модели. "
                    train_message += f"Создайте свою уникальную модель для генерации потрясающих фотографий в вашем стиле!\n\n"
                    train_message += f"Стоимость обучения: *300 токенов*\n\n"
                    
                    # Создаем клавиатуру с кнопкой для запуска обучения модели
                    builder = InlineKeyboardBuilder()
                    builder.button(text="🧠 Обучить модель", callback_data="start_training")
                    builder.button(text="❓ Как выбрать фотографии", callback_data="training_guide")
                    
                    await bot.send_message(user_id, train_message, reply_markup=builder.as_markup(), parse_mode="Markdown")
                    logger.info(f"Пользователю {user_id} отправлено предложение обучить модель")
                
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")
                await message.answer(f"⚠️ Токены добавлены, но не удалось отправить уведомление пользователю: {e}")
        else:
            await message.answer("❌ Не удалось обновить токены пользователя.")
    except Exception as e:
        logger.error(f"Ошибка в команде add_tokens: {e}")
        await message.answer(f"❌ Произошла ошибка: {str(e)}")

@admin_router.message(Command("create_promo"))
async def cmd_create_promo(message: Message, command: CommandObject):
    """
    Создание промокода
    """
    try:
        if not command.args:
            await message.answer("❌ Используйте формат: /create_promo code tokens [expire_days] [max_uses]")
            return
            
        args = command.args.strip().split()
        if len(args) < 2:
            await message.answer("❌ Используйте формат: /create_promo code tokens [expire_days] [max_uses]")
            return
            
        code = args[0].upper()
        
        try:
            tokens = int(args[1])
            expire_days = int(args[2]) if len(args) > 2 else None
            max_uses = int(args[3]) if len(args) > 3 else None
        except ValueError:
            await message.answer("❌ Количество токенов, дней и использований должны быть числами.")
            return
            
        admin_repo = get_admin_repository()
        if admin_repo is None:
            await message.answer("❌ Не удалось получить репозиторий администратора.")
            return
            
        # Проверяем, существует ли промокод
        existing_promo = admin_repo.get_promo_code(code)
        if existing_promo:
            await message.answer(f"❌ Промокод {code} уже существует.")
            return
            
        # Подготавливаем данные для создания промокода
        promo_data = {
            'code': code,
            'tokens_bonus': tokens,
            'is_active': True,
            'created_by': message.from_user.id
        }
        
        if expire_days:
            # Используем SQL-выражение напрямую
            promo_data['valid_to'] = f"NOW() + INTERVAL '{expire_days} days'"
            
        if max_uses:
            promo_data['max_uses'] = max_uses
            
        # Создаем промокод
        new_promo = admin_repo.create_promo_code(promo_data)
        if new_promo:
            promo_text = f"✅ Промокод {code} создан:\n\n"
            promo_text += f"Бонус токенов: {tokens}\n"
            
            if expire_days:
                promo_text += f"Срок действия: {expire_days} дней\n"
                
            if max_uses:
                promo_text += f"Максимальное количество использований: {max_uses}\n"
                
            await message.answer(promo_text)
            
            # Логируем действие администратора
            admin_repo.log_admin_action(
                admin_id=message.from_user.id,
                action_type="create_promo",
                entity_type="promo_code",
                entity_id=new_promo.get('promo_id'),
                description=f"Создан промокод {code} на {tokens} токенов"
            )
        else:
            await message.answer("❌ Не удалось создать промокод.")
    except Exception as e:
        logger.error(f"Ошибка в команде create_promo: {e}")
        await message.answer(f"❌ Произошла ошибка: {str(e)}")

@admin_router.message(Command("get_promos"))
async def cmd_get_promos(message: Message):
    """
    Получение списка промокодов
    """
    try:
        admin_repo = get_admin_repository()
        if admin_repo is None:
            await message.answer("❌ Не удалось получить репозиторий администратора.")
            return
            
        promos = admin_repo.get_all_promo_codes(limit=10)
        if promos:
            promos_text = "🎁 Список промокодов:\n\n"
            
            for promo in promos:
                status = "✅ Активен" if promo.get('is_active', False) else "❌ Неактивен"
                promos_text += f"Код: {promo.get('code')}\n"
                promos_text += f"Статус: {status}\n"
                promos_text += f"Бонус токенов: {promo.get('tokens_bonus', 0)}\n"
                
                # Отображаем текущее количество использований
                promos_text += f"Использований: {promo.get('usage_count', 0)}"
                
                # Отображаем максимальное количество использований, если оно установлено
                if promo.get('max_uses'):
                    promos_text += f"/{promo.get('max_uses')}"
                
                # Добавляем информацию о сроке действия промокода
                valid_to = promo.get('valid_to')
                if valid_to:
                    promos_text += f"\nСрок действия до: {valid_to.strftime('%d.%m.%Y')}"
                else:
                    promos_text += "\nБез ограничения по сроку"
                    
                promos_text += f"\n\n"
                
            await message.answer(promos_text)
        else:
            await message.answer("❌ Промокоды не найдены.")
    except Exception as e:
        logger.error(f"Ошибка в команде get_promos: {e}")
        await message.answer(f"❌ Произошла ошибка: {str(e)}")

@admin_router.message(Command("update_stats"))
async def cmd_update_stats(message: Message):
    """
    Обновление статистики системы на основе актуальных данных из базы
    """
    try:
        admin_repo = get_admin_repository()
        user_repo = get_user_repository()
        model_repo = get_model_repository()
        generation_repo = get_generation_repository()
        payment_repo = get_payment_repository()
        
        if not all([admin_repo, user_repo, model_repo, generation_repo, payment_repo]):
            await message.answer("❌ Не удалось получить один из репозиториев.")
            return
        
        # Получаем актуальные данные
        conn = admin_repo.get_connection()
        try:
            with conn.cursor() as cursor:
                # Общее количество пользователей
                cursor.execute('SELECT COUNT(*) FROM "User"')
                total_users = cursor.fetchone()[0]
                
                # Активные пользователи (активные в последние 30 дней)
                cursor.execute('SELECT COUNT(*) FROM "User" WHERE last_active > NOW() - INTERVAL \'30 days\'')
                active_users = cursor.fetchone()[0]
                
                # Новые пользователи (зарегистрированные в последние 7 дней)
                cursor.execute('SELECT COUNT(*) FROM "User" WHERE activation_date > NOW() - INTERVAL \'7 days\'')
                new_users = cursor.fetchone()[0]
                
                # Всего генераций
                cursor.execute('SELECT COUNT(*) FROM "Generation"')
                total_generations = cursor.fetchone()[0]
                
                # Всего потрачено токенов
                cursor.execute('SELECT COALESCE(SUM(tokens_spent), 0) FROM "User"')
                total_tokens_spent = cursor.fetchone()[0]
                
                # Общий доход
                cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM "Payment" WHERE status = \'completed\'')
                total_revenue = cursor.fetchone()[0]
                
                # Всего отправлено подарков
                cursor.execute('SELECT COUNT(*) FROM "TokenGift"')
                total_gifts_sent = cursor.fetchone()[0]
                
                # Всего обучено моделей
                cursor.execute('SELECT COUNT(*) FROM "Model" WHERE status = \'ready\'')
                total_models_trained = cursor.fetchone()[0]
                
            # Обновляем статистику
            stats_data = {
                'total_users': total_users,
                'active_users': active_users,
                'new_users': new_users,
                'total_generations': total_generations,
                'total_tokens_spent': total_tokens_spent,
                'total_revenue': total_revenue,
                'total_gifts_sent': total_gifts_sent,
                'total_models_trained': total_models_trained
            }
            
            # Обновляем статистику
            updated_stats = admin_repo.update_system_stats(stats_data)
            
            if updated_stats:
                await message.answer("✅ Статистика системы успешно обновлена.")
                
                # Показываем обновленную статистику
                stats_text = "📊 Обновленная статистика системы:\n\n"
                stats_text += f"👤 Всего пользователей: {updated_stats.get('total_users', 0)}\n"
                stats_text += f"👥 Активных пользователей: {updated_stats.get('active_users', 0)}\n"
                stats_text += f"🆕 Новых пользователей: {updated_stats.get('new_users', 0)}\n"
                stats_text += f"🖼 Всего генераций: {updated_stats.get('total_generations', 0)}\n"
                stats_text += f"🪙 Всего потрачено токенов: {updated_stats.get('total_tokens_spent', 0)}\n"
                stats_text += f"💰 Общий доход: {updated_stats.get('total_revenue', 0)/100} руб.\n"
                stats_text += f"🎁 Отправлено подарков: {updated_stats.get('total_gifts_sent', 0)}\n"
                stats_text += f"🧠 Обучено моделей: {updated_stats.get('total_models_trained', 0)}\n"
                
                await message.answer(stats_text)
            else:
                await message.answer("❌ Не удалось обновить статистику системы.")
        except Exception as e:
            logger.error(f"Ошибка при запросе данных для статистики: {e}")
            await message.answer(f"❌ Произошла ошибка при запросе данных: {str(e)}")
        finally:
            admin_repo.release_connection(conn)
            
    except Exception as e:
        logger.error(f"Ошибка в команде update_stats: {e}")
        await message.answer(f"❌ Произошла ошибка: {str(e)}")

@admin_router.message(Command("get_loras"))
async def cmd_get_loras(message: Message):
    """
    Получение списка Extra LoRA моделей
    """
    try:
        admin_repo = get_admin_repository()
        if admin_repo is None:
            await message.answer("❌ Не удалось получить репозиторий администратора.")
            return
            
        # Получаем соединение с базой данных
        conn = admin_repo.get_connection()
        try:
            with conn.cursor() as cursor:
                # Запрос на получение списка LoRA моделей
                cursor.execute('''
                    SELECT * FROM "ExtraLora"
                    ORDER BY extra_lora_id DESC
                    LIMIT 10
                ''')
                loras = cursor.fetchall()
                
                if loras:
                    loras_text = "🧠 Список LoRA моделей:\n\n"
                    
                    for lora in loras:
                        status = "✅ Активна" if lora[8] else "❌ Неактивна"  # is_active
                        loras_text += f"ID: {lora[0]}\n"  # extra_lora_id
                        loras_text += f"Название: {lora[1]}\n"  # name
                        loras_text += f"Описание: {lora[2] or 'Нет описания'}\n"  # description
                        loras_text += f"Триггер: {lora[4]}\n"  # trigger_phrase
                        loras_text += f"Вес: {lora[5]}\n"  # default_weight
                        loras_text += f"Категория: {lora[7] or 'Не указана'}\n"  # category
                        loras_text += f"Статус: {status}\n\n"
                        
                    await message.answer(loras_text)
                else:
                    await message.answer("❌ LoRA модели не найдены.")
        except Exception as e:
            logger.error(f"Ошибка при запросе LoRA моделей: {e}")
            await message.answer(f"❌ Произошла ошибка при запросе данных: {str(e)}")
        finally:
            admin_repo.release_connection(conn)
            
    except Exception as e:
        logger.error(f"Ошибка в команде get_loras: {e}")
        await message.answer(f"❌ Произошла ошибка: {str(e)}")

def setup_admin_handlers(dp):
    """
    Регистрация обработчиков административных команд
    """
    dp.include_router(admin_router) 