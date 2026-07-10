import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.v1.payments import router
from app.core.rabbitmq import broker
from app.db.database import engine
from app.models import payment, outbox
from app.services.outbox_service import outbox_publisher


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создаем таблицы при старте (в проде использовать Alembic)
    async with engine.begin() as conn:
        await conn.run_sync(payment.Base.metadata.create_all)
        await conn.run_sync(outbox.Base.metadata.create_all)

    # Запускаем брокер и outbox publisher
    await broker.start()

    # Запускаем outbox publisher в фоновом режиме
    await asyncio.create_task(outbox_publisher())

    yield

    # Останавливаем брокер при завершении
    await broker.close()


app = FastAPI(
    title='Payment Service',
    description='Асинхронный сервис платежей',
    version='1.0.0',
    lifespan=lifespan
)

app.include_router(router)


@app.get('/health')
async def health_check():
    return {'status': 'ok', 'service': 'payment-service'}




















