# Dream Photo Backend

Бэкенд-часть проекта Dream Photo, включающая в себя Telegram бота и FastAPI сервер для обработки запросов от веб-интерфейса.

## Примерная структура проекта
```
dream-photo-ai-backend/
├── run.sh                         # Bash-скрипт для запуска PostgreSQL, FastAPI и бота
├── .env                           # Переменные окружения (не коммитим в репозиторий)
├── .env.example                   # Пример .env для dev-окружения
├── README.md                      # Документация проекта
├── requirements.txt              # Зависимости Python
├── config/
│   └── config.py                 # Pydantic-конфигурация проекта (БД, API, токены и т.д.)
├── app/
│   ├── api/
│   │   ├── app.py                # Инициализация FastAPI-приложения
│   │   ├── lifecycle.py          # Startup / Shutdown события
│   │   ├── middlewares.py        # Middleware для логирования и CORS
│   │   └── routes/
│   │       ├── __init__.py       # Роутер-аггрегатор
│   │       └── health.py         # Эндпоинт проверки /health
│   ├── bot/
│   │   ├── main.py               # Точка входа Telegram-бота
│   │   ├── handlers/
│   │   │   ├── __init__.py       # Регистрация всех хендлеров
│   │   │   ├── commands.py       # /start, /help и др.
│   │   │   └── admin_notifications.py # Уведомления для админов
│   │   └── loader.py             # Инициализация бота, диспетчера и хранилища
│   ├── db/
│   │   ├── db.py                 # Подключение к PostgreSQL и context-managed курсор
│   │   └── schema.sql            # SQL-схема базы данных
│   ├── repository/
│   │   ├── __init__.py           # Инициализация + init_connection
│   │   ├── base_repository.py    # Общая логика запросов
│   │   ├── user_repository.py    # Работа с пользователями
│   │   ├── model_repository.py   # Работа с AI-моделями
│   │   ├── admin_repository.py   # Админ-операции
│   │   ├── payment_repository.py # Работа с платежами
│   │   └── referral_repository.py # Реферальная система
│   ├── utils/
│   │   ├── logger.py             # Конфигурация логирования
│   │   └── training_utils.py     # Вспомогательные функции для обучения
└── tests/                         # (опционально) Тесты
```

## Основные компоненты

### Telegram Бот (main.py)
- Обработка команд пользователей
- Интеграция с системой обучения моделей
- Административные функции
- Система уведомлений
- Логирование действий

### API Сервер (api.py)
- REST API для веб-интерфейса
- CORS настройки
- Эндпоинты для обучения моделей
- Мониторинг состояния
- Интеграция с базой данных

### Обработчики (handlers/)
- **admin_db_commands.py**: Команды для управления базой данных
- **admin_notifications.py**: Система уведомлений администраторов
- **commands.py**: Основные команды бота
- **training_api.py**: API для обучения моделей
- **training_handlers.py**: Логика обучения моделей

### Утилиты (utils/)
- **training_utils.py**: Функции для работы с моделями
- **add_test_loras.py**: Инструменты для тестирования

### База данных (repository/)
- PostgreSQL для хранения данных
- Отдельные репозитории для разных сущностей
- Миграции и схема в schema.sql

## Зависимости

Основные зависимости проекта:
- Python 3.11
- aiogram 3.3.0 (Telegram Bot API)
- FastAPI 0.104.1 (REST API)
- PostgreSQL (База данных)
- Replicate API (Обучение моделей)

## Настройка окружения

1. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Настройте переменные окружения в файле `.env` в корневой директории проекта.

## Запуск

### Telegram бот:
```bash
python main.py
```

### API сервер:
```bash
python app.py
```

## API Эндпоинты

### Основные эндпоинты:
- `GET /`: Проверка работоспособности API
- `GET /health`: Проверка состояния сервера и БД
- `POST /api/train`: Запуск обучения модели
- `GET /api/models`: Получение списка моделей
- `GET /api/user/{user_id}`: Информация о пользователе

## База данных

Backend использует PostgreSQL для хранения всех данных приложения. Взаимодействие с базой данных организовано через паттерн Repository, что обеспечивает абстракцию и инкапсуляцию логики доступа к данным.

### Структура базы данных

База данных включает следующие основные таблицы:

#### Таблица User
```sql
CREATE TABLE IF NOT EXISTS "User" (
    user_id BIGINT PRIMARY KEY,                -- ID пользователя в Telegram
    username VARCHAR(100),                     -- Имя пользователя в Telegram
    first_name VARCHAR(100),                   -- Имя пользователя
    last_name VARCHAR(100),                    -- Фамилия пользователя
    activation_date TIMESTAMP,                 -- Дата активации аккаунта
    tokens_left INTEGER DEFAULT 0,             -- Количество оставшихся токенов для генерации
    tokens_spent INTEGER DEFAULT 0,            -- Общее количество потраченных токенов
    -- другие поля...
);
```
Хранит информацию о пользователях, их токенах, статистику и настройки.

#### Таблица Model
```sql
CREATE TABLE IF NOT EXISTS "Model" (
    model_id SERIAL PRIMARY KEY,               -- Уникальный ID модели
    user_id BIGINT REFERENCES "User"(user_id), -- ID пользователя-владельца модели
    name VARCHAR(100) NOT NULL,                -- Название модели
    trigger_word VARCHAR(50) NOT NULL,         -- Триггер-слово для активации модели
    status VARCHAR(20) DEFAULT 'training',     -- Статус модели (training, ready, error)
    -- другие поля...
);
```
Содержит информацию об обученных моделях пользователей.

#### Таблица Generation
```sql
CREATE TABLE IF NOT EXISTS "Generation" (
    generation_id SERIAL PRIMARY KEY,          -- Уникальный ID генерации
    user_id BIGINT REFERENCES "User"(user_id), -- ID пользователя, запросившего генерацию
    model_id INTEGER REFERENCES "Model"(model_id), -- ID используемой модели
    prompt_text TEXT,                          -- Полный текст промпта
    -- другие поля...
);
```
Хранит историю всех генераций изображений.

#### Таблица Payment
```sql
CREATE TABLE IF NOT EXISTS "Payment" (
    payment_id SERIAL PRIMARY KEY,             -- Уникальный ID платежа
    user_id BIGINT REFERENCES "User"(user_id), -- ID пользователя, сделавшего платеж
    date TIMESTAMP DEFAULT NOW(),              -- Дата и время платежа
    amount INTEGER NOT NULL,                   -- Сумма платежа (в копейках)
    tokens INTEGER NOT NULL,                   -- Количество купленных токенов
    -- другие поля...
);
```
Хранит информацию о платежах пользователей.

#### Таблица ReferralInvite
```sql
CREATE TABLE IF NOT EXISTS "ReferralInvite" (
    invite_id SERIAL PRIMARY KEY,              -- Уникальный ID приглашения
    referrer_id BIGINT REFERENCES "User"(user_id), -- ID пользователя-реферера
    referred_id BIGINT REFERENCES "User"(user_id), -- ID приглашенного пользователя
    -- другие поля...
);
```
Используется для реферальной системы.

### Репозитории

Репозитории организуют доступ к данным в базе и инкапсулируют SQL-запросы.

#### BaseRepository (`base_repository.py`)
Базовый класс для всех репозиториев, содержащий общие методы:
- Подключение к базе данных
- Выполнение транзакций
- Работа с пулом соединений
- Логирование запросов и ошибок

```python
async def execute(self, query, params=None, fetch=False):
    """Выполняет SQL запрос с параметрами."""
    try:
        async with self.pool.acquire() as conn:
            if fetch:
                return await conn.fetch(query, *params) if params else await conn.fetch(query)
            else:
                return await conn.execute(query, *params) if params else await conn.execute(query)
    except Exception as e:
        logging.error(f"Ошибка выполнения запроса: {e}")
        return None
```

#### UserRepository (`user_repository.py`)
Репозиторий для работы с пользователями:
- `get_user(user_id)` - Получение данных пользователя
- `create_user(user_id, username, first_name, last_name)` - Создание нового пользователя
- `update_tokens(user_id, tokens)` - Обновление баланса токенов
- `get_user_statistics(user_id)` - Получение статистики пользователя

Используется в:
- Обработчиках команд бота для проверки пользователя
- API-эндпоинтах для получения информации о пользователе
- Процессе генерации для списания токенов

#### ModelRepository (`model_repository.py`)
Управляет данными о моделях пользователей:
- `create_model(user_id, name, trigger_word)` - Создание новой модели
- `get_user_models(user_id)` - Получение всех моделей пользователя
- `update_model_status(model_id, status)` - Обновление статуса модели
- `get_model_details(model_id)` - Получение детальной информации о модели

Используется в:
- Процессе обучения модели
- API-эндпоинтах для получения списка моделей
- Процессе генерации изображений

#### PaymentRepository (`payment_repository.py`)
Работает с платежами и транзакциями:
- `add_payment(user_id, amount, tokens)` - Добавление нового платежа
- `get_user_payments(user_id)` - Получение истории платежей пользователя
- `calculate_total_revenue()` - Расчет общего дохода

Используется в:
- Обработчиках платежей
- Административных командах для анализа доходов
- Расчете бонусов реферальной программы

#### GenerationRepository (`generation_repository.py`)
Управляет историей генераций:
- `start_generation(user_id, model_id, prompt_text)` - Начало новой генерации
- `finish_generation(generation_id, result_url)` - Завершение генерации
- `get_user_generations(user_id)` - Получение всех генераций пользователя

Используется в:
- Процессе генерации изображений
- API-эндпоинтах для получения истории генераций
- Анализе использования системы

#### ReferralRepository (`referral_repository.py`)
Управляет реферальной системой:
- `create_referral_code(user_id)` - Создание реферального кода
- `process_referral(referrer_id, referred_id)` - Обработка приглашения
- `get_referral_statistics(user_id)` - Получение статистики рефералов

Используется в:
- Процессе регистрации новых пользователей
- Начислении бонусов за рефералов
- Отображении статистики реферальной программы

#### AdminRepository (`admin_repository.py`)
Предоставляет административные функции:
- `get_global_statistics()` - Получение общей статистики системы
- `block_user(user_id)` - Блокировка пользователя
- `manage_extra_lora(lora_data)` - Управление дополнительными моделями

Используется в:
- Административных командах бота
- Панели мониторинга
- Настройке системных параметров

### Схема взаимодействия

1. Контроллер (обработчик команды или API-эндпоинт) получает запрос
2. Контроллер вызывает соответствующий метод репозитория
3. Репозиторий выполняет SQL-запрос к базе данных
4. Результат возвращается контроллеру, который формирует ответ

Пример работы с репозиторием:
```python
# Обработчик команды /balance
async def cmd_balance(message: Message):
    user_id = message.from_user.id
    user_repo = UserRepository()
    user = await user_repo.get_user(user_id)
    
    if user:
        await message.answer(f"Ваш баланс: {user['tokens_left']} токенов")
    else:
        await message.answer("Вы не зарегистрированы. Используйте /start")
```

### Оптимизация производительности

Для обеспечения высокой производительности используются:
- Пул соединений с базой данных для минимизации времени установки соединения
- Индексы для часто используемых полей
- Асинхронное выполнение запросов через asyncpg
- Кэширование часто запрашиваемых данных

### Миграции

Схема базы данных определена в `schema.sql`. При первом запуске приложения происходит инициализация базы данных с полной структурой. Для миграций используется ручной подход с версионированием схемы.

## Логирование

- Логи бота: `bot.log`
- Логи API: `api.log`
- Уровень логирования: INFO

## Безопасность

- Все чувствительные данные хранятся в `.env`
- CORS настройки для API
- Проверка прав администратора
- Валидация входных данных

## Администрирование

Административные команды доступны через Telegram бот:
- `/admin_stats`: Статистика использования
- `/admin_users`: Управление пользователями
- `/admin_models`: Управление моделями
- `/admin_payments`: Информация о платежах

## Мониторинг

- Проверка состояния через `/health`
- Логирование всех действий
- Уведомления администраторов о важных событиях
- Статистика использования ресурсов

Вот **актуализированная версия** инструкции для твоего проекта `dream-photo-ai-backend`, учитывая:

- Новый `run.sh`
- FastAPI + Telegram Bot
- Автоинициализацию PostgreSQL
- Использование `.env`
- Запуск с Python 3.9+ (не только 3.11)

---

## 🚀 Автономный запуск бэкенда

`dream-photo-ai-backend` — это **полноценный автономный сервер**, включающий:

- 🧠 FastAPI API (для фронтенда, генерации, обучения)
- 🤖 Telegram-бота (на базе `aiogram 3.x`)
- 🗃 PostgreSQL базу данных (поднимается локально без Docker)

Вы можете склонировать/скопировать только папку `dream-photo-ai-backend` и запустить её **без frontend или других компонентов**.

---

### 📦 Подготовка к запуску

1. **Склонируйте/скопируйте** папку `dream-photo-ai-backend` на сервер/локальную машину:
   ```bash
   git clone <репозиторий>
   cd dream-photo-ai-backend
   ```

2. **Создайте `.env`** на основе `.env.example`:
   ```bash
   cp .env.example .env
   ```
   Отредактируйте переменные под своё окружение (DB_USER, DB_PASSWORD, BOT_TOKEN и т.д.).

3. **Создайте виртуальное окружение и активируйте его**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. **Установите зависимости**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Сделайте скрипт исполняемым**:
   ```bash
   chmod +x run.sh
   ```

---

### ⚙️ Запуск

#### ✅ Рекомендуемый способ:

```bash
./run.sh
```

Скрипт автоматически:

- Подтянет переменные из `.env`
- Проверит наличие `initdb`, `pg_ctl` и `psql` (через `brew` при необходимости)
- Инициализирует или запустит PostgreSQL
- Создаст роль и базу данных (если не существуют)
- Запустит FastAPI сервер (http://localhost:8000)
- Запустит Telegram-бота

---

### 🛑 Завершение

Нажмите `Ctrl+C`, чтобы остановить:

- FastAPI
- Telegram-бота
- PostgreSQL (если был запущен этим скриптом)

---

### 🔁 Альтернативный ручной запуск (при отладке)

- Запуск FastAPI:
  ```bash
  uvicorn app.api.app:app --host 0.0.0.0 --port 8000
  ```

- Запуск бота:
  ```bash
  python app/bot/main.py
  ```

---

### 📚 Swagger

Swagger-документация будет доступна по адресу:

📎 http://localhost:8000/docs

---

### Особенности автономного запуска

- **Полная независимость** - бэкенд не требует наличия frontend или других компонентов
- Скрипты автоматически создают виртуальное окружение, если оно отсутствует
- Все зависимости устанавливаются автоматически
- Автоматически создается и инициализируется база данных (требуется PostgreSQL)
- Логи API сервера сохраняются в `api.log`
- Логи Telegram бота сохраняются в `bot.log`
- Изменять настройки можно в файле `.env`
- При проблемах с установкой зависимостей используйте `start-py311.sh` (требуется Python 3.11)

### Требования к системе

- Python 3.11 (рекомендуется) или 3.10
- PostgreSQL 12+
- Доступ к интернету для API-интеграций
- Минимум 1GB RAM, рекомендуется 2GB

### Структура директории для автономного запуска

Минимальный набор файлов для автономного запуска:
```
backend/
├── .env                    # Файл с настройками окружения
├── api.py                  # FastAPI сервер
├── main.py                 # Telegram бот
├── requirements.txt        # Зависимости проекта
├── start-py311.sh          # Скрипт запуска через Python 3.11
├── start-server.sh         # Универсальный скрипт запуска
├── start-api.sh            # Скрипт запуска только API
├── start-bot.sh            # Скрипт запуска только бота
├── init_db.sql             # SQL-скрипт для инициализации базы данных
├── handlers/               # Обработчики
├── repository/             # Слой доступа к данным
└── utils/                  # Вспомогательные функции
```

Все остальные файлы и директории вне папки `backend` не требуются для работы бэкенда.
