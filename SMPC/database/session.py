import os
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Получаем параметры подключения из переменных окружения
DB_USER = os.getenv("DB_USER", "test_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "13579")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "steam_db")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def create_session_factory() -> sessionmaker:
    engine = create_async_engine(
        url=DATABASE_URL,
        pool_size=10,
        max_overflow=10,
        echo=False,
        future=True,
        
    )
    return sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

@asynccontextmanager
async def get_session(session_factory: sessionmaker) -> AsyncSession:
    async with session_factory() as session:
        yield session