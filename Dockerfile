# ===========================
# Dockerfile (в корне проекта)
# ===========================
FROM python:3.9-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем зависимости заранее (для кэширования Docker слоёв)
COPY requirements.txt .

# Обновляем pip и устанавливаем зависимости
RUN pip install --upgrade pip setuptools \
    && pip install -r requirements.txt

# Копируем весь остальной код проекта
COPY . .

# Устанавливаем PYTHONPATH, чтобы импорты работали корректно
ENV PYTHONPATH=/app

# Команда по умолчанию (можно переопределить в docker-compose)
CMD ["python", "-m", "app"]