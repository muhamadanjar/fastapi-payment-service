from datetime import datetime
import hashlib

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel.ext.asyncio.session import AsyncSession

from app.domain.entity.enums import CallbackType, ChangedBy, TransactionStatus
from app.domain.entity.payment_gateway import PaymentGatewayCallback
from app.domain.entity.transactions import TransactionLog
from app.infrastructure.database.depedencies import get_async_primary_db
from app.infrastructure.database.repositories.payment_gateway import (
    PaymentGatewayCallbackRepository,
    PaymentGatewayCredentialRepository,
    PaymentGatewayRepository,
)
from app.infrastructure.database.repositories.transactions import TransactionRepository

# Public callback endpoints from payment gateways.
callback_router = APIRouter()

# Internal webhook management endpoints.
management_router = APIRouter()


@callback_router.post("/payment/{gateway_code}")
async def payment(
    gateway_code: str,
    request: Request,
    db: AsyncSession = Depends(get_async_primary_db),
):
    payload = await request.json()
    gateway_repo = PaymentGatewayRepository(db)
    callback_repo = PaymentGatewayCallbackRepository(db)
    credential_repo = PaymentGatewayCredentialRepository(db)
    transaction_repo = TransactionRepository(db)

    gateway = await gateway_repo.get_by_code(gateway_code)
    if not gateway:
        raise HTTPException(status_code=404, detail="Gateway not found")

    order_id = payload.get("order_id") or payload.get("external_id") or payload.get("reference_id")
    if not order_id:
        raise HTTPException(status_code=400, detail="Missing transaction identifier in payload")

    transaction = (
        await transaction_repo.get_by_invoice_number(order_id)
        or await transaction_repo.get_by_transaction_code(order_id)
        or await transaction_repo.get_by_payment_reference(order_id)
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    credential = await credential_repo.get_active_credential(
        application_id=transaction.application_id,
        gateway_id=gateway.id,
    )

    signature = (
        request.headers.get("signature_key")
        or request.headers.get("x-signature-key")
        or request.headers.get("x-callback-token")
        or payload.get("signature_key")
    )
    is_signature_valid = True

    if credential:
        gateway_code_lower = gateway_code.lower()
        if "midtrans" in gateway_code_lower and credential.api_key:
            status_code = str(payload.get("status_code", ""))
            gross_amount = str(payload.get("gross_amount", payload.get("amount", "")))
            expected = hashlib.sha512(f"{order_id}{status_code}{gross_amount}{credential.api_key}".encode()).hexdigest()
            is_signature_valid = (signature or "").lower() == expected.lower()
        elif "xendit" in gateway_code_lower and credential.webhook_secret:
            callback_token = request.headers.get("x-callback-token", "")
            is_signature_valid = callback_token == credential.webhook_secret

    callback = PaymentGatewayCallback(
        transaction_id=transaction.id,
        gateway_id=gateway.id,
        callback_type=CallbackType.PAYMENT_NOTIFICATION,
        raw_payload=payload,
        signature=signature,
        is_signature_valid=is_signature_valid,
        is_processed=False,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    saved_callback = await callback_repo.create(callback)

    if not is_signature_valid:
        await callback_repo.update(
            saved_callback.id,
            {"notes": "Invalid signature/token", "processed_at": datetime.utcnow()},
        )
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    status_raw = (payload.get("transaction_status") or payload.get("status") or "").lower()
    status_mapping = {
        "pending": TransactionStatus.AWAITING_PAYMENT,
        "awaiting_payment": TransactionStatus.AWAITING_PAYMENT,
        "settlement": TransactionStatus.SETTLEMENT,
        "paid": TransactionStatus.PAID,
        "capture": TransactionStatus.PAID,
        "expire": TransactionStatus.EXPIRED,
        "expired": TransactionStatus.EXPIRED,
        "cancel": TransactionStatus.CANCELLED,
        "cancelled": TransactionStatus.CANCELLED,
        "failure": TransactionStatus.FAILED,
        "failed": TransactionStatus.FAILED,
        "refund": TransactionStatus.REFUNDED,
        "refunded": TransactionStatus.REFUNDED,
    }
    new_status = status_mapping.get(status_raw, transaction.status)

    update_data = {
        "status": new_status,
        "updated_at": datetime.utcnow(),
    }
    if new_status in [TransactionStatus.PAID, TransactionStatus.SETTLEMENT]:
        update_data["paid_at"] = datetime.utcnow()

    updated_transaction = await transaction_repo.update(transaction.id, update_data)
    await callback_repo.update(
        saved_callback.id,
        {
            "is_processed": True,
            "processed_at": datetime.utcnow(),
            "notes": f"Transaction updated to {updated_transaction.status}",
        },
    )

    log = TransactionLog(
        transaction_id=transaction.id,
        previous_status=transaction.status,
        new_status=updated_transaction.status,
        changed_by=ChangedBy.GATEWAY,
        gateway_callback_id=saved_callback.id,
        notes=f"Webhook from {gateway.gateway_code}",
        log_metadata={"payload": payload},
    )
    db.add(log)
    await db.commit()

    return {"message": "accepted", "gateway_code": gateway_code, "transaction_id": transaction.id}


@callback_router.post("/test")
async def test(request: Request):
    payload = await request.json()
    return {"message": "webhook test accepted", "payload": payload}


@management_router.get("/logs")
async def logs(
    gateway_id: str | None = None,
    is_success: bool | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
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
    if is_success is not None:
        conditions.append(["is_processed", "=", is_success])
    if date_from:
        conditions.append(["created_at", ">=", date_from])
    if date_to:
        conditions.append(["created_at", "<=", date_to])
    criteria = {"and": conditions} if conditions else None

    result = await repo.paginate(skip=skip, limit=limit, criteria=criteria, sortby=[["created_at", "desc"]])
    return {"data": result["data"], "meta": result["metas"]}


@management_router.post("/{id}/retry")
async def webhook_retry(id: str, db: AsyncSession = Depends(get_async_primary_db)):
    callback_repo = PaymentGatewayCallbackRepository(db)
    callback = await callback_repo.get_by_id(id)
    if not callback:
        raise HTTPException(status_code=404, detail="Webhook log not found")

    payload = callback.raw_payload or {}
    status_raw = (payload.get("transaction_status") or payload.get("status") or "").lower()
    status_mapping = {
        "pending": TransactionStatus.AWAITING_PAYMENT,
        "awaiting_payment": TransactionStatus.AWAITING_PAYMENT,
        "settlement": TransactionStatus.SETTLEMENT,
        "paid": TransactionStatus.PAID,
        "capture": TransactionStatus.PAID,
        "expire": TransactionStatus.EXPIRED,
        "expired": TransactionStatus.EXPIRED,
        "cancel": TransactionStatus.CANCELLED,
        "cancelled": TransactionStatus.CANCELLED,
        "failure": TransactionStatus.FAILED,
        "failed": TransactionStatus.FAILED,
        "refund": TransactionStatus.REFUNDED,
        "refunded": TransactionStatus.REFUNDED,
    }

    tx_repo = TransactionRepository(db)
    tx = await tx_repo.get_by_id(callback.transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Related transaction not found")

    new_status = status_mapping.get(status_raw, tx.status)
    await tx_repo.update(tx.id, {"status": new_status, "updated_at": datetime.utcnow()})
    await callback_repo.update(id, {"is_processed": True, "processed_at": datetime.utcnow(), "notes": "Retried manually"})
    return {"message": "retry requested", "webhook_id": id, "applied_status": new_status}