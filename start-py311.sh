#!/bin/bash

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Функция для красивого вывода
print_message() {
  echo -e "${BOLD}${2}${1}${NC}"
}

print_message "Запуск Dream Photo AI с Python 3.11" "${GREEN}"
print_message "===================================" "${GREEN}"

# Проверка наличия Python 3.11
if command -v python3.11 &> /dev/null; then
  print_message "Python 3.11 найден в системе" "${GREEN}"
  PYTHON_CMD="python3.11"
else
  # Проверяем другие возможные пути
  if [ -f "/opt/homebrew/bin/python3.11" ]; then
    print_message "Python 3.11 найден в Homebrew" "${GREEN}"
    PYTHON_CMD="/opt/homebrew/bin/python3.11"
  elif [ -f "/usr/local/bin/python3.11" ]; then
    print_message "Python 3.11 найден в /usr/local/bin" "${GREEN}"
    PYTHON_CMD="/usr/local/bin/python3.11"
  elif [ -d "/Users/serzhbigulov/Documents/Ai_dream_photo/venv_py311" ]; then
    print_message "Найдено виртуальное окружение Python 3.11 в родительской директории" "${GREEN}"
    source "/Users/serzhbigulov/Documents/Ai_dream_photo/venv_py311/bin/activate"
    PYTHON_CMD="python"
  else
    print_message "Python 3.11 не найден. Пожалуйста, установите Python 3.11:" "${RED}"
    print_message "brew install python@3.11" "${YELLOW}"
    exit 1
  fi
fi

# Определяем версию Python
PY_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
print_message "Используется Python версии: $PY_VERSION" "${GREEN}"

# Проверяем совместимость
if [[ "$PY_VERSION" != "3.11" ]]; then
  print_message "Внимание: Вы используете Python $PY_VERSION, но рекомендуется Python 3.11" "${YELLOW}"
  read -p "Продолжить с текущей версией? (y/n): " answer
  if [[ $answer != "y" ]]; then
    print_message "Прерывание запуска" "${RED}"
    exit 1
  fi
fi

# Проверка наличия файла .env
if [ ! -f .env ]; then
  print_message "Файл .env не найден. Создаю его с базовыми настройками..." "${YELLOW}"
  cat > .env << EOL
# Telegram Bot
BOT_TOKEN=ЗАМЕНИТЕ_НА_ВАШ_ТОКЕН
WEBAPP_URL=https://example.ngrok-free.app
BOT_USERNAME=dream_photo_bot

# Replicate API
REPLICATE_API_TOKEN=ЗАМЕНИТЕ_НА_ВАШ_ТОКЕН

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=dream_photo
DB_USER=serzhbigulov
DB_PASSWORD=postgres
DB_MIN_CONN=1
DB_MAX_CONN=10

# Другие API ключи
NGROK_AUTH_TOKEN=ЗАМЕНИТЕ_НА_ВАШ_ТОКЕН
NGROK_URL=https://example.ngrok-free.app

# Цены (в копейках)
MODEL_TRAINING_PRICE=50000
GENERATION_PRICE=5000

# Другие настройки
DEBUG=True
ADMIN_USER_IDS=63196679,472568354
SERVER_IP=127.0.0.1
API_PORT=8000

# База данных - включаем проверку подключения
DISABLE_DB_CHECK=false

# Пути к директориям
BASE_UPLOAD_DIR=user_training_photos
EOL
  print_message "Создан базовый файл .env" "${GREEN}"
fi

# Функция для проверки и инициализации базы данных
check_and_init_database() {
  print_message "Проверка базы данных PostgreSQL..." "${GREEN}"
  
  # Проверяем, установлен ли PostgreSQL
  if ! command -v psql &> /dev/null; then
    print_message "PostgreSQL не установлен. Пожалуйста, установите PostgreSQL:" "${RED}"
    print_message "brew install postgresql@14" "${YELLOW}"
    print_message "Запускаю с отключенной проверкой базы данных" "${YELLOW}"
    sed -i '' 's/DISABLE_DB_CHECK=false/DISABLE_DB_CHECK=true/g' .env
    return 1
  fi
  
  # Проверяем, запущен ли сервер PostgreSQL
  if ! pg_isready &> /dev/null; then
    print_message "Сервер PostgreSQL не запущен. Запустите его с помощью:" "${RED}"
    print_message "brew services start postgresql@14" "${YELLOW}"
    print_message "Запускаю с отключенной проверкой базы данных" "${YELLOW}"
    sed -i '' 's/DISABLE_DB_CHECK=false/DISABLE_DB_CHECK=true/g' .env
    return 1
  fi
  
  # Получаем настройки БД из .env
  DB_NAME=$(grep -o "DB_NAME=.*" .env | cut -d'=' -f2)
  DB_USER=$(grep -o "DB_USER=.*" .env | cut -d'=' -f2)
  DB_PASSWORD=$(grep -o "DB_PASSWORD=.*" .env | cut -d'=' -f2)
  
  # Проверяем, существует ли база данных
  if ! psql -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    print_message "База данных $DB_NAME не существует. Создаем..." "${YELLOW}"
    createdb $DB_NAME || {
      print_message "Не удалось создать базу данных. Запускаю с отключенной проверкой БД." "${RED}"
      sed -i '' 's/DISABLE_DB_CHECK=false/DISABLE_DB_CHECK=true/g' .env
      return 1
    }
  fi
  
  # Проверяем наличие таблиц в базе данных
  TABLE_COUNT=$(psql -d $DB_NAME -c "SELECT count(*) FROM pg_tables WHERE schemaname = 'public';" -t | tr -d ' ')
  
  if [ "$TABLE_COUNT" -eq "0" ] || [ -f "init_db.sql" ]; then
    print_message "Инициализируем базу данных схемой из init_db.sql..." "${YELLOW}"
    
    if [ -f "init_db.sql" ]; then
      psql -d $DB_NAME -f init_db.sql || {
        print_message "Ошибка при инициализации базы данных. Запускаю с отключенной проверкой БД." "${RED}"
        sed -i '' 's/DISABLE_DB_CHECK=false/DISABLE_DB_CHECK=true/g' .env
        return 1
      }
    elif [ -f "repository/schema.sql" ]; then
      psql -d $DB_NAME -f repository/schema.sql || {
        print_message "Ошибка при инициализации базы данных. Запускаю с отключенной проверкой БД." "${RED}"
        sed -i '' 's/DISABLE_DB_CHECK=false/DISABLE_DB_CHECK=true/g' .env
        return 1
      }
    else
      print_message "Файл схемы не найден. Запускаю с отключенной проверкой базы данных." "${RED}"
      sed -i '' 's/DISABLE_DB_CHECK=false/DISABLE_DB_CHECK=true/g' .env
      return 1
    fi
  fi
  
  # Включаем проверку базы данных
  sed -i '' 's/DISABLE_DB_CHECK=true/DISABLE_DB_CHECK=false/g' .env
  print_message "База данных успешно инициализирована и готова к использованию!" "${GREEN}"
  return 0
}

# Проверяем и инициализируем базу данных
print_message "Проверка и настройка базы данных..." "${GREEN}"
check_and_init_database

# Создаем виртуальное окружение с Python 3.11
if [ ! -d "venv_py311" ]; then
  print_message "Создание виртуального окружения с Python 3.11..." "${GREEN}"
  $PYTHON_CMD -m venv venv_py311
  
  if [ $? -ne 0 ]; then
    print_message "Ошибка при создании виртуального окружения." "${RED}"
    exit 1
  fi
  
  print_message "Виртуальное окружение создано!" "${GREEN}"
fi

# Активация виртуального окружения
print_message "Активация виртуального окружения..." "${GREEN}"
source venv_py311/bin/activate

# Установка базовых зависимостей
print_message "Установка основных зависимостей..." "${GREEN}"
pip install --upgrade pip
pip install python-dotenv fastapi uvicorn pydantic requests pillow aiogram

# Установка PostgreSQL драйвера
print_message "Установка драйвера PostgreSQL..." "${GREEN}"
pip install psycopg2-binary || {
  print_message "Не удалось установить psycopg2-binary, пробуем psycopg2..." "${YELLOW}"
  pip install psycopg2 || print_message "Не удалось установить PostgreSQL драйвер, но продолжаем запуск" "${RED}"
}

# Установка зависимостей
if [ -f "requirements.txt" ]; then
  print_message "Установка дополнительных зависимостей из requirements.txt..." "${GREEN}"
  pip install -r requirements.txt || {
    print_message "Возникли проблемы при установке пакетов из requirements.txt" "${YELLOW}"
    print_message "Пробуем установить каждый пакет отдельно..." "${YELLOW}"
    
    # Построчная установка зависимостей
    while read requirement; do
      if [[ ! -z "$requirement" && ! "$requirement" =~ ^\s*# ]]; then
        print_message "Установка: $requirement" "${GREEN}"
        pip install $requirement || print_message "Не удалось установить $requirement" "${RED}"
      fi
    done < requirements.txt
  }
fi

# Получаем настройку DISABLE_DB_CHECK из обновленного .env файла
DISABLE_DB_CHECK=$(grep -o "DISABLE_DB_CHECK=.*" .env | cut -d'=' -f2)

# Запрос компонента для запуска
print_message "Какой компонент вы хотите запустить?" "${YELLOW}"
print_message "1. API сервер (FastAPI)" "${GREEN}"
print_message "2. Telegram бот (Aiogram)" "${GREEN}"
print_message "3. Оба компонента" "${GREEN}"
read -p "Выберите вариант (1/2/3): " choice

case $choice in
  1)
    print_message "Запуск API сервера..." "${GREEN}"
    if [ "$DISABLE_DB_CHECK" = "true" ]; then
      print_message "Запускаю с отключенной проверкой базы данных (DISABLE_DB_CHECK=true)" "${YELLOW}"
      DISABLE_DB_CHECK=true python api.py
    else
      print_message "Запускаю с проверкой базы данных" "${GREEN}"
      python api.py
    fi
    ;;
  2)
    print_message "Запуск Telegram бота..." "${GREEN}"
    if [ "$DISABLE_DB_CHECK" = "true" ]; then
      DISABLE_DB_CHECK=true python main.py
    else
      python main.py
    fi
    ;;
  3)
    print_message "Запуск API сервера в фоновом режиме..." "${GREEN}"
    if [ "$DISABLE_DB_CHECK" = "true" ]; then
      DISABLE_DB_CHECK=true python api.py > api.log 2>&1 &
    else
      python api.py > api.log 2>&1 &
    fi
    API_PID=$!
    
    # Ожидание запуска API
    print_message "Ожидание запуска API (5 секунд)..." "${YELLOW}"
    sleep 5
    
    # Проверка запуска API
    if ps -p $API_PID > /dev/null; then
      print_message "API сервер успешно запущен (PID: $API_PID)" "${GREEN}"
    else
      print_message "Ошибка при запуске API сервера. Проверьте api.log" "${RED}"
      exit 1
    fi
    
    print_message "Запуск Telegram бота..." "${GREEN}"
    if [ "$DISABLE_DB_CHECK" = "true" ]; then
      DISABLE_DB_CHECK=true python main.py
    else
      python main.py
    fi
    
    # При завершении бота остановить API
    print_message "Останавливаю API сервер (PID: $API_PID)..." "${YELLOW}"
    kill $API_PID 2>/dev/null || print_message "API сервер уже остановлен" "${YELLOW}"
    ;;
  *)
    print_message "Неверный выбор. Запускаю только API сервер..." "${YELLOW}"
    if [ "$DISABLE_DB_CHECK" = "true" ]; then
      DISABLE_DB_CHECK=true python api.py
    else
      python api.py
    fi
    ;;
esac

print_message "Работа скрипта завершена." "${GREEN}" 