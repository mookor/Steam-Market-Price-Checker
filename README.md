# Steam Market Price Monitor Bot 🎮

Telegram-бот для мониторинга цен на предметы в Steam Community Market. Отслеживает изменения цен и отправляет уведомления при достижении целевых значений для покупки или продажи.

## 🚀 Функционал бота

### Основные возможности:
- **Мониторинг цен** - отслеживание текущих цен на предметы Steam Market
- **Уведомления** - автоматические оповещения при достижении целевых цен
- **Список отслеживания** - управление watchlist с предметами для мониторинга
- **Поддержка валют** - работа с USD и RUB
- **Веб API** - REST API для интеграции с другими сервисами

### Команды бота:
- `/start` - Запуск бота и первоначальная настройка
- `/add` - Добавить предмет в список отслеживания
- `/prices` - Показать текущие цены всех отслеживаемых предметов
- `/subscribe` - Подписаться на уведомления о ценах
- `/unsubscribe` - Отписаться от уведомлений
- `/change_currency` - Изменить валюту (USD/RUB)
- `/help` - Показать справку по командам

### Технические особенности:
- **База данных**: PostgreSQL для хранения данных пользователей и предметов
- **API**: FastAPI для веб-интерфейса и внешних интеграций
- **Контейнеризация**: Docker и Docker Compose для простого развертывания
- **Мониторинг**: Автоматическая проверка цен с настраиваемым интервалом
- **Логирование**: Подробные логи работы системы

## 📋 Требования

- Docker и Docker Compose
- Telegram Bot Token (получить у [@BotFather](https://t.me/BotFather))

## 🛠 Установка и запуск

### Быстрый старт

1. **Клонируйте репозиторий:**
   ```bash
   git clone <repository-url>
   cd steam
   ```

2. **Настройте токен бота:**
   Создайте в корне проекта файл `docker.env`
   Отредактируйте файл `docker.env` и замените токен на свой:
   ```bash
   TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather
   ```

3. **Запустите бота:**
   
   **Linux/macOS:**
   ```bash
   chmod +x quick_start.sh
   ./quick_start.sh
   ```
   
   **Windows:**
   ```cmd
   quick_start.bat
   ```

### Ручной запуск через Docker Compose

1. **Соберите и запустите контейнеры:**
   ```bash
   docker-compose build
   docker-compose up -d
   ```

2. **Проверьте статус:**
   ```bash
   docker-compose ps
   ```

3. **Просмотр логов:**
   ```bash
   docker-compose logs -f
   ```

### Управление сервисом

- **Остановить бота:** `docker-compose stop`
- **Перезапустить:** `docker-compose restart`
- **Полностью удалить:** `docker-compose down`
- **Просмотр логов:** `docker-compose logs -f`

## 🌐 Веб-интерфейс

После запуска доступны:
- **API**: http://localhost:8000
- **Документация API**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/health

## ⚙️ Конфигурация

### Переменные окружения (docker.env):

```bash
# Токен Telegram бота (ОБЯЗАТЕЛЬНО!)
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Интервал проверки цен в минутах (по умолчанию 5)
CHECK_INTERVAL=5

# Дополнительные настройки
PYTHONUNBUFFERED=1
```

### База данных:
- **Host**: localhost:5433 (внешний порт)
- **Database**: steam_db
- **User**: test_user
- **Password**: 13579

## 📁 Структура проекта

```
steam/
├── SMPC/                   # Основной код приложения
│   ├── api/               # FastAPI веб-сервер
│   ├── bot/               # Telegram бот
│   ├── database/          # Работа с базой данных
│   └── price_parser/      # Парсинг цен Steam Market
├── logs/                  # Логи приложения
├── docker-compose.yml     # Конфигурация Docker
├── docker.env            # Переменные окружения
├── Dockerfile            # Образ приложения
├── requirements.txt      # Python зависимости
├── run_bot.py           # Запуск бота
└── start_server.py      # Запуск API сервера
```

## 🔧 Разработка

### Локальный запуск без Docker:

1. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Настройте переменные окружения:**
   ```bash
   export TELEGRAM_BOT_TOKEN="your_token"
   export DB_HOST="localhost"
   export DB_PORT="5433"
   # ... другие переменные
   ```

3. **Запустите PostgreSQL:**
   ```bash
   docker-compose up -d postgres
   ```

4. **Запустите компоненты:**
   ```bash
   # API сервер
   python start_server.py
   
   # Telegram бот (в другом терминале)
   python run_bot.py
   ```

## 📝 Использование

1. **Найдите бота в Telegram** и отправьте `/start`
2. **Выберите валюту** (USD или RUB)
3. **Добавьте предметы** командой `/add` и укажите URL предмета из Steam Market
4. **Установите целевые цены** для покупки и продажи
5. **Подпишитесь на уведомления** командой `/subscribe`

Бот будет автоматически проверять цены и отправлять уведомления при достижении целевых значений.

## 🐛 Устранение неполадок

### Проблемы с запуском:
- Убедитесь, что Docker и Docker Compose установлены
- Проверьте, что токен бота указан правильно в `docker.env`
- Убедитесь, что порты 8000 и 5433 свободны

### Проблемы с ботом:
- Проверьте логи: `docker-compose logs -f steam_app`
- Убедитесь, что бот не заблокирован в Telegram
- Проверьте правильность токена

### Проблемы с базой данных:
- Проверьте статус контейнера: `docker-compose ps`
- Проверьте логи PostgreSQL: `docker-compose logs postgres`


