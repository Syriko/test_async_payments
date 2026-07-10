from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime
from app.models.payment import Payment, PaymentStatus
from app.models.outbox import Outbox, OutboxStatus
from app.schemas.payment import PaymentCreate


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_payment(self, payment_data: PaymentCreate, idempotency_key: str):
        # Проверяем существующий платеж с таким idempotency_key
        existing = await self.get_payment_by_idempotency_key(idempotency_key)
        if existing:
            return existing

        # Создаем новый платеж
        payment = Payment(
            amount=payment_data.amount,
            currency=payment_data.currency.value,
            description=payment_data.description,
            metadata=payment_data.metadata or {},
            idempotency_key=idempotency_key,
            webhook_url=str(payment_data.webhook_url),
            status=PaymentStatus.PENDING
        )

        self.db.add(payment)

        # Создаем запись в outbox
        outbox_event = Outbox(
            event_type='payment.created',
            payload={'payment_id': str(payment.id)},
            status=OutboxStatus.PENDING
        )
        self.db.add(outbox_event)

        # Сохраняем всё в одной транзакции
        await self.db.commit()
        await self.db.refresh(payment)

        return payment

    async def get_payment(self, payment_id: UUID):
        result = await self.db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def get_payment_by_idempotency_key(self, key: str):
        result = await self.db.execute(
            select(Payment).where(Payment.idempotency_key == key)
        )
        return result.scalar_one_or_none()

    async def update_payment_status(
            self,
            payment_id: UUID,
            status: PaymentStatus,
            processed_at: datetime = None
    ):
        payment = await self.get_payment(payment_id)
        if payment:
            payment.status = status
            if processed_at:
                payment.processed_at = processed_at
            elif status in [PaymentStatus.SUCCEEDED, PaymentStatus.FAILED]:
                payment.processed_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(payment)


        return payment
    
    
    
    
    
    
    


















