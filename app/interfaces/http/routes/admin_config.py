from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_roles
from app.domain.entity.transactions import Transaction
from app.domain.entity.voucher import VoucherEligibleUser
from app.domain.schema.admin_schema import (
    ApplicationUpdateRequest,
    AssignVoucherUsersRequest,
    ForceTransactionStatusRequest,
)
from app.infrastructure.database.depedencies import get_async_primary_db
from app.infrastructure.database.repositories.application import ApplicationRepository
from app.infrastructure.database.repositories.payment_gateway import (
    PaymentGatewayCallbackRepository,
    PaymentGatewayRequestRepository,
)
from app.infrastructure.database.repositories.transactions import TransactionRepository
from app.infrastructure.database.repositories.voucher import (
    VoucherEligibleUserRepository,
    VoucherRepository,
)

# Admin-only: all routes here require an administrative role (ADMIN_ROLES env).
router = APIRouter(dependencies=[Depends(require_roles())])


@router.get("/applications")
async def get_applications(
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_async_primary_db),
):
    repo = ApplicationRepository(db)
    page = max(page, 1)
    limit = max(min(limit, 100), 1)
    skip = (page - 1) * limit
    data = await repo.get_all(skip=skip, limit=limit)
    return {"data": data, "meta": {"page": page, "limit": limit, "count": len(data)}}


@router.put("/applications/{id}")
async def update_application(
    id: str,
    payload: ApplicationUpdateRequest,
    db: AsyncSession = Depends(get_async_primary_db),
):
    repo = ApplicationRepository(db)
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    if "metadata" in update_data:
        update_data["app_metadata"] = update_data.pop("metadata")
    update_data["updated_at"] = datetime.utcnow()
    updated = await repo.update(id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Application not found")
    return updated


@router.post("/applications/{id}/regenerate-keys")
async def regenerate_keys(id: str, db: AsyncSession = Depends(get_async_primary_db)):
    repo = ApplicationRepository(db)
    updated = await repo.regenerate_keys(id)
    if not updated:
        raise HTTPException(status_code=404, detail="Application not found")
    return {
        "application_id": updated.id,
        "app_key": updated.app_key,
        "app_secret": updated.app_secret,
    }


@router.post("/transactions/{id}/force-status")
async def force_transaction_status(
    id: str,
    payload: ForceTransactionStatusRequest,
    db: AsyncSession = Depends(get_async_primary_db),
):
    repo = TransactionRepository(db)
    transaction = await repo.get_by_id(id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    updated = await repo.update(
        id,
        {
            "status": payload.new_status,
            "notes": payload.reason or transaction.notes,
            "updated_at": datetime.utcnow(),
        },
    )
    return {"transaction_id": id, "status": updated.status}


@router.get("/callbacks")
async def get_callbacks(
    gateway_id: str | None = None,
    is_processed: bool | None = None,
    is_signature_valid: bool | None = None,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_async_primary_db),
):
    repo = PaymentGatewayCallbackRepository(db)
    page = max(page, 1)
    limit = max(min(limit, 100), 1)
    skip = (page - 1) * limit

    conditions: list = []
    if gateway_id:
        conditions.append(["gateway_id", "=", gateway_id])
    if is_processed is not None:
        conditions.append(["is_processed", "=", is_processed])
    if is_signature_valid is not None:
        conditions.append(["is_signature_valid", "=", is_signature_valid])

    criteria = {"and": conditions} if conditions else None
    result = await repo.paginate(skip=skip, limit=limit, criteria=criteria, sortby=[["created_at", "desc"]])
    return {"data": result["data"], "meta": result["metas"]}


@router.post("/vouchers/{id}/assign-users")
async def assign_voucher_users(
    id: str,
    payload: AssignVoucherUsersRequest,
    db: AsyncSession = Depends(get_async_primary_db),
):
    voucher_repo = VoucherRepository(db)
    eligible_repo = VoucherEligibleUserRepository(db)
    voucher = await voucher_repo.get_by_id(id)
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")

    created = 0
    skipped = 0
    for user_id in payload.user_ids:
        existing = await eligible_repo.get_by_voucher_and_user(voucher_id=id, user_id=user_id)
        if existing:
            skipped += 1
            continue
        entity = VoucherEligibleUser(
            voucher_id=id,
            user_id=user_id,
            application_id=payload.application_id,
            expires_at=payload.expires_at,
        )
        await eligible_repo.create(entity)
        created += 1

    return {"voucher_id": id, "created": created, "skipped": skipped}


@router.get("/health")
async def admin_health(db: AsyncSession = Depends(get_async_primary_db)):
    stmt = select(func.count()).select_from(Transaction)
    result = await db.execute(stmt)
    total_transactions = result.scalar() or 0
    return {
        "status": "healthy",
        "database": "connected",
        "summary": {"total_transactions": total_transactions},
    }


@router.get("/reconciliation")
async def get_reconciliation(
    date: str | None = None,
    gateway_id: str | None = None,
    db: AsyncSession = Depends(get_async_primary_db),
):
    tx_repo = TransactionRepository(db)
    req_repo = PaymentGatewayRequestRepository(db)

    tx_conditions: list = []
    req_conditions: list = []
    if date:
        tx_conditions.append(["created_at", ">=", date])
        req_conditions.append(["created_at", ">=", date])
    if gateway_id:
        tx_conditions.append(["gateway_id", "=", gateway_id])
        req_conditions.append(["gateway_id", "=", gateway_id])

    tx_criteria = {"and": tx_conditions} if tx_conditions else None
    req_criteria = {"and": req_conditions} if req_conditions else None
    tx_count = await tx_repo.count_filtered(criteria=tx_criteria)
    req_count = await req_repo.count_filtered(criteria=req_criteria)

    matched = min(tx_count or 0, req_count or 0)
    return {
        "matched_transactions": matched,
        "unmatched_transactions": abs((tx_count or 0) - (req_count or 0)),
        "filters": {"date": date, "gateway_id": gateway_id},
    }
