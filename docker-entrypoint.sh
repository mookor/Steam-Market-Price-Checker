#!/bin/bash
set -e

echo "🚀 Starting Steam Monitor Application..."

# Функция для ожидания готовности PostgreSQL
wait_for_postgres() {
    echo "⏳ Waiting for PostgreSQL to be ready..."
    until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
        echo "PostgreSQL is unavailable - sleeping"
        sleep 2
    done
    echo "✅ PostgreSQL is ready!"
}

# Функция для проверки готовности API
wait_for_api() {
    echo "⏳ Waiting for API to be ready..."
    until curl -f http://localhost:8000/health 2>/dev/null; do
        echo "API is unavailable - sleeping"
        sleep 2
    done
    echo "✅ API is ready!"
}

# Экспорт переменных окружения для базы данных
export DB_USER=${DB_USER:-test_user}
export DB_PASSWORD=${DB_PASSWORD:-13579}
export DB_HOST=${DB_HOST:-postgres}
export DB_PORT=${DB_PORT:-5432}
export DB_NAME=${DB_NAME:-steam_db}

# Ждем готовности PostgreSQL
wait_for_postgres

# Шаг 1: Настройка базы данных
echo "🗄️ Setting up database..."
cd /app/SMPC/database
python setup_database.py

cd /app/SMPC/api

# Шаг 2: Запуск API сервера в фоне
echo "🌐 Starting API server..."
python start_server.py &
API_PID=$!

# Ждем готовности API
wait_for_api


cd /app/SMPC/bot

# Шаг 3: Запуск бота
echo "🤖 Starting Telegram bot..."
python run_bot.py &
BOT_PID=$!

# Функция для корректного завершения процессов
cleanup() {
    echo "🛑 Shutting down services..."
    kill $BOT_PID 2>/dev/null || true
    kill $API_PID 2>/dev/null || true
    wait $BOT_PID 2>/dev/null || true
    wait $API_PID 2>/dev/null || true
    echo "✅ Services stopped"
    exit 0
}

# Обработка сигналов для корректного завершения
trap cleanup SIGTERM SIGINT

echo "✅ All services started successfully!"
echo "📊 API available at: http://localhost:8000"
echo "📚 API docs at: http://localhost:8000/docs"
echo "🤖 Telegram bot is running"

# Ждем завершения процессов
wait $API_PID $BOT_PID
