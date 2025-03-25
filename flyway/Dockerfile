# Используем официальный образ Flyway
FROM flyway/flyway:9.22.3

# Устанавливаем рабочую директорию (необязательно, но удобно)
WORKDIR /flyway

# Копируем конфигурационный файл Flyway (если используется)
COPY flyway.conf /flyway/conf/flyway.conf

# Копируем SQL-миграции
COPY sql /flyway/sql
