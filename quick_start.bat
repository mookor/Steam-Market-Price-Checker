@echo off
chcp 65001 >nul

REM =================================
REM Steam Market Monitor - Quick Start
REM =================================

echo 🚀 Steam Market Monitor - Quick Start Script
echo =============================================

REM Проверяем наличие Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker не установлен! Установите Docker Desktop и повторите попытку.
    echo    Скачать: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Проверяем наличие docker-compose
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose не установлен! Обычно входит в Docker Desktop.
    pause
    exit /b 1
)

REM Проверяем наличие .env файла
if not exist ".env" (
    echo 📝 Создаем .env файл из шаблона...
    copy env.example .env >nul
    echo ⚠️  ВАЖНО: Отредактируйте файл .env и укажите ваш TELEGRAM_BOT_TOKEN!
    echo    Получить токен можно у @BotFather в Telegram
    echo.
    echo После редактирования .env файла запустите скрипт снова.
    pause
    exit /b 1
)

REM Проверяем, указан ли токен
findstr "your_bot_token_here" .env >nul
if not errorlevel 1 (
    echo ⚠️  Пожалуйста, укажите ваш реальный токен в файле .env
    echo    Замените 'your_bot_token_here' на токен от @BotFather
    pause
    exit /b 1
)

REM Создаем необходимые директории
echo 📁 Создаем директории...
if not exist "data" mkdir data
if not exist "logs" mkdir logs

REM Проверяем конфигурацию
if not exist "config.yaml" (
    echo 📋 Создаем базовую конфигурацию...
    (
        echo items:
        echo   - name: "Fracture Case"
        echo     listing_id: 730
        echo     sell_target_price: 140
        echo     buy_target_price: 80
        echo   - name: "Frostivus 2023 Treasure Chest"
        echo     listing_id: 570
        echo     sell_target_price: 10
        echo     buy_target_price: 2.5
    ) > config.yaml
)

echo 🔨 Собираем Docker образ...
docker-compose build

echo 🚀 Запускаем бота...
docker-compose up -d

echo.
echo ✅ Бот запущен!
echo.
echo 📊 Полезные команды:
echo    docker-compose logs -f    # Просмотр логов
echo    docker-compose stop       # Остановить бота
echo    docker-compose restart    # Перезапустить бота
echo    docker-compose down       # Полностью удалить контейнер
echo.
echo 📱 Найдите вашего бота в Telegram и отправьте /start
echo.
echo 🔍 Проверить статус: docker-compose ps
echo.
pause
