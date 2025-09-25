#!/bin/bash

# Скрипт для установки Steam Monitor как Docker сервиса с автозапуском

set -e

echo "🚀 Установка Steam Monitor Docker Service"
echo "=========================================="

# Проверяем, что мы в правильной директории
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Ошибка: docker-compose.yml не найден в текущей директории"
    echo "Пожалуйста, запустите скрипт из корневой директории проекта"
    exit 1
fi

# Проверяем наличие Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Пожалуйста, установите Docker сначала:"
    echo "   curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "   sudo sh get-docker.sh"
    exit 1
fi

# Проверяем наличие Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Пожалуйста, установите Docker Compose сначала"
    exit 1
fi

# Проверяем наличие токена бота
if [ ! -f "docker.env" ]; then
    echo "❌ Файл docker.env не найден"
    echo "Пожалуйста, создайте файл docker.env и укажите TELEGRAM_BOT_TOKEN"
    exit 1
fi

# Проверяем, что токен установлен
if grep -q "your_bot_token_here" docker.env; then
    echo "❌ Пожалуйста, замените 'your_bot_token_here' на реальный токен бота в файле docker.env"
    exit 1
fi

echo "✅ Предварительные проверки пройдены"

# Создаем директории для логов и данных
echo "📁 Создание директорий..."
mkdir -p logs
mkdir -p SMPC/database/database/backups

# Устанавливаем права на выполнение для скриптов
echo "🔧 Настройка прав доступа..."
chmod +x docker-entrypoint.sh
chmod +x install-docker-service.sh

# Копируем переменные окружения
echo "📋 Настройка переменных окружения..."
cp docker.env .env

# Собираем Docker образ
echo "🏗️ Сборка Docker образа..."
docker-compose build

# Устанавливаем systemd service
echo "⚙️ Установка systemd service..."
sudo cp steam-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable steam-monitor.service

echo ""
echo "✅ Установка завершена!"
echo ""
echo "📋 Доступные команды:"
echo "  sudo systemctl start steam-monitor    # Запустить сервис"
echo "  sudo systemctl stop steam-monitor     # Остановить сервис"
echo "  sudo systemctl status steam-monitor   # Проверить статус"
echo "  sudo systemctl restart steam-monitor  # Перезапустить сервис"
echo ""
echo "📊 После запуска сервис будет доступен по адресам:"
echo "  API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "📝 Логи можно посмотреть командами:"
echo "  docker-compose logs -f                # Все логи"
echo "  docker-compose logs -f steam_app      # Логи приложения"
echo "  docker-compose logs -f postgres       # Логи базы данных"
echo ""
echo "🚀 Для запуска сервиса выполните:"
echo "  sudo systemctl start steam-monitor"
