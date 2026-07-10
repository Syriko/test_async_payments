import asyncio
import random
from datetime import datetime
from uuid import UUID
from sqlalchemy import select, update
from app.db.database import AsyncSessionLocal
from app.core.rabbitmq import (broker, PAYMENTS_QUEUE, PAYMENTS_DLQ,
                               PAYMENTS_RETRY_1S, PAYMENTS_RETRY_2S,
                               PAYMENTS_RETRY_4S)
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import WebhookPayload
from app.services.webhook_service import send_webhook
from app.core.config import settings


class PaymentProcessor:

    @staticmethod
    async def get_payment(payment_id: UUID):
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Payment).where(Payment.id == payment_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def update_payment_status(payment_id: UUID, status: PaymentStatus):
        async with AsyncSessionLocal() as db:
            await db.execute(
                update(Payment)
                .where(Payment.id == payment_id)
                .values(
                    status=status,
                    processed_at=datetime.utcnow()
                )
            )
            await db.commit()

    @staticmethod
    async def process_payment(payment: Payment):
        # Эмуляция обработки платежа
        # Создаем задержку 2-5 секунд
        delay = random.uniform(2, 5)
        await asyncio.sleep(delay)

        # 90% успеха, 10% ошибка
        if random.random() < 0.9:
            return PaymentStatus.SUCCEEDED, True
        else:
            return PaymentStatus.FAILED, False

    @staticmethod
    async def send_webhook_notification(
            payment_id: UUID,
            status: PaymentStatus,
            amount: float,
            currency: str
    ):
        webhook_payload = WebhookPayload(
            payment_id=payment_id,
            status=status,
            amount=amount,
            currency=currency,
            processed_at=datetime.utcnow()
        )
        payment = await PaymentProcessor.get_payment(payment_id)
        if not payment:
            print(f'[Error] Payment {payment_id} not found for webhook')
            return False

        return await send_webhook(payment.webhook_url, webhook_payload)

    @staticmethod
    async def handle_retry(payment_id: UUID, retry_count: int):
        # Повторный обработчик транзакции с задержкой
        if retry_count >= 3:
            print(f'[INFO] Payment {payment_id} moved to DLQ after {retry_count} attempts')
            await broker.publish(
                {'payment_id': str(payment_id)},
                exchange='payments.dlx',
                routing_key='payments.dlq'
            )
            return False

        # Выбираем очередь для повторной попытки в зависимости от количества
        delay_queues = [
            PAYMENTS_RETRY_1S,
            PAYMENTS_RETRY_2S,
            PAYMENTS_RETRY_4S
        ]

        queue = delay_queues[min(retry_count, len(delay_queues) - 1)]
        await broker.publish(
            {'payment_id': str(payment_id), 'retry_count': retry_count + 1},
            exchange='payments.exchange',
            routing_key=queue.name
        )

        print(f'[INFO] Payment {payment_id} scheduled for retry №{retry_count + 1}')
        return True


@broker.subscriber(PAYMENTS_QUEUE)
async def process_payment_message(message: dict) -> None:
    payment_id = UUID(message.get('payment_id'))
    retry_count = message.get('retry_count', 0)

    print(f'[INFO] Processing payment {payment_id}, attempt №{retry_count}')

    # Получаем платеж из БД
    payment = await PaymentProcessor.get_payment(payment_id)
    if not payment:
        print(f'[Error] Payment {payment_id} not found')
        return

    # Проверяем, не обработан ли уже платеж
    if payment.status != PaymentStatus.PENDING:
        print(f'[INFO] Payment {payment_id} already processed, status {payment.status}')
        return

    try:
        # Эмулируем обработку платежа
        status, success = await PaymentProcessor.process_payment(payment)

        if not success:
            print(f'[Error] Payment {payment_id} processing failed, retrying')
            if retry_count >= 2:
                await PaymentProcessor.update_payment_status(payment_id, PaymentStatus.FAILED)
                print(f'[Error] Payment {payment_id} failed after 3 attempts')
                return

            # Планируем повторную попытку
            await PaymentProcessor.handle_retry(payment_id, retry_count)
            return

        # Успешная обработка
        await PaymentProcessor.update_payment_status(payment_id, status)

        # Отправляем webhook
        webhook_success = await PaymentProcessor.send_webhook_notification(
            payment_id=payment_id,
            status=status,
            amount=payment.amount,
            currency=payment.currency.value
        )

        if not webhook_success:
            # Если webhook не удался, пробуем повторно
            print(f'[Error] Webhook failed for payment {payment_id}, retrying')
            await PaymentProcessor.handle_retry(payment_id, retry_count)
            return

        print(f'[INFO] Payment {payment_id} processed successfully')

    except Exception as ex:
        print(f'[Error] Error processing payment {payment_id}: {ex}')
        if retry_count < 2:
            await PaymentProcessor.handle_retry(payment_id, retry_count)
        else:
            await PaymentProcessor.update_payment_status(payment_id, PaymentStatus.FAILED)


@broker.subscriber(PAYMENTS_RETRY_1S)
@broker.subscriber(PAYMENTS_RETRY_2S)
@broker.subscriber(PAYMENTS_RETRY_4S)
async def process_retry_message(message: dict):
    # Перенаправление в основную очередь
    payment_id = UUID(message.get('payment_id'))
    retry_count = message.get('retry_count', 0)

    await broker.publish(
        {'payment_id': str(payment_id), 'retry_count': retry_count},
        exchange='payments.exchange',
        routing_key='payments.new'
    )

    print(f'[INFO] Retry message for payment {payment_id}')


@broker.subscriber(PAYMENTS_DLQ)
async def process_dlq_message(message: dict) -> None:
    # Обработчик неуспешных запросов
    payment_id = message.get('payment_id')
    print(f'Payment {payment_id} moved to DLQ - check why')


async def main():
    print(f'[INFO] Start')

    await broker.declare_exchange('payments.exchange')
    await broker.declare_exchange('payments.dlx')
    await broker.declare_queue(PAYMENTS_QUEUE)
    await broker.declare_queue(PAYMENTS_DLQ)
    await broker.declare_queue(PAYMENTS_RETRY_1S)
    await broker.declare_queue(PAYMENTS_RETRY_2S)
    await broker.declare_queue(PAYMENTS_RETRY_4S)
    await broker.start()

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await broker.close()


if __name__ == '__main__':
    asyncio.run(main())
