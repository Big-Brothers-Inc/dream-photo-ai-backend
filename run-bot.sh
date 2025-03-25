#!/bin/bash

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Dream Photo - Запуск Telegram бота ===${NC}"

# Проверяем, активировано ли виртуальное окружение
if [[ "$VIRTUAL_ENV" == "" ]]; then
  echo -e "${YELLOW}Виртуальное окружение не активировано. Активируем...${NC}"
  if [ -d "../venv_new" ]; then
    source ../venv_new/bin/activate
  else
    echo -e "${YELLOW}Виртуальное окружение не найдено в родительской директории. Проверяем текущую...${NC}"
    if [ -d "venv_new" ]; then
      source venv_new/bin/activate
    else
      echo -e "${RED}Виртуальное окружение не найдено. Создаем...${NC}"
      python3 -m virtualenv venv_new --python=python3.11
      source venv_new/bin/activate
      pip install -r requirements.txt
    fi
  fi
else
  echo -e "${GREEN}Используется виртуальное окружение: $VIRTUAL_ENV${NC}"
fi

# Проверяем наличие необходимых файлов
if [ ! -f "main.py" ]; then
  echo -e "${RED}Файл main.py не найден в текущей директории!${NC}"
  exit 1
fi

# Создаем директорию для логов, если её нет
mkdir -p ../logs

# Проверяем наличие зависимостей
echo -e "${BLUE}Проверка зависимостей...${NC}"
pip show aiogram > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo -e "${YELLOW}aiogram не установлен. Устанавливаем...${NC}"
  pip install aiogram
fi

# Проверяем наличие токена бота в .env
if [ -f "../.env" ]; then
  BOT_TOKEN=$(grep -E "^BOT_TOKEN=" "../.env" | cut -d= -f2)
  if [ -z "$BOT_TOKEN" ]; then
    echo -e "${RED}BOT_TOKEN не найден в .env файле!${NC}"
    exit 1
  else
    echo -e "${GREEN}Токен бота найден в .env файле${NC}"
  fi
else
  echo -e "${RED}.env файл не найден в родительской директории!${NC}"
  exit 1
fi

# Запускаем Telegram бота
echo -e "${BLUE}Запуск Telegram бота...${NC}"
python3 main.py > ../logs/bot.log 2>&1 &
BOT_PID=$!
echo -e "${GREEN}Telegram бот запущен (PID: $BOT_PID)${NC}"

# Ожидаем Ctrl+C
trap "echo -e '${YELLOW}Остановка Telegram бота...${NC}'; kill $BOT_PID; echo -e '${GREEN}Telegram бот остановлен${NC}'; exit 0" SIGINT SIGTERM
wait $BOT_PID

# Эта часть кода не будет выполнена, пока не завершится python main.py
echo -e "${GREEN}Telegram бот остановлен${NC}" 