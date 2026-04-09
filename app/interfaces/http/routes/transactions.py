from datetime import datetime, timedelta
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.domain.entity.enums import AdminFeeType, TransactionStatus
from app.domain.entity.transactions import Transaction, TransactionLog
from app.domain.schema.transaction_schema import (
    TransactionCancelRequest,
    TransactionCreateRequest,
    TransactionPayRequest,
    TransactionRefundRequest,
    TransactionResponse,
)
from app.infrastructure.database.depedencies import get_async_primary_db
from app.infrastructure.database.repositories.payment_method import PaymentMethodRepository
from app.infrastructure.database.repositories.transactions import TransactionRepository

router = APIRouter()


@router.get("/")
async def get_all(
    page: int = 1,
    limit: int = 10,
    user_id: str | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: AsyncSession = Depends(get_async_primary_db),
):
    repo = TransactionRepository(db)
    page = max(page, 1)
    limit = max(min(limit, 100), 1)
    skip = (page - 1) * limit
    # TODO: apply user_id/status/date filters when service/domain logic is ready.
    conditions: list = []
    if user_id:
        conditions.append(["user_id", "=", user_id])
    if status:
        conditions.append(["status", "=", status])
    if date_from:
        conditions.append(["created_at", ">=", date_from])
    if date_to:
        conditions.append(["created_at", "<=", date_to])
    criteria = {"and": conditions} if conditions else None
    result = await repo.paginate(skip=skip, limit=limit, criteria=criteria, sortby=[["created_at", "desc"]])
    return {
        "data": [TransactionResponse.model_validate(item) for item in result["data"]],
        "meta": {
            "page": page,
            "limit": limit,
            "count": len(result["data"]),
            "total": result["metas"]["total"],
            "total_pages": result["metas"]["total_pages"],
            "filters": {
                "user_id": user_id,
                "status": status,
                "date_from": date_from,
                "date_to": date_to,
            },
        },
    }


@router.post("/")
async def post_transaction(payload: TransactionCreateRequest, db: AsyncSession = Depends(get_async_primary_db)):
    repo = TransactionRepository(db)
    total_amount = max(payload.subtotal - payload.discount_amount, 0)
    suffix = uuid.uuid4().hex[:10].upper()
    transaction = Transaction(
        application_id=payload.application_id,
        user_id=payload.user_id,
        voucher_id=payload.voucher_id,
        transaction_code=f"TRX-{suffix}",
        invoice_number=f"INV-{suffix}",
        status=TransactionStatus.PENDING,
        subtotal=payload.subtotal,
        discount_amount=payload.discount_amount,
        admin_fee=0,
        total_amount=total_amount,
        currency=payload.currency,
        notes=payload.notes,
    )
    created = await repo.create(transaction)
    return TransactionResponse.model_validate(created)

@router.get("/{transaction_id}")
async def get_transaction(transaction_id: str, db: AsyncSession = Depends(get_async_primary_db)):
    repo = TransactionRepository(db)
    transaction = await repo.get_by_id(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return TransactionResponse.model_validate(transaction)

@router.post("/{transaction_id}/pay", description="Pilih metode pembayaran & generate payment instruction")
async def post_transaction_pay(
    transaction_id: str,
    payload: TransactionPayRequest,
    db: AsyncSession = Depends(get_async_primary_db),
):
    transaction_repo = TransactionRepository(db)
    payment_method_repo = PaymentMethodRepository(db)
    transaction = await transaction_repo.get_by_id(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if transaction.status in [TransactionStatus.PAID, TransactionStatus.SETTLEMENT]:
        raise HTTPException(status_code=400, detail="Transaction already paid")

    method = await payment_method_repo.get_by_id(payload.payment_method_id)
    if not method or not method.is_active:
        raise HTTPException(status_code=404, detail="Payment method not found or inactive")

    if method.admin_fee_type == AdminFeeType.PERCENTAGE:
        admin_fee = transaction.subtotal * (method.admin_fee / 100)
    else:
        admin_fee = method.admin_fee
    total_amount = max(transaction.subtotal - transaction.discount_amount, 0) + admin_fee

    update_data = {
        "payment_method_id": payload.payment_method_id,
        "gateway_id": payload.gateway_id,
        "admin_fee": admin_fee,
        "total_amount": total_amount,
        "status": TransactionStatus.AWAITING_PAYMENT,
        "payment_reference": f"PAY-{uuid.uuid4().hex[:12].upper()}",
        "payment_url": f"/payments/{transaction_id}",
        "expired_at": datetime.utcnow() + timedelta(hours=24),
        "updated_at": datetime.utcnow(),
    }
    updated = await transaction_repo.update(transaction_id, update_data)
    return {
        "transaction_id": transaction_id,
        "status": updated.status,
        "payment_details": {
            "payment_url": updated.payment_url,
            "payment_reference": updated.payment_reference,
            "expired_at": updated.expired_at,
            "total_amount": updated.total_amount,
            "admin_fee": updated.admin_fee,
        },
    }

@router.get("/{transaction_id}/status")
async def get_transaction_status(transaction_id: str, db: AsyncSession = Depends(get_async_primary_db)):
    repo = TransactionRepository(db)
    transaction = await repo.get_by_id(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {
        "transaction_id": transaction.id,
        "status": transaction.status,
        "paid_at": transaction.paid_at,
        "expired_at": transaction.expired_at,
    }

@router.post("/{transaction_id}/cancel")
async def post_transaction_cancel(
    transaction_id: str,
    payload: TransactionCancelRequest,
    db: AsyncSession = Depends(get_async_primary_db),
):
    repo = TransactionRepository(db)
    transaction = await repo.get_by_id(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if transaction.status in [TransactionStatus.PAID, TransactionStatus.SETTLEMENT, TransactionStatus.REFUNDED]:
        raise HTTPException(status_code=400, detail="Paid/refunded transaction cannot be cancelled")

    updated = await repo.update(
        transaction_id,
        {
            "status": TransactionStatus.CANCELLED,
            "notes": payload.reason or transaction.notes,
            "updated_at": datetime.utcnow(),
        },
    )
    return {"transaction_id": transaction_id, "status": updated.status}

@router.post("/{transaction_id}/refund", description="Request refund transaksi")
async def post_transaction_refund(
    transaction_id: str,
    payload: TransactionRefundRequest,
    db: AsyncSession = Depends(get_async_primary_db),
):
    repo = TransactionRepository(db)
    transaction = await repo.get_by_id(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if transaction.status not in [TransactionStatus.PAID, TransactionStatus.SETTLEMENT]:
        raise HTTPException(status_code=400, detail="Only paid/settled transaction can be refunded")
    if payload.refund_amount > transaction.total_amount:
        raise HTTPException(status_code=400, detail="Refund amount exceeds total amount")

    updated = await repo.update(
        transaction_id,
        {
            "status": TransactionStatus.REFUNDED,
            "notes": payload.notes or payload.reason or transaction.notes,
            "updated_at": datetime.utcnow(),
        },
    )
    return {
        "transaction_id": transaction_id,
        "status": updated.status,
        "refund_amount": payload.refund_amount,
    }

@router.get("/{transaction_id}/invoice")
async def get_transaction_invoice(transaction_id: str, db: AsyncSession = Depends(get_async_primary_db)):
    repo = TransactionRepository(db)
    transaction = await repo.get_by_id(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {
        "invoice_number": transaction.invoice_number,
        "transaction_id": transaction.id,
        "user_id": transaction.user_id,
        "status": transaction.status,
        "subtotal": transaction.subtotal,
        "discount_amount": transaction.discount_amount,
        "admin_fee": transaction.admin_fee,
        "total_amount": transaction.total_amount,
        "currency": transaction.currency,
        "created_at": transaction.created_at,
    }


@router.post("/{transaction_id}/resend-instructions")
async def resend_payment_instructions(transaction_id: str, db: AsyncSession = Depends(get_async_primary_db)):
    repo = TransactionRepository(db)
    transaction = await repo.get_by_id(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if transaction.status not in [TransactionStatus.PENDING, TransactionStatus.AWAITING_PAYMENT]:
        raise HTTPException(status_code=400, detail="Instructions can only be resent for pending transactions")

    return {
        "transaction_id": transaction.id,
        "payment_reference": transaction.payment_reference,
        "payment_url": transaction.payment_url,
        "message": "Payment instructions resent",
    }


@router.get("/{transaction_id}/timeline")
async def get_transaction_timeline(transaction_id: str, db: AsyncSession = Depends(get_async_primary_db)):
    repo = TransactionRepository(db)
    transaction = await repo.get_by_id(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    statement = select(TransactionLog).where(TransactionLog.transaction_id == transaction_id).order_by(TransactionLog.created_at.asc())
    result = await db.execute(statement)
    logs = result.scalars().all()
    events = [
        {
            "type": "created",
            "status": transaction.status,
            "timestamp": transaction.created_at,
            "notes": "Transaction created",
        }
    ]
    for log in logs:
        events.append(
            {
                "type": "status_change",
                "from_status": log.previous_status,
                "to_status": log.new_status,
                "changed_by": log.changed_by,
                "timestamp": log.created_at,
                "notes": log.notes,
            }
        )

    return {"transaction_id": transaction_id, "events": events}


    