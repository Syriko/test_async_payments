from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import String, Numeric, Text, JSON, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base
import enum


class PaymentStatus(str, enum.Enum):
    PENDING = 'pending'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'


class Currency(str, enum.Enum):
    RUB = 'RUB'
    USD = 'USD'
    EUR = 'EUR'


class Payment(Base):
    __tablename__ = 'payments'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[Currency] = mapped_column(SQLEnum(Currency), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    additional_metadata: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)
    status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus),
        default=PaymentStatus.PENDING
    )
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    webhook_url: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'amount': float(self.amount),
            'currency': self.currency.value,
            'description': self.description,
            'additional_metadata': self.additional_metadata,
            'status': self.status.value,
            'idempotency_key': self.idempotency_key,
            'webhook_url': self.webhook_url,
            'created_at': self.created_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }

























