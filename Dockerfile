# Используем официальный Python образ
FROM python:3.12-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Дополнительные зависимости для бота
RUN pip install python-telegram-bot==22.4 python-dotenv==1.1.1 APScheduler==3.11.0 psycopg2-binary==2.9.10 PyYAML==6.0.2

# Копируем весь проект
COPY . .

# Устанавливаем пакет SMPC в editable режиме
RUN pip install -e .

# Создаем директории для логов и бэкапов
RUN mkdir -p logs SMPC/database/database/backups

# Устанавливаем права на выполнение для скриптов
RUN chmod +x docker-entrypoint.sh

# Создаем пользователя для безопасности
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Устанавливаем права на директорию логов
RUN chmod 755 logs

USER appuser

# Открываем порт для API
EXPOSE 8000

# Точка входа
ENTRYPOINT ["./docker-entrypoint.sh"]
