#!/bin/bash

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Путь к виртуальному окружению
VENV_PATH="venv"

# Функция для красивого вывода
print_message() {
  echo -e "${BOLD}${2}${1}${NC}"
}

print_message "Запуск Dream Photo AI (Универсальный скрипт)" "${GREEN}"
print_message "===========================================" "${GREEN}"

# Проверка наличия файла .env
if [ ! -f .env ]; then
  print_message "Файл .env не найден. Создаю базовый файл окружения." "${YELLOW}"
  cp temp.env .env 2>/dev/null || echo "# Базовый .env файл" > .env
  print_message "Файл .env создан, но требует настройки!" "${YELLOW}"
fi

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
  print_message "Python 3 не найден. Пожалуйста, установите Python 3." "${RED}"
  exit 1
fi

# Определяем текущую версию Python
PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
print_message "Обнаружена версия Python: $PY_VERSION" "${GREEN}"

# Проверка наличия виртуального окружения, если нет - создаем
if [ ! -d "$VENV_PATH" ]; then
  print_message "Виртуальное окружение не найдено. Создаю новое..." "${YELLOW}"
  python3 -m venv $VENV_PATH
  
  if [ $? -ne 0 ]; then
    print_message "Ошибка при создании виртуального окружения." "${RED}"
    exit 1
  fi
  
  print_message "Виртуальное окружение создано!" "${GREEN}"
fi

# Активация виртуального окружения
print_message "Активация виртуального окружения..." "${GREEN}"
source $VENV_PATH/bin/activate

# Устанавливаем базовые зависимости отдельно
print_message "Установка базовых зависимостей..." "${GREEN}"
pip install --upgrade pip python-dotenv fastapi uvicorn requests aiofiles

# Проверяем, есть ли файл requirements.txt
if [ -f "requirements.txt" ]; then
  print_message "Установка зависимостей из requirements.txt..." "${GREEN}"
  # Пробуем установить все зависимости, игнорируя ошибки
  pip install -r requirements.txt --no-dependencies || print_message "Некоторые пакеты не удалось установить, но это может быть нормально" "${YELLOW}"
fi

# Установка минимально необходимых библиотек для запуска
print_message "Установка критически важных зависимостей..." "${GREEN}"
pip install aiogram || print_message "Ошибка при установке aiogram" "${RED}"

# Принудительное указание переменной DISABLE_DB_CHECK для обхода проверки БД
export DISABLE_DB_CHECK=false

# Запрос компонента для запуска
print_message "Какой компонент вы хотите запустить?" "${YELLOW}"
print_message "1. API сервер (FastAPI)" "${GREEN}"
print_message "2. Telegram бот (Aiogram)" "${GREEN}"
print_message "3. Оба компонента" "${GREEN}"
read -p "Выберите вариант (1/2/3): " choice

case $choice in
  1)
    print_message "Запуск API сервера..." "${GREEN}"
    python3 api.py
    ;;
  2)
    print_message "Запуск Telegram бота..." "${GREEN}"
    python3 main.py
    ;;
  3)
    print_message "Запуск API сервера в фоновом режиме..." "${GREEN}"
    python3 api.py > api.log 2>&1 &
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
    python3 main.py
    
    # При завершении бота остановить API
    print_message "Останавливаю API сервер (PID: $API_PID)..." "${YELLOW}"
    kill $API_PID 2>/dev/null || print_message "API сервер уже остановлен" "${YELLOW}"
    ;;
  *)
    print_message "Неверный выбор. Запускаю только API сервер..." "${YELLOW}"
    python3 api.py
    ;;
esac

print_message "Работа скрипта завершена." "${GREEN}" 