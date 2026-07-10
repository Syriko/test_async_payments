from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class Currency(str, Enum):
    RUB = 'RUB'
    USD = 'USD'
    EUR = 'EUR'


class PaymentStatus(str, Enum):
    PENDING = 'pending'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'


class PaymentCreate(BaseModel):
    amount: float = Field(gt=0, description='Сумма платежа')
    currency: Currency = Field(description='Валюта')
    description: str = Field(min_length=1, max_length=500, description='Описание')
    additional_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description='Метаданные')
    webhook_url: HttpUrl = Field(description='URL для уведомлений')

    model_config = ConfigDict(use_enum_values=True)


class PaymentResponse(BaseModel):
    id: UUID
    status: PaymentStatus
    created_at: datetime

    model_config = ConfigDict(use_enum_values=True, from_attributes=True)


class PaymentDetailResponse(BaseModel):
    id: UUID
    amount: float
    currency: Currency
    description: str
    additional_metadata: Optional[Dict[str, Any]]
    status: PaymentStatus
    idempotency_key: str
    webhook_url: str
    created_at: datetime
    processed_at: Optional[datetime]

    model_config = ConfigDict(use_enum_values=True, from_attributes=True)


class WebhookPayload(BaseModel):
    payment_id: UUID
    status: PaymentStatus
    amount: float
    currency: Currency
    processed_at: datetime




























    