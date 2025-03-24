-- Скрипт инициализации базы данных dream_photo
-- Автоматически удаляет старые таблицы и создает новые

-- Включаем режим вывода сообщений
\echo 'Инициализация базы данных dream_photo...'

-- Удаляем старые таблицы в правильном порядке (с учетом зависимостей внешних ключей)
-- Сначала выключаем проверку внешних ключей для более быстрого удаления
\echo 'Удаление существующих таблиц...'

-- Отключаем ограничения внешних ключей на время операции
BEGIN;
SET CONSTRAINTS ALL DEFERRED;

-- Удаление таблиц в безопасном порядке
DROP TABLE IF EXISTS "AdminAction" CASCADE;
DROP TABLE IF EXISTS "GlobalStats" CASCADE;
DROP TABLE IF EXISTS "PromoUsage" CASCADE;
DROP TABLE IF EXISTS "PromoCode" CASCADE;
DROP TABLE IF EXISTS "UserJourney" CASCADE;
DROP TABLE IF EXISTS "Generation" CASCADE;
DROP TABLE IF EXISTS "LoraPrompt" CASCADE;
DROP TABLE IF EXISTS "ExtraLora" CASCADE;
DROP TABLE IF EXISTS "Model" CASCADE;
DROP TABLE IF EXISTS "TokenGift" CASCADE;
DROP TABLE IF EXISTS "ReferralInvite" CASCADE;
DROP TABLE IF EXISTS "Payment" CASCADE;
DROP TABLE IF EXISTS "Source" CASCADE;
DROP TABLE IF EXISTS "User" CASCADE;

COMMIT;

\echo 'Существующие таблицы удалены'
\echo 'Создание новых таблиц по схеме...'

-- Создаем новые таблицы по схеме
-- Обновленная таблица пользователей со всеми изменениями
CREATE TABLE IF NOT EXISTS "user" (
    user_id BIGINT PRIMARY KEY,                -- ID пользователя в Telegram
    username VARCHAR(100),                     -- Имя пользователя в Telegram
    first_name VARCHAR(100),                   -- Имя пользователя
    last_name VARCHAR(100),                    -- Фамилия пользователя
    activation_date TIMESTAMP,                 -- Дата активации аккаунта
    tokens_left INTEGER DEFAULT 0,             -- Количество оставшихся токенов для генерации
    blocked BOOLEAN DEFAULT FALSE,             -- Флаг блокировки пользователя
    language VARCHAR(10) DEFAULT 'ru',         -- Предпочитаемый язык пользователя
    last_active TIMESTAMP,                     -- Последняя активность пользователя
    user_state VARCHAR(50) DEFAULT 'new',      -- Текущее состояние/этап пользователя в боте
    images_generated INTEGER DEFAULT 0,        -- Количество сгенерированных изображений
    models_trained INTEGER DEFAULT 0           -- Количество обученных моделей
);

-- Обновленная таблица платежей
CREATE TABLE IF NOT EXISTS "payment" (
    payment_id SERIAL PRIMARY KEY,             -- Уникальный ID платежа
    user_id BIGINT REFERENCES "user"(user_id), -- ID пользователя, сделавшего платеж
    date TIMESTAMP DEFAULT NOW(),              -- Дата и время платежа
    amount INTEGER NOT NULL,                   -- Сумма платежа (в копейках)
    tokens INTEGER NOT NULL,                   -- Количество купленных токенов
    payment_method VARCHAR(50),                -- Метод оплаты
    transaction_id VARCHAR(100),               -- ID транзакции платежной системы
    status VARCHAR(20) DEFAULT 'completed',    -- Статус платежа
    promo_code VARCHAR(50),                    -- Использованный промокод (если есть)
    discount_percent INTEGER DEFAULT 0         -- Процент скидки
);

-- Обновленная таблица реферальных приглашений с добавленными полями
CREATE TABLE IF NOT EXISTS "referral_invite" (
    invite_id SERIAL PRIMARY KEY,              -- Уникальный ID приглашения
    referrer_id BIGINT REFERENCES "user"(user_id), -- ID пользователя-реферера
    referred_id BIGINT REFERENCES "user"(user_id), -- ID приглашенного пользователя
    date TIMESTAMP DEFAULT NOW(),              -- Дата приглашения
    bonus_paid BOOLEAN DEFAULT FALSE,          -- Выплачен ли бонус рефереру
    invite_link VARCHAR(100),                  -- Уникальная ссылка-приглашение
    referral_code VARCHAR(20),                 -- Уникальный реферальный код пользователя
    referral_tokens INTEGER DEFAULT 0          -- Токены, полученные от реферальной программы
);

-- Обновленная таблица моделей
CREATE TABLE IF NOT EXISTS "model" (
    model_id SERIAL PRIMARY KEY,               -- Уникальный ID модели
    user_id BIGINT REFERENCES "user"(user_id), -- ID пользователя-владельца модели
    name VARCHAR(100) NOT NULL,                -- Название модели
    trigger_word VARCHAR(50) NOT NULL,         -- Триггер-слово для активации модели
    status VARCHAR(20) DEFAULT 'training',     -- Статус модели (training, ready, error)
    preview_url TEXT,                          -- URL превью модели
    training_id TEXT,                          -- ID тренировки в Replicate API
    replicate_version TEXT,                    -- Версия модели в Replicate
    model_url TEXT,                            -- Полный URL модели
    created_at TIMESTAMP DEFAULT NOW(),        -- Дата создания модели
    updated_at TIMESTAMP DEFAULT NOW(),        -- Дата последнего обновления
    training_duration INTEGER,                 -- Длительность обучения в секундах
    training_cost INTEGER,                     -- Стоимость обучения в токенах
    model_type VARCHAR(20) DEFAULT 'user'      -- Тип модели (user, system)
);

-- Таблица для тегов LORA
CREATE TABLE IF NOT EXISTS "lora_tag" (
    tag_id SERIAL PRIMARY KEY,                 -- Уникальный ID тега
    name VARCHAR(50) NOT NULL,                 -- Название тега
    description TEXT                           -- Описание тега
);

-- Объединенная таблица LORA (вместо ExtraLora и LoraPrompt)
CREATE TABLE IF NOT EXISTS "lora" (
    lora_id SERIAL PRIMARY KEY,                -- Уникальный ID LORA
    name VARCHAR(100) NOT NULL,                -- Название LORA
    description TEXT,                          -- Описание LORA
    lora_url TEXT NOT NULL,                    -- Ссылка на LORA
    trigger_word VARCHAR(100) NOT NULL,        -- Триггер-слово для LORA
    default_weight DECIMAL(4,2) DEFAULT 1.0,   -- Вес по умолчанию (0.00-1.50)
    prompt_text TEXT,                          -- Текст промпта
    preview_url TEXT,                          -- URL превью LORA
    created_at TIMESTAMP DEFAULT NOW(),        -- Дата создания
    user_id BIGINT REFERENCES "user"(user_id), -- Кто создал (админ)
    is_active BOOLEAN DEFAULT TRUE,            -- Активна ли LORA
    sex BOOLEAN                                -- Пол для генерации (м/ж)
);

-- Таблица для связи LORA с тегами
CREATE TABLE IF NOT EXISTS "lora_tag_relation" (
    relation_id SERIAL PRIMARY KEY,            -- Уникальный ID связи
    lora_id INTEGER REFERENCES "lora"(lora_id), -- ID LORA
    tag_id INTEGER REFERENCES "lora_tag"(tag_id) -- ID тега
);

-- Обновленная таблица генераций
CREATE TABLE IF NOT EXISTS "generation" (
    generation_id SERIAL PRIMARY KEY,          -- Уникальный ID генерации
    user_id BIGINT REFERENCES "user"(user_id), -- ID пользователя, запросившего генерацию
    model_id INTEGER REFERENCES "model"(model_id), -- ID используемой модели
    lora_id INTEGER REFERENCES "lora"(lora_id), -- ID LORA
    prompt_text TEXT,                          -- Полный текст промпта
    lora_scale DECIMAL(4,2),                   -- Фактический вес LoRA, использованный в генерации
    start_date TIMESTAMP DEFAULT NOW(),        -- Дата и время начала генерации
    finish_date TIMESTAMP,                     -- Дата и время завершения генерации
    error_date TIMESTAMP,                      -- Дата и время ошибки (если произошла)
    error_message TEXT,                        -- Сообщение об ошибке
    mark_feedback INTEGER,                     -- Оценка результата пользователем (1-5)
    text_feedback TEXT,                        -- Текстовый отзыв пользователя  
    tokens_spent INTEGER,                      -- Потрачено токенов
    guidance_scale DECIMAL(5,2),               -- Guidance scale (CFG)
    steps INTEGER,                             -- Количество шагов диффузии
    ip_adapter_scale DECIMAL(4,2),             -- Масштаб адаптера изображения (если использовался)
    shared BOOLEAN DEFAULT FALSE,              -- Поделился ли пользователь результатом
    is_error BOOLEAN DEFAULT FALSE,            -- Флаг ошибки
    content_amount INTEGER DEFAULT 1           -- Количество изображений
);

-- Обновленная таблица пути пользователя (упрощенная)
CREATE TABLE IF NOT EXISTS "user_journey" (
    journey_id SERIAL PRIMARY KEY,             -- Уникальный ID записи
    user_id BIGINT REFERENCES "user"(user_id), -- ID пользователя
    event_type VARCHAR(50) NOT NULL,           -- Тип события (registration, first_generation, etc)
    timestamp TIMESTAMP DEFAULT NOW(),         -- Время события
    metadata JSONB                             -- Дополнительные данные о событии
);

-- Таблица для промокодов
CREATE TABLE IF NOT EXISTS "promo_code" (
    promo_id SERIAL PRIMARY KEY,               -- Уникальный ID промокода
    code VARCHAR(50) NOT NULL UNIQUE,          -- Код промокода
    discount_percent INTEGER,                  -- Процент скидки
    tokens_bonus INTEGER,                      -- Бонусные токены
    valid_from TIMESTAMP DEFAULT NOW(),        -- Начало действия
    valid_to TIMESTAMP,                        -- Окончание действия
    max_usages INTEGER,                        -- Максимальное количество использований
    created_by BIGINT REFERENCES "user"(user_id), -- Кто создал
    is_active BOOLEAN DEFAULT TRUE             -- Активен ли промокод
);

-- Таблица использования промокодов
CREATE TABLE IF NOT EXISTS "promo_usage" (
    usage_id SERIAL PRIMARY KEY,               -- Уникальный ID использования
    promo_id INTEGER REFERENCES "promo_code"(promo_id), -- ID промокода
    user_id BIGINT REFERENCES "user"(user_id), -- ID пользователя
    used_at TIMESTAMP DEFAULT NOW(),           -- Время использования
    payment_id INTEGER REFERENCES "payment"(payment_id) -- Связанный платеж (если есть)
);

-- Дополнительные индексы для оптимизации запросов
CREATE INDEX idx_user_username ON "user"(username);
CREATE INDEX idx_payment_date ON "payment"(date);
CREATE INDEX idx_generation_lora_id ON "generation"(lora_id);
CREATE INDEX idx_generation_finish_date ON "generation"(finish_date);
CREATE INDEX idx_generation_is_error ON "generation"(is_error);
CREATE INDEX idx_model_replicate_version ON "model"(replicate_version);
CREATE INDEX idx_lora_tag_relation_lora_id ON "lora_tag_relation"(lora_id);
CREATE INDEX idx_lora_tag_relation_tag_id ON "lora_tag_relation"(tag_id);
CREATE INDEX idx_user_journey_user_id ON "user_journey"(user_id);
CREATE INDEX idx_user_journey_event_type ON "user_journey"(event_type);
CREATE INDEX idx_promo_usage_user_id ON "promo_usage"(user_id);
CREATE INDEX idx_referral_invite_referrer_id ON "referral_invite"(referrer_id);
CREATE INDEX idx_referral_invite_referred_id ON "referral_invite"(referred_id);

-- Тестовый пользователь-администратор 
\echo 'Добавляю тестового пользователя-администратора...'
INSERT INTO "user" (user_id, username, first_name, last_name, activation_date, tokens_left)
VALUES (63196679, 'serzhbigulov', 'Serzh', 'Bigulov', NOW(), 1000)
ON CONFLICT (user_id) DO UPDATE 
SET tokens_left = "user".tokens_left + 1000, 
    username = 'serzhbigulov', 
    first_name = 'Serzh', 
    last_name = 'Bigulov';

\echo 'База данных успешно инициализирована!'
