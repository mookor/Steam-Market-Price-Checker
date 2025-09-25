-- Скрипт для создания базы данных steam_db
-- Выполните этот скрипт подключившись к PostgreSQL как суперпользователь

-- Создание базы данных (если не существует)
SELECT 'CREATE DATABASE steam_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'steam_db')\gexec

-- Предоставление прав пользователю test_user
GRANT ALL PRIVILEGES ON DATABASE steam_db TO test_user;
