from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.config import settings
from app.db.database import get_db
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentDetailResponse
from app.services.payment_service import PaymentService

router = APIRouter(prefix='/api/v1', tags=['payments'])


async def verify_api_key(x_api_key):
    """Проверка статического API ключа"""
    if x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return x_api_key


@router.post(
    '/payments',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=PaymentResponse
)
async def create_payment(
        payment_data: PaymentCreate,
        idempotency_key,
        api_key: str = Depends(verify_api_key),
        db: AsyncSession = Depends(get_db)
):
    '''
    Создание нового платежа.
    Использует Idempotency-Key для защиты от дублей.
    '''
    service = PaymentService(db)

    try:
        payment = await service.create_payment(
            payment_data=payment_data,
            idempotency_key=idempotency_key
        )
        return PaymentResponse(
            id=payment.id,
            status=payment.status,
            created_at=payment.created_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    '/payments/{payment_id}',
    response_model=PaymentDetailResponse
)
async def get_payment(
        payment_id: UUID,
        api_key: str = Depends(verify_api_key),
        db: AsyncSession = Depends(get_db)
):
    '''
    Получение детальной информации о платеже.
    '''
    service = PaymentService(db)
    payment = await service.get_payment(payment_id)

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Payment not found'
        )

    return payment





