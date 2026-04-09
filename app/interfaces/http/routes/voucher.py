from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entity.voucher import Voucher, VoucherCondition
from app.domain.schema.voucher_schema import (
    VoucherClaimRequest,
    VoucherConditionCreateRequest,
    VoucherCreateRequest,
    VoucherResponse,
    VoucherUpdateRequest,
    VoucherValidateRequest,
    VoucherValidateResponse,
)
from app.infrastructure.database.depedencies import get_async_primary_db
from app.infrastructure.database.repositories.voucher import (
    VoucherConditionRepository,
    VoucherEligibleUserRepository,
    VoucherRepository,
)

router = APIRouter()

def _calculate_discount(discount_type: str, discount_value: float, amount: float, max_discount: float | None) -> float:
    if discount_type == "percentage":
        discount = amount * (discount_value / 100)
    else:
        discount = discount_value
    if max_discount is not None:
        discount = min(discount, max_discount)
    return max(discount, 0)


@router.post("/validate")
async def post_validate(payload: VoucherValidateRequest, db: AsyncSession = Depends(get_async_primary_db)):
    voucher_repo = VoucherRepository(db)
    eligible_repo = VoucherEligibleUserRepository(db)
    voucher = await voucher_repo.get_by_code(payload.voucher_code)
    now = datetime.utcnow()

    if not voucher:
        return VoucherValidateResponse(is_valid=False, error_message="Voucher not found")
    if not voucher.is_active:
        return VoucherValidateResponse(is_valid=False, error_message="Voucher is inactive")
    if voucher.valid_from and voucher.valid_from > now:
        return VoucherValidateResponse(is_valid=False, error_message="Voucher is not active yet")
    if voucher.valid_until and voucher.valid_until < now:
        return VoucherValidateResponse(is_valid=False, error_message="Voucher has expired")
    if payload.transaction_amount < voucher.min_transaction:
        return VoucherValidateResponse(is_valid=False, error_message="Minimum transaction not reached")
    if voucher.usage_limit is not None and voucher.usage_count >= voucher.usage_limit:
        return VoucherValidateResponse(is_valid=False, error_message="Voucher usage limit exceeded")

    if voucher.voucher_type == "private":
        if not payload.user_id:
            return VoucherValidateResponse(is_valid=False, error_message="user_id is required for private voucher")
        eligible = await eligible_repo.get_by_voucher_and_user(voucher.id, payload.user_id)
        if not eligible:
            return VoucherValidateResponse(is_valid=False, error_message="User is not eligible for this voucher")

    discount_amount = _calculate_discount(
        discount_type=voucher.discount_type,
        discount_value=voucher.discount_value,
        amount=payload.transaction_amount,
        max_discount=voucher.max_discount,
    )
    return VoucherValidateResponse(
        is_valid=True,
        discount_amount=discount_amount,
        voucher_details=VoucherResponse.model_validate(voucher).model_dump(),
    )


@router.get("/my-vouchers")
async def get_myvoucher(
    user_id: str | None = None,
    is_claimed: bool | None = None,
    is_expired: bool | None = None,
    db: AsyncSession = Depends(get_async_primary_db),
):
    repo = VoucherEligibleUserRepository(db)
    data = await repo.list_by_user(user_id=user_id, is_claimed=is_claimed, is_expired=is_expired)
    return {
        "data": data,
        "filters": {
            "user_id": user_id,
            "is_claimed": is_claimed,
            "is_expired": is_expired,
        },
    }


@router.post("/{id}/claim")
async def post_claim(id: str, payload: VoucherClaimRequest, db: AsyncSession = Depends(get_async_primary_db)):
    repo = VoucherEligibleUserRepository(db)
    eligible = await repo.get_by_voucher_and_user(voucher_id=id, user_id=payload.user_id)
    if not eligible:
        raise HTTPException(status_code=404, detail="Eligible voucher for user not found")
    if eligible.is_claimed:
        return {"message": "Voucher already claimed", "voucher_id": id, "user_id": payload.user_id}

    updated = await repo.update(
        eligible.id,
        {
            "is_claimed": True,
            "claimed_at": datetime.utcnow(),
        },
    )
    return {"message": "Voucher claimed", "data": updated}


@router.get("/public")
async def get_public(db: AsyncSession = Depends(get_async_primary_db)):
    repo = VoucherRepository(db)
    data = await repo.get_active_public()
    return {"data": [VoucherResponse.model_validate(item) for item in data]}


@router.post("/")
async def post_create_voucher(payload: VoucherCreateRequest, db: AsyncSession = Depends(get_async_primary_db)):
    repo = VoucherRepository(db)
    voucher = Voucher(**payload.model_dump())
    data = await repo.create(voucher)
    return VoucherResponse.model_validate(data)


@router.put("/{id}")
async def put_detail(id: str, payload: VoucherUpdateRequest, db: AsyncSession = Depends(get_async_primary_db)):
    repo = VoucherRepository(db)
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    update_data["updated_at"] = datetime.utcnow()
    data = await repo.update(id, update_data)
    if not data:
        raise HTTPException(status_code=404, detail="Voucher not found")
    return VoucherResponse.model_validate(data)


@router.post("/{id}/conditions")
async def post_conditions(
    id: str,
    payload: VoucherConditionCreateRequest,
    db: AsyncSession = Depends(get_async_primary_db),
):
    voucher_repo = VoucherRepository(db)
    condition_repo = VoucherConditionRepository(db)

    voucher = await voucher_repo.get_by_id(id)
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")

    condition = VoucherCondition(voucher_id=id, **payload.model_dump())
    data = await condition_repo.create(condition)
    return {"message": "Condition added", "data": data}


@router.get("/{id}/eligible-users")
async def get_eligible_users(id: str, db: AsyncSession = Depends(get_async_primary_db)):
    repo = VoucherEligibleUserRepository(db)
    data = await repo.list_by_voucher(voucher_id=id)
    return {"data": data, "voucher_id": id}
