#!/bin/bash

# =================================
# Steam Market Monitor - Quick Start
# =================================

echo "🚀 Steam Market Monitor - Quick Start Script"
echo "============================================="

# Проверяем наличие Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен! Установите Docker и повторите попытку."
    echo "   Скачать: https://www.docker.com/get-started"
    exit 1
fi

# Проверяем наличие docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен! Установите Docker Compose и повторите попытку."
    exit 1
fi

# Проверяем наличие .env файла
if [ ! -f ".env" ]; then
    echo "📝 Создаем .env файл из шаблона..."
    cp env.example .env
    echo "⚠️  ВАЖНО: Отредактируйте файл .env и укажите ваш TELEGRAM_BOT_TOKEN!"
    echo "   Получить токен можно у @BotFather в Telegram"
    echo ""
    echo "После редактирования .env файла запустите скрипт снова."
    exit 1
fi

# Проверяем, указан ли токен
if grep -q "your_bot_token_here" .env; then
    echo "⚠️  Пожалуйста, укажите ваш реальный токен в файле .env"
    echo "   Замените 'your_bot_token_here' на токен от @BotFather"
    exit 1
fi

# Создаем необходимые директории
echo "📁 Создаем директории..."
mkdir -p data logs

# Проверяем конфигурацию
if [ ! -f "config.yaml" ]; then
    echo "📋 Создаем базовую конфигурацию..."
    cat > config.yaml << EOF
items:
  - name: "Fracture Case"
    listing_id: 730
    sell_target_price: 140
    buy_target_price: 80
  - name: "Frostivus 2023 Treasure Chest"
    listing_id: 570
    sell_target_price: 10
    buy_target_price: 2.5
EOF
fi

echo "🔨 Собираем Docker образ..."
docker-compose build

echo "🚀 Запускаем бота..."
docker-compose up -d

echo ""
echo "✅ Бот запущен!"
echo ""
echo "📊 Полезные команды:"
echo "   docker-compose logs -f    # Просмотр логов"
echo "   docker-compose stop       # Остановить бота"
echo "   docker-compose restart    # Перезапустить бота"
echo "   docker-compose down       # Полностью удалить контейнер"
echo ""
echo "📱 Найдите вашего бота в Telegram и отправьте /start"
echo ""
echo "🔍 Проверить статус: docker-compose ps"
