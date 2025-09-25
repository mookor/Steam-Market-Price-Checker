"""
Скрипт для создания базы данных и таблиц
Включает систему миграций для обновления структуры таблиц
"""

import asyncio
import asyncpg
import json
import os
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from models import Base

# Параметры подключения
DB_USER = os.getenv("DB_USER", "test_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "13579")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "steam_db")

# URL для подключения к postgres (системной БД) для создания новой БД
POSTGRES_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres"
# URL для подключения к созданной БД
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


async def drop_database():
    """Удаление базы данных steam_db"""
    try:
        # Подключаемся к системной БД postgres для удаления БД
        conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database='postgres'
        )
        
        # Проверяем, существует ли БД
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", DB_NAME
        )
        
        if exists:
            # Завершаем все активные подключения к БД
            await conn.execute(f"""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = '{DB_NAME}' AND pid <> pg_backend_pid()
            """)
            
            # Удаляем БД
            await conn.execute(f'DROP DATABASE "{DB_NAME}"')
            print(f"База данных '{DB_NAME}' удалена успешно")
        else:
            print(f"База данных '{DB_NAME}' не существует")
            
        await conn.close()
        return True
        
    except Exception as e:
        print(f"Ошибка при удалении базы данных: {e}")
        return False


async def create_database():
    """Создание базы данных steam_db"""
    try:
        # Подключаемся к системной БД postgres для создания новой БД
        conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database='postgres'
        )
        
        # Проверяем, существует ли уже БД
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", DB_NAME
        )
        
        if not exists:
            # Создаем БД (нужно закрыть транзакцию)
            await conn.execute(f'CREATE DATABASE "{DB_NAME}"')
            print(f"База данных '{DB_NAME}' создана успешно")
        else:
            print(f"База данных '{DB_NAME}' уже существует")
            
        await conn.close()
        return True
        
    except Exception as e:
        print(f"Ошибка при создании базы данных: {e}")
        return False


async def create_tables():
    """Создание таблиц в базе данных"""
    try:
        # Создаем движок для подключения к нашей БД
        engine = create_async_engine(DATABASE_URL, echo=True)
        
        # Создаем таблицы
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        print("Таблицы созданы успешно")
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")
        return False


async def create_migration_table():
    """Создание таблицы для отслеживания миграций"""
    try:
        conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        
        # Создаем таблицу миграций если её нет
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id SERIAL PRIMARY KEY,
                version VARCHAR(50) UNIQUE NOT NULL,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        """)
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"Ошибка при создании таблицы миграций: {e}")
        return False


async def get_current_schema_version():
    """Получение текущей версии схемы"""
    try:
        conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        
        # Получаем последнюю примененную миграцию
        version = await conn.fetchval("""
            SELECT version FROM schema_migrations 
            ORDER BY applied_at DESC 
            LIMIT 1
        """)
        
        await conn.close()
        return version or "0.0.0"
        
    except Exception as e:
        print(f"Ошибка при получении версии схемы: {e}")
        return "0.0.0"


async def backup_data():
    """Создание резервной копии данных"""
    try:
        conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        
        backup_data = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Получаем список всех таблиц
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name != 'schema_migrations'
        """)
        
        # Сохраняем данные каждой таблицы
        for table in tables:
            table_name = table['table_name']
            rows = await conn.fetch(f"SELECT * FROM {table_name}")
            backup_data[table_name] = [dict(row) for row in rows]
        
        # Сохраняем в файл
        backup_dir = "database/backups"
        os.makedirs(backup_dir, exist_ok=True)
        backup_file = f"{backup_dir}/backup_{timestamp}.json"
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
        
        await conn.close()
        print(f"Резервная копия создана: {backup_file}")
        return backup_file
        
    except Exception as e:
        print(f"Ошибка при создании резервной копии: {e}")
        return None


async def drop_all_tables():
    """Удаление всех таблиц (кроме миграций)"""
    try:
        conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        
        # Получаем список всех таблиц
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name != 'schema_migrations'
        """)
        
        # Удаляем таблицы в правильном порядке (с учетом зависимостей)
        for table in tables:
            table_name = table['table_name']
            await conn.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
            print(f"Таблица {table_name} удалена")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"Ошибка при удалении таблиц: {e}")
        return False


async def restore_data(backup_file):
    """Восстановление данных из резервной копии"""
    try:
        if not os.path.exists(backup_file):
            print(f"Файл резервной копии не найден: {backup_file}")
            return False
            
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        
        # Восстанавливаем данные для каждой таблицы
        for table_name, rows in backup_data.items():
            if not rows:
                continue
                
            # Проверяем, существует ли таблица
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = $1
                )
            """, table_name)
            
            if not table_exists:
                print(f"Таблица {table_name} не существует, пропускаем")
                continue
            
            # Получаем колонки таблицы
            columns = await conn.fetch("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = $1
                ORDER BY ordinal_position
            """, table_name)
            
            column_names = [col['column_name'] for col in columns]
            
            # Вставляем данные
            for row in rows:
                # Фильтруем только существующие колонки
                filtered_row = {k: v for k, v in row.items() if k in column_names}
                
                if filtered_row:
                    placeholders = ', '.join([f'${i+1}' for i in range(len(filtered_row))])
                    columns_str = ', '.join(filtered_row.keys())
                    
                    await conn.execute(
                        f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})",
                        *filtered_row.values()
                    )
            
            print(f"Данные таблицы {table_name} восстановлены ({len(rows)} записей)")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"Ошибка при восстановлении данных: {e}")
        return False


async def update_schema():
    """Обновление схемы базы данных с сохранением данных"""
    print("=== Обновление схемы базы данных ===")
    
    # Шаг 1: Создаем таблицу миграций
    print("\n1. Создание таблицы миграций...")
    if not await create_migration_table():
        return False
    
    # Шаг 2: Получаем текущую версию
    current_version = await get_current_schema_version()
    print(f"Текущая версия схемы: {current_version}")
    
    # Шаг 3: Создаем резервную копию
    print("\n2. Создание резервной копии данных...")
    backup_file = await backup_data()
    if not backup_file:
        print("Не удалось создать резервную копию. Прерываем обновление.")
        return False
    
    # Шаг 4: Удаляем старые таблицы
    print("\n3. Удаление старых таблиц...")
    if not await drop_all_tables():
        print("Не удалось удалить старые таблицы")
        return False
    
    # Шаг 5: Создаем новые таблицы
    print("\n4. Создание новых таблиц...")
    if not await create_tables():
        print("Не удалось создать новые таблицы")
        return False
    
    # Шаг 6: Восстанавливаем данные
    print("\n5. Восстановление данных...")
    if not await restore_data(backup_file):
        print("Не удалось восстановить данные")
        return False
    
    # Шаг 7: Обновляем версию схемы
    try:
        conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        
        new_version = datetime.now().strftime("%Y.%m.%d_%H%M%S")
        await conn.execute("""
            INSERT INTO schema_migrations (version, description) 
            VALUES ($1, $2)
        """, new_version, "Schema update with data migration")
        
        await conn.close()
        print(f"Версия схемы обновлена до: {new_version}")
        
    except Exception as e:
        print(f"Ошибка при обновлении версии: {e}")
        return False
    
    print("\n✅ Схема базы данных успешно обновлена!")
    return True


async def test_connection():
    """Тестирование подключения к БД"""
    try:
        conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        
        # Проверяем созданные таблицы
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        print("Созданные таблицы:")
        for table in tables:
            print(f"  - {table['table_name']}")
            
        await conn.close()
        return True
        
    except Exception as e:
        print(f"Ошибка при тестировании подключения: {e}")
        return False


async def main():
    """Основная функция настройки БД"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "update" or command == "migrate":
            # Обновление схемы с сохранением данных
            await update_schema()
            return
            
        elif command == "drop" or command == "delete":
            # Полное удаление БД (потеря данных!)
            print("🗑️  ВНИМАНИЕ: Это ПОЛНОСТЬЮ УДАЛИТ базу данных!")
            print(f"База данных '{DB_NAME}' будет безвозвратно удалена.")
            response = input("Продолжить? (yes/no): ").lower()
            if response == "yes":
                print("=== Удаление базы данных ===")
                
                # Создаем резервную копию перед удалением
                print("\n1. Создание финальной резервной копии...")
                backup_file = await backup_data()
                if backup_file:
                    print(f"Резервная копия сохранена: {backup_file}")
                
                # Удаляем БД
                print("\n2. Удаление базы данных...")
                if await drop_database():
                    print("\n✅ База данных удалена успешно!")
                    if backup_file:
                        print(f"💾 Резервная копия: {backup_file}")
                else:
                    print("\n❌ Ошибка при удалении базы данных")
            else:
                print("Операция отменена")
            return
            
        elif command == "reset":
            # Полное пересоздание БД (потеря данных!)
            print("⚠️  ВНИМАНИЕ: Это приведет к полной потере данных!")
            response = input("Продолжить? (yes/no): ").lower()
            if response == "yes":
                print("=== Полное пересоздание базы данных ===")
                
                # Создаем резервную копию перед удалением
                print("\n1. Создание резервной копии...")
                await backup_data()
                
                # Удаляем и пересоздаем БД
                print("\n2. Пересоздание базы данных...")
                await drop_database()
                await create_database()
                await create_tables()
                
                if await test_connection():
                    print("\n✅ База данных пересоздана успешно!")
                else:
                    print("\n❌ Ошибка при тестировании")
            else:
                print("Операция отменена")
            return
            
        elif command == "backup":
            # Создание резервной копии
            backup_file = await backup_data()
            if backup_file:
                print(f"✅ Резервная копия создана: {backup_file}")
            else:
                print("❌ Ошибка при создании резервной копии")
            return
            
        elif command == "restore":
            # Восстановление из резервной копии
            if len(sys.argv) < 3:
                print("Использование: python setup_database.py restore <backup_file>")
                return
                
            backup_file = sys.argv[2]
            if await restore_data(backup_file):
                print("✅ Данные восстановлены успешно!")
            else:
                print("❌ Ошибка при восстановлении данных")
            return
            
        elif command == "status":
            # Показать статус БД
            print("=== Статус базы данных ===")
            version = await get_current_schema_version()
            print(f"Версия схемы: {version}")
            
            if await test_connection():
                print("Статус подключения: ✅ OK")
            else:
                print("Статус подключения: ❌ Ошибка")
            return
            
        elif command == "help":
            print("""
=== Команды управления базой данных ===

python setup_database.py                - Первоначальная настройка БД
python setup_database.py update         - Обновить схему с сохранением данных
python setup_database.py migrate        - То же что и update
python setup_database.py drop           - УДАЛИТЬ базу данных полностью
python setup_database.py delete         - То же что и drop
python setup_database.py reset          - Полное пересоздание БД (потеря данных!)
python setup_database.py backup         - Создать резервную копию
python setup_database.py restore <file> - Восстановить из резервной копии
python setup_database.py status         - Показать статус БД
python setup_database.py help           - Показать эту справку

⚠️  ОПАСНЫЕ КОМАНДЫ (потеря данных):
   • drop/delete - полностью удаляет БД
   • reset       - пересоздает БД с нуля
            """)
            return
        else:
            print(f"Неизвестная команда: {command}")
            print("Используйте 'python setup_database.py help' для справки")
            return
    
    # Обычная настройка БД (первый запуск)
    print("=== Настройка базы данных Steam ===")
    
    # Шаг 1: Создание БД
    print("\n1. Создание базы данных...")
    if not await create_database():
        print("Не удалось создать базу данных. Завершение.")
        return
    
    # Шаг 2: Создание таблицы миграций
    print("\n2. Создание таблицы миграций...")
    await create_migration_table()
    
    # Шаг 3: Создание таблиц
    print("\n3. Создание таблиц...")
    if not await create_tables():
        print("Не удалось создать таблицы. Завершение.")
        return
    
    # Шаг 4: Записываем начальную версию схемы
    try:
        conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        
        initial_version = datetime.now().strftime("%Y.%m.%d_%H%M%S")
        await conn.execute("""
            INSERT INTO schema_migrations (version, description) 
            VALUES ($1, $2)
            ON CONFLICT (version) DO NOTHING
        """, initial_version, "Initial schema creation")
        
        await conn.close()
        print(f"Начальная версия схемы: {initial_version}")
        
    except Exception as e:
        print(f"Предупреждение: не удалось записать версию схемы: {e}")
    
    # Шаг 5: Тестирование
    print("\n4. Тестирование подключения...")
    if await test_connection():
        print("\n✅ База данных настроена успешно!")
        print(f"Можно использовать URL: {DATABASE_URL}")
        print("\nДоступные команды:")
        print("- python setup_database.py update  # Обновить схему")
        print("- python setup_database.py backup  # Создать резервную копию")
        print("- python setup_database.py help    # Показать все команды")
    else:
        print("\n❌ Ошибка при тестировании")


if __name__ == "__main__":
    asyncio.run(main())
