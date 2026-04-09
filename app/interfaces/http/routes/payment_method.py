from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entity.enums import AdminFeeType
from app.domain.schema.payment_method_schema import (
    CalculateFeeRequest,
    CalculateFeeResponse,
    PaymentMethodResponse,
)
from app.infrastructure.database.depedencies import get_async_primary_db
from app.infrastructure.database.repositories.payment_method import PaymentMethodRepository

router = APIRouter()


@router.get("/", name="List metode pembayaran available")
async def get_all(type: str | None = None, db: AsyncSession = Depends(get_async_primary_db)):
    repo = PaymentMethodRepository(db)
    methods = await repo.get_active(method_type=type)
    return {"data": [PaymentMethodResponse.model_validate(item) for item in methods], "filter": {"type": type}}

@router.get("/{id}", name="Detail metode pembayaran")
async def get_detail(id: str, db: AsyncSession = Depends(get_async_primary_db)):
    repo = PaymentMethodRepository(db)
    method = await repo.get_by_id(id)
    if not method:
        return {"message": "Payment method not found", "payment_method_id": id}
    return PaymentMethodResponse.model_validate(method)

@router.post("/{id}/calculate-fee", name="Hitung admin fee untuk amount tertentu")
async def calculate_fee(
    id: str,
    payload: CalculateFeeRequest,
    db: AsyncSession = Depends(get_async_primary_db),
):
    repo = PaymentMethodRepository(db)
    method = await repo.get_by_id(id)
    if not method:
        return {"message": "Payment method not found", "payment_method_id": id}

    if method.admin_fee_type == AdminFeeType.PERCENTAGE:
        admin_fee = payload.amount * (method.admin_fee / 100)
    else:
        admin_fee = method.admin_fee

    total_with_fee = payload.amount + admin_fee
    return CalculateFeeResponse(
        payment_method_id=method.id,
        amount=payload.amount,
        admin_fee=admin_fee,
        total_with_fee=total_with_fee,
    )