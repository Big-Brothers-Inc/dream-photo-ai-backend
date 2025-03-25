
-- Удаление таблиц в безопасном порядке
DROP TABLE IF EXISTS "promo_usage" CASCADE;
DROP TABLE IF EXISTS "user_journey" CASCADE;
DROP TABLE IF EXISTS "admin_actions" CASCADE;
DROP TABLE IF EXISTS "admin" CASCADE;
DROP TABLE IF EXISTS "generation" CASCADE;
DROP TABLE IF EXISTS "lora_tag_relation" CASCADE;
DROP TABLE IF EXISTS "lora" CASCADE;
DROP TABLE IF EXISTS "lora_tag" CASCADE;
DROP TABLE IF EXISTS "model" CASCADE;
DROP TABLE IF EXISTS "referral_invite" CASCADE;
DROP TABLE IF EXISTS "enrollment" CASCADE;
DROP TABLE IF EXISTS "payment" CASCADE;
DROP TABLE IF EXISTS "promo_code" CASCADE;
DROP TABLE IF EXISTS "user" CASCADE;


CREATE TABLE IF NOT EXISTS "user" (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    activation_dttm TIMESTAMP,
    tokens_left INTEGER DEFAULT 0,
    blocked BOOLEAN DEFAULT FALSE,
    language VARCHAR(10) DEFAULT 'ru',
    last_active TIMESTAMP,
    user_state VARCHAR(50) DEFAULT 'NEW'
);


CREATE TABLE IF NOT EXISTS "promo_code" (
    promo_id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    discount_percent INTEGER,
    tokens_amount INTEGER,
    valid_from TIMESTAMP DEFAULT NOW(),
    valid_to TIMESTAMP,
    max_usages INTEGER,
    created_by BIGINT REFERENCES "user"(user_id),
    is_active BOOLEAN DEFAULT TRUE
);


CREATE TABLE IF NOT EXISTS "payment" (
    payment_id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES "user"(user_id),
    payment_dttm TIMESTAMP DEFAULT NOW(),
    amount INTEGER NOT NULL,
    tokens INTEGER NOT NULL,
    payment_method VARCHAR(50),
    transaction_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'completed',
    promo_id BIGINT REFERENCES "promo_code"(promo_id)
);


CREATE TABLE IF NOT EXISTS "enrollment" (
    enrollment_id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES "user"(user_id),
    payment_id BIGINT REFERENCES "payment"(payment_id),
    promo_id BIGINT REFERENCES "promo_code"(promo_id),
    enrollment_dttm TIMESTAMP DEFAULT NOW(),
    amount INTEGER NOT NULL
);


CREATE TABLE IF NOT EXISTS "referral_invite" (
    invite_id SERIAL PRIMARY KEY,
    referrer_id BIGINT REFERENCES "user"(user_id),
    referred_id BIGINT REFERENCES "user"(user_id),
    invite_dttm TIMESTAMP DEFAULT NOW(),
    bonus_paid BOOLEAN DEFAULT FALSE,
    invite_link VARCHAR(100),
    referral_code VARCHAR(20),
    referral_tokens INTEGER DEFAULT 0
);


CREATE TABLE IF NOT EXISTS "model" (
    model_id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES "user"(user_id),
    name VARCHAR(100) NOT NULL,
    trigger_word VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'training',
    preview_url TEXT,
    training_id TEXT,
    replicate_version TEXT,
    model_url TEXT,
    create_dttm TIMESTAMP DEFAULT NOW(),
    update_dttm TIMESTAMP DEFAULT NOW(),
    training_duration INTEGER,
    training_cost INTEGER,
    model_type VARCHAR(20) DEFAULT 'user'
);


CREATE TABLE IF NOT EXISTS "lora_tag" (
    tag_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT
);


CREATE TABLE IF NOT EXISTS "lora" (
    lora_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    lora_url TEXT NOT NULL,
    trigger_word VARCHAR(100) NOT NULL,
    default_weight DECIMAL(4,2) DEFAULT 1.0,
    prompt_text TEXT,
    preview_url TEXT,
    create_dttm TIMESTAMP DEFAULT NOW(),
    user_id BIGINT REFERENCES "user"(user_id),
    is_active BOOLEAN DEFAULT TRUE,
    sex BOOLEAN
);


CREATE TABLE IF NOT EXISTS "admin" (
    admin_id BIGINT PRIMARY KEY,
    user_id BIGINT REFERENCES "user"(user_id),
    status VARCHAR(20) DEFAULT 'ACTIVE'
);


CREATE TABLE IF NOT EXISTS "admin_actions" (
    action_id BIGINT PRIMARY KEY,
    admin_id BIGINT REFERENCES "user"(user_id),
    action VARCHAR(20),
    user_id BIGINT REFERENCES "user"(user_id),
    lora_id BIGINT REFERENCES "lora"(lora_id)
);


CREATE TABLE IF NOT EXISTS "lora_tag_relation" (
    relation_id SERIAL PRIMARY KEY,
    lora_id INTEGER REFERENCES "lora"(lora_id),
    tag_id INTEGER REFERENCES "lora_tag"(tag_id)
);


CREATE TABLE IF NOT EXISTS "generation" (
    generation_id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES "user"(user_id),
    model_id INTEGER REFERENCES "model"(model_id),
    lora_id INTEGER REFERENCES "lora"(lora_id),
    prompt_text TEXT,
    lora_scale DECIMAL(4,2),
    start_dttm TIMESTAMP DEFAULT NOW(),
    finish_dttm TIMESTAMP,
    error_dttm TIMESTAMP,
    error_message TEXT,
    mark_feedback INTEGER,
    text_feedback TEXT,
    tokens_spent INTEGER,
    guidance_scale DECIMAL(5,2),
    steps INTEGER,
    ip_adapter_scale DECIMAL(4,2),
    shared BOOLEAN DEFAULT FALSE,
    is_error BOOLEAN DEFAULT FALSE,
    content_amount INTEGER DEFAULT 1
);


CREATE TABLE IF NOT EXISTS "user_journey" (
    journey_id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES "user"(user_id),
    event_type VARCHAR(50) NOT NULL,
    action_dttm TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);


CREATE TABLE IF NOT EXISTS "promo_usage" (
    usage_id SERIAL PRIMARY KEY,
    promo_id INTEGER REFERENCES "promo_code"(promo_id),
    user_id BIGINT REFERENCES "user"(user_id),
    usage_dttm TIMESTAMP DEFAULT NOW(),
    payment_id INTEGER REFERENCES "payment"(payment_id)
);

-- 📦 user
CREATE INDEX IF NOT EXISTS idx_user_username ON "user"(username);
CREATE INDEX IF NOT EXISTS idx_user_language ON "user"(language);
CREATE INDEX IF NOT EXISTS idx_user_state ON "user"(user_state);

-- 📌 admin_actions
CREATE INDEX IF NOT EXISTS idx_admin_actions_admin_id ON "admin_actions"(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_actions_user_id ON "admin_actions"(user_id);
CREATE INDEX IF NOT EXISTS idx_admin_actions_lora_id ON "admin_actions"(lora_id);

-- 💸 payment
CREATE INDEX IF NOT EXISTS idx_payment_user_id ON "payment"(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_dttm ON "payment"(payment_dttm);
CREATE INDEX IF NOT EXISTS idx_payment_status ON "payment"(status);

-- 🧠 model
CREATE INDEX IF NOT EXISTS idx_model_user_id ON "model"(user_id);
CREATE INDEX IF NOT EXISTS idx_model_trigger_word ON "model"(trigger_word);
CREATE INDEX IF NOT EXISTS idx_model_status ON "model"(status);
CREATE INDEX IF NOT EXISTS idx_model_replicate_version ON "model"(replicate_version);

-- 🔁 generation
CREATE INDEX IF NOT EXISTS idx_generation_user_id ON "generation"(user_id);
CREATE INDEX IF NOT EXISTS idx_generation_model_id ON "generation"(model_id);
CREATE INDEX IF NOT EXISTS idx_generation_lora_id ON "generation"(lora_id);
CREATE INDEX IF NOT EXISTS idx_generation_is_error ON "generation"(is_error);
CREATE INDEX IF NOT EXISTS idx_generation_start_dttm ON "generation"(start_dttm);

-- 🎨 lora
CREATE INDEX IF NOT EXISTS idx_lora_user_id ON "lora"(user_id);
CREATE INDEX IF NOT EXISTS idx_lora_trigger_word ON "lora"(trigger_word);
CREATE INDEX IF NOT EXISTS idx_lora_is_active ON "lora"(is_active);

-- 🔖 promo_code
CREATE INDEX IF NOT EXISTS idx_promo_code_code ON "promo_code"(code);

-- 🧾 promo_usage
CREATE INDEX IF NOT EXISTS idx_promo_usage_user_id ON "promo_usage"(user_id);
CREATE INDEX IF NOT EXISTS idx_promo_usage_promo_id ON "promo_usage"(promo_id);

-- 👣 user_journey
CREATE INDEX IF NOT EXISTS idx_user_journey_user_id ON "user_journey"(user_id);
CREATE INDEX IF NOT EXISTS idx_user_journey_event_type ON "user_journey"(event_type);

-- 👥 referral_invite
CREATE INDEX IF NOT EXISTS idx_referral_referrer_id ON "referral_invite"(referrer_id);
CREATE INDEX IF NOT EXISTS idx_referral_referred_id ON "referral_invite"(referred_id);
CREATE INDEX IF NOT EXISTS idx_referral_code ON "referral_invite"(referral_code);
