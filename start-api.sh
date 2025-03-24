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

print_message "Автономный запуск API Dream Photo AI" "${GREEN}"
print_message "======================================" "${GREEN}"

# Проверка наличия файла .env
if [ ! -f .env ]; then
  print_message "Файл .env не найден. Невозможно продолжить запуск." "${RED}"
  exit 1
fi

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
  print_message "Python 3 не найден. Пожалуйста, установите Python 3." "${RED}"
  exit 1
fi

# Проверка наличия виртуального окружения, если нет - создаем
if [ ! -d "venv" ]; then
  print_message "Виртуальное окружение не найдено. Создаю новое..." "${YELLOW}"
  python3 -m venv venv
  
  if [ $? -ne 0 ]; then
    print_message "Ошибка при создании виртуального окружения." "${RED}"
    exit 1
  fi
  
  print_message "Виртуальное окружение создано!" "${GREEN}"
fi

# Активация виртуального окружения
print_message "Активация виртуального окружения..." "${GREEN}"
source venv/bin/activate

# Установка зависимостей
if [ ! -f "requirements.txt" ]; then
  print_message "Файл requirements.txt не найден. Невозможно установить зависимости." "${RED}"
  exit 1
fi

print_message "Установка зависимостей..." "${GREEN}"
pip install -r requirements.txt

if [ $? -ne 0 ]; then
  print_message "Ошибка при установке зависимостей." "${RED}"
  exit 1
fi

# Принудительное указание переменной DISABLE_DB_CHECK для обхода проверки БД
export DISABLE_DB_CHECK=false

# Запуск API
print_message "Запуск API сервера..." "${GREEN}"
python3 api.py

print_message "API сервер остановлен." "${YELLOW}" 