# Dream Photo AI Backend

Бэкенд-часть приложения Dream Photo AI для генерации изображений с использованием моделей искусственного интеллекта.

## Требования

- Python 3.9+
- Docker (опционально)
- PostgreSQL

## Локальная разработка

1. Клонируйте репозиторий:
```bash
git clone git@github.com:Big-Brothers-Inc/dream-photo-ai-backend.git
cd dream-photo-ai-backend
```

2. Создайте виртуальное окружение и установите зависимости:
```bash
python -m venv venv
source venv/bin/activate  # Для Linux/Mac
# или
venv\Scripts\activate  # Для Windows
pip install -r requirements.txt
```

3. Настройте переменные окружения, создав файл `.env` на основе `.env.example`.

4. Инициализируйте базу данных:
```bash
python init_db.py
```

5. Запустите приложение:
```bash
python loader/bot.py
```

## Запуск с Docker

1. Соберите Docker образ:
```bash
docker build -t dream-photo-ai-backend .
```

2. Запустите контейнер:
```bash
docker run -p 5000:5000 --env-file .env dream-photo-ai-backend
```

## Структура проекта

- `config/` - Конфигурационные файлы
- `db/` - Модели базы данных и настройки подключения
- `handlers/` - Обработчики запросов
- `loader/` - Загрузчики и точки входа
- `repository/` - Слой доступа к данным
- `services/` - Бизнес-логика
- `utils/` - Вспомогательные функции и утилиты
- `temp_photos/` - Временное хранилище загруженных фотографий

## API Endpoints

API документация доступна по адресу `/docs` после запуска приложения. 