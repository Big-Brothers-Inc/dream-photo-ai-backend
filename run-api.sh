#!/bin/bash

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Dream Photo - Запуск API сервера ===${NC}"

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
if [ ! -f "api.py" ]; then
  echo -e "${RED}Файл api.py не найден в текущей директории!${NC}"
  exit 1
fi

# Создаем директорию для логов, если её нет
mkdir -p ../logs

# Проверяем наличие зависимостей
echo -e "${BLUE}Проверка зависимостей...${NC}"
pip show fastapi > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo -e "${YELLOW}FastAPI не установлен. Устанавливаем...${NC}"
  pip install fastapi uvicorn
fi

# Запускаем API сервер
echo -e "${BLUE}Запуск API сервера...${NC}"
python3 api.py > ../logs/api.log 2>&1 &
API_PID=$!
echo -e "${GREEN}API сервер запущен (PID: $API_PID)${NC}"

# Ожидаем Ctrl+C
trap "echo -e '${YELLOW}Остановка API сервера...${NC}'; kill $API_PID; echo -e '${GREEN}API сервер остановлен${NC}'; exit 0" SIGINT SIGTERM
wait $API_PID

# Эта часть кода не будет выполнена, пока не завершится python api.py
echo -e "${GREEN}API сервер остановлен${NC}" 