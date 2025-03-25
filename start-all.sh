#!/bin/bash

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

print_message() {
  echo -e "${BOLD}${2}${1}${NC}"
}

print_message "Запуск всех компонентов Dream Photo AI" "${GREEN}"
print_message "=====================================" "${GREEN}"

# Запуск API в фоновом режиме
print_message "Запуск API сервера в фоновом режиме..." "${GREEN}"
./start-api.sh > api.log 2>&1 &
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

# Запуск бота
print_message "Запуск Telegram бота..." "${GREEN}"
./start-bot.sh

# При завершении бота остановить API
print_message "Останавливаю API сервер (PID: $API_PID)..." "${YELLOW}"
kill $API_PID

print_message "Все компоненты остановлены." "${GREEN}" 