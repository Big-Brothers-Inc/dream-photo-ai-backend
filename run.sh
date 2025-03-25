#!/bin/bash

# Устанавливаем PYTHONPATH
export PYTHONPATH=$(pwd)

# === Настройки ===
VENV_PATH="./venv"
PYTHON="$VENV_PATH/bin/python"

# === Проверка виртуального окружения ===
if [ ! -f "$PYTHON" ]; then
  echo "❌ Виртуальное окружение не найдено по пути: $PYTHON"
  echo "Создайте его: python -m venv venv"
  exit 1
fi

# === Проверка наличия PostgreSQL CLI ===
check_postgres_cli() {
  if ! command -v initdb >/dev/null 2>&1 || ! command -v pg_ctl >/dev/null 2>&1; then
    echo "⚠️ PostgreSQL CLI (initdb / pg_ctl) не найдены. Устанавливаем через Homebrew..."
    if ! command -v brew >/dev/null 2>&1; then
      echo "❌ Homebrew не установлен. Установи его: https://brew.sh"
      exit 1
    fi
    brew install postgresql@14

    # Добавляем PostgreSQL в PATH, если нужно
    export PATH="/opt/homebrew/opt/postgresql@14/bin:$PATH"
    echo "✅ PostgreSQL установлен."
  else
    echo "✅ PostgreSQL CLI найден."
  fi
}

check_postgres_cli

# === Импорт значений из config ===
echo "📦 Импорт настроек из config.py..."
# 🔍 Проверим, подтянулся ли DB_USER из .env
echo "🔍 Проверка: значения из .env"
$PYTHON -c "from app.config import config; print('[.env] DB_USER =', config.DB_USER); print('[.env] DB_NAME =', config.DB_NAME)"

PG_DATA=$($PYTHON -c "from app.config import config; print(config.BASE_UPLOAD_DIR or 'pg_data')")
PG_PORT=$($PYTHON -c "from app.config import config; print(config.DB_PORT or 5432)")

FASTAPI_HOST=$($PYTHON -c "from app.config import config; print(config.API_HOST or '0.0.0.0')")
FASTAPI_PORT=$($PYTHON -c "from app.config import config; print(config.API_PORT or 8000)")

# === Запуск PostgreSQL (если не Docker) ===
if ! pg_isready -p $PG_PORT > /dev/null 2>&1; then
  echo "🚀 Запускаем PostgreSQL на порту $PG_PORT..."
  if [ ! -d "$PG_DATA" ]; then
    echo "📁 Инициализация базы данных в $PG_DATA..."
    initdb -D "$PG_DATA"
  fi
  pg_ctl -D "$PG_DATA" -o "-p $PG_PORT" -l logfile start
  sleep 2
else
  echo "✅ PostgreSQL уже работает на порту $PG_PORT"
fi

# === Создание базы данных, если её нет ===
echo "🛠 Проверка и создание базы данных (если нужно)..."
$PYTHON - <<EOF
import psycopg2
from app.config import config

try:
    conn = psycopg2.connect(dbname='postgres', user=config.DB_USER, password=config.DB_PASSWORD)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (config.DB_NAME,))
    if not cur.fetchone():
        print(f"➕ База данных '{config.DB_NAME}' не найдена. Создаём...")
        cur.execute(f"CREATE DATABASE {config.DB_NAME}")
        print("✅ База данных успешно создана.")
    else:
        print(f"✅ База данных '{config.DB_NAME}' уже существует.")

    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Ошибка при создании базы данных: {e}")
EOF




# === Запуск FastAPI ===
echo "🌐 Запуск FastAPI на http://$FASTAPI_HOST:$FASTAPI_PORT..."
$PYTHON -m uvicorn app.api.app:app --host $FASTAPI_HOST --port $FASTAPI_PORT &
FASTAPI_PID=$!

# === Запуск Telegram-бота ===
echo "🤖 Запуск Telegram-бота..."
$PYTHON app/bot/main.py &
BOT_PID=$!

# === Обработка остановки (Ctrl+C) ===
trap "echo '🛑 Остановка...'; kill $BOT_PID $FASTAPI_PID; pg_ctl -D $PG_DATA stop" SIGINT

# === Ожидание завершения процессов ===
wait
