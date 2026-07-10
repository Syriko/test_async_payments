import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import AsyncSessionLocal
from app.models.outbox import Outbox, OutboxStatus
from app.core.rabbitmq import broker, PAYMENTS_EXCHANGE


async def publish_outbox_event(outbox: Outbox):
    # Перенос записи с outbox в rebbit
    try:
        await broker.publish(
            outbox.payload,
            exchange=PAYMENTS_EXCHANGE,
            routing_key='payments.new'
        )
        return True
    except Exception as ex:
        print(f'[Error] Outbox add event error {outbox.id}: {ex}')
        return False


async def outbox_publisher():
    # Фоновая функция
    while True:
        try:
            async with AsyncSessionLocal() as db:
                # Находим необработанные события
                result = await db.execute(
                    select(Outbox)
                    .where(Outbox.status == OutboxStatus.PENDING)
                    .order_by(Outbox.created_at)
                    .limit(100)
                )
                events = result.scalars().all()

                for event in events:
                    success = await publish_outbox_event(event)

                    if success:
                        # Обновляем статус на processed
                        await db.execute(
                            update(Outbox)
                            .where(Outbox.id == event.id)
                            .values(
                                status=OutboxStatus.PROCESSED,
                                processed_at=datetime.utcnow()
                            )
                        )
                    else:
                        # Увеличиваем счетчик ошибок
                        new_retry_count = event.retry_count + 1
                        if new_retry_count >= 3:
                            status = OutboxStatus.FAILED
                            error_msg = 'Max retry attempts exceeded'
                        else:
                            status = OutboxStatus.PENDING
                            error_msg = f'Retry attempt {new_retry_count}'

                        await db.execute(
                            update(Outbox)
                            .where(Outbox.id == event.id)
                            .values(
                                retry_count=new_retry_count,
                                status=status,
                                error_message=error_msg
                            )
                        )

                    await db.commit()
        except Exception as ex:
            print(f'[Error] Outbox error: {ex}')

        # Ждем перед следующим циклом
        await asyncio.sleep(5)
        
        
        


















