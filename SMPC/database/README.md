# Steam Database Setup

Этот проект содержит SQLAlchemy модели и примеры для работы с базой данных Steam.

## Установка зависимостей

```bash
pip install sqlalchemy asyncpg psycopg2-binary
```

## Настройка базы данных

### Вариант 1: Автоматическая настройка

Запустите скрипт настройки:

```bash
python setup_database.py
```

### Вариант 2: Ручная настройка

1. Подключитесь к PostgreSQL как суперпользователь:
```bash
sudo -u postgres psql
```

2. Создайте базу данных:
```sql
CREATE DATABASE steam_db;
GRANT ALL PRIVILEGES ON DATABASE steam_db TO test_user;
\q
```

3. Или используйте готовый SQL файл:
```bash
sudo -u postgres psql -f create_db.sql
```

## Структура файлов

- `models.py` - SQLAlchemy модели для таблиц
- `01_create_tables.sql` - SQL скрипт создания таблиц
- `example_usage.py` - Асинхронный пример использования
- `example_usage_sync.py` - Синхронный пример использования
- `setup_database.py` - Скрипт автоматической настройки БД
- `create_db.sql` - SQL для создания БД

## Использование

### Асинхронная версия:
```bash
python example_usage.py
```

### Синхронная версия:
```bash
python example_usage_sync.py
```

## Модели

### User
- `id` - Уникальный идентификатор
- `username` - Имя пользователя (уникальное)
- `email` - Email (уникальный)
- `subscriber` - Флаг подписки
- `period` - Период действия

### UserItem
- `id` - Уникальный идентификатор
- `user_id` - Ссылка на пользователя
- `listing_id` - ID предмета в Steam
- `name` - Название предмета
- `buy_target_price` - Целевая цена покупки
- `sell_target_price` - Целевая цена продажи
- `notification_sent` - Флаг отправки уведомления

### UserPeriodUpdate
- `id` - Уникальный идентификатор
- `user_id` - Ссылка на пользователя
- `period` - Период обновления
- `updated_at` - Время обновления

## Настройка подключения

Измените параметры подключения в файлах:

```python
DATABASE_URL = "postgresql+asyncpg://username:password@localhost:5432/steam_db"
```

## Возможные проблемы

### База данных не существует
```
asyncpg.exceptions.InvalidCatalogNameError: database "steam_db" does not exist
```

**Решение:** Создайте базу данных используя один из способов выше.

### Отсутствует драйвер
```
ModuleNotFoundError: No module named 'psycopg2'
```

**Решение:** Установите драйверы:
```bash
pip install psycopg2-binary asyncpg
```
