from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import String, JSON, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base
import enum


class OutboxStatus(str, enum.Enum):
    PENDING = 'pending'
    PROCESSED = 'processed'
    FAILED = 'failed'


class Outbox(Base):
    __tablename__ = 'outbox'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[OutboxStatus] = mapped_column(
        SQLEnum(OutboxStatus),
        default=OutboxStatus.PENDING
    )
    retry_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str] = mapped_column(String(512), nullable=True)












