from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entity.transactions import Transaction
from app.domain.entity.voucher import VoucherUsage
from app.infrastructure.database.depedencies import get_async_primary_db

reports_router = APIRouter()
analytics_router = APIRouter()


@reports_router.get("/transactions")
async def report_transactions(
    date_from: str | None = None,
    date_to: str | None = None,
    status: str | None = None,
    payment_method: str | None = None,
    format: str = "json",
    db: AsyncSession = Depends(get_async_primary_db),
):
    statement = select(Transaction)
    if date_from:
        statement = statement.where(Transaction.created_at >= date_from)
    if date_to:
        statement = statement.where(Transaction.created_at <= date_to)
    if status:
        statement = statement.where(Transaction.status == status)
    if payment_method:
        statement = statement.where(Transaction.payment_method_id == payment_method)
    result = await db.execute(statement)
    rows = result.scalars().all()
    return {"format": format, "total": len(rows), "data": rows}


@reports_router.get("/revenue")
async def report_revenue(
    date_from: str | None = None,
    date_to: str | None = None,
    group_by: str = "day",
    db: AsyncSession = Depends(get_async_primary_db),
):
    statement = select(Transaction)
    if date_from:
        statement = statement.where(Transaction.created_at >= date_from)
    if date_to:
        statement = statement.where(Transaction.created_at <= date_to)
    result = await db.execute(statement)
    rows = result.scalars().all()

    buckets: dict[str, float] = {}
    for row in rows:
        dt: datetime = row.created_at
        if group_by == "month":
            key = dt.strftime("%Y-%m")
        elif group_by == "week":
            key = f"{dt.isocalendar().year}-W{dt.isocalendar().week:02d}"
        else:
            key = dt.strftime("%Y-%m-%d")
        buckets[key] = buckets.get(key, 0) + float(row.total_amount)

    return {"group_by": group_by, "revenue_breakdown": buckets}


@reports_router.get("/vouchers")
async def report_vouchers(
    voucher_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: AsyncSession = Depends(get_async_primary_db),
):
    statement = select(VoucherUsage)
    if voucher_id:
        statement = statement.where(VoucherUsage.voucher_id == voucher_id)
    if date_from:
        statement = statement.where(VoucherUsage.used_at >= date_from)
    if date_to:
        statement = statement.where(VoucherUsage.used_at <= date_to)
    result = await db.execute(statement)
    rows = result.scalars().all()
    return {"total_usage": len(rows), "data": rows}


@reports_router.get("/payment-methods")
async def report_payment_methods(
    date_from: str | None = None,
    date_to: str | None = None,
    db: AsyncSession = Depends(get_async_primary_db),
):
    statement = select(Transaction.payment_method_id, func.count(Transaction.id)).group_by(Transaction.payment_method_id)
    if date_from:
        statement = statement.where(Transaction.created_at >= date_from)
    if date_to:
        statement = statement.where(Transaction.created_at <= date_to)
    result = await db.execute(statement)
    rows = result.all()
    return {"distribution": [{"payment_method_id": r[0], "count": r[1]} for r in rows]}


@analytics_router.get("/dashboard")
async def analytics_dashboard(db: AsyncSession = Depends(get_async_primary_db)):
    total_stmt = select(func.count(Transaction.id))
    revenue_stmt = select(func.coalesce(func.sum(Transaction.total_amount), 0))
    pending_stmt = select(func.count(Transaction.id)).where(Transaction.status.in_(["pending", "awaiting_payment"]))
    success_stmt = select(func.count(Transaction.id)).where(Transaction.status.in_(["paid", "settlement"]))

    total = (await db.execute(total_stmt)).scalar() or 0
    revenue = float((await db.execute(revenue_stmt)).scalar() or 0)
    pending = (await db.execute(pending_stmt)).scalar() or 0
    success = (await db.execute(success_stmt)).scalar() or 0
    success_rate = (success / total * 100) if total else 0

    return {
        "total_transactions": total,
        "revenue": revenue,
        "pending_payments": pending,
        "success_rate": round(success_rate, 2),
    }


@analytics_router.get("/user-behavior")
async def analytics_user_behavior(
    user_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: AsyncSession = Depends(get_async_primary_db),
):
    statement = select(Transaction)
    if user_id:
        statement = statement.where(Transaction.user_id == user_id)
    if date_from:
        statement = statement.where(Transaction.created_at >= date_from)
    if date_to:
        statement = statement.where(Transaction.created_at <= date_to)
    result = await db.execute(statement)
    rows = result.scalars().all()
    total = len(rows)
    avg_order = (sum(float(r.total_amount) for r in rows) / total) if total else 0

    method_counts: dict[str, int] = {}
    for row in rows:
        key = row.payment_method_id or "unknown"
        method_counts[key] = method_counts.get(key, 0) + 1
    favorite_method = max(method_counts, key=method_counts.get) if method_counts else None

    return {
        "user_id": user_id,
        "total_transactions": total,
        "average_order_value": round(avg_order, 2),
        "favorite_payment_method": favorite_method,
    }
