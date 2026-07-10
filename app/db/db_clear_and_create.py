import asyncio
import datetime
from decimal import Decimal

from sqlalchemy import text, Numeric, JSON
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.models.payment import Base


DATABASE_URL = 'postgresql+asyncpg://postgres:zzz500zzz@localhost:5432/test_payments'
engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=True,
)


async def connection_checker():
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text('SELECT 1'))
            print(result)
            print('[INFO] Подключение успешно!')
    except Exception as ex:
        print(f'Ошибка подключения: {ex}')


async def clear_and_create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


def main():
    asyncio.run(clear_and_create_db())


if __name__ == '__main__':
    main()
