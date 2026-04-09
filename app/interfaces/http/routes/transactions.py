from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.depedencies import get_async_primary_db
from app.infrastructure.database.repositories.transactions import TransactionRepository

router = APIRouter()


@router.get("/")
async def get_all(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_async_primary_db),
):
    repo = TransactionRepository(db)
    return await repo.get_all(skip=skip, limit=limit)


@router.post("/")
async def post_transaction(db: AsyncSession = Depends(get_async_primary_db)):
    repo = TransactionRepository(db)
    return {}

@router.get("/{transaction_id}")
async def get_transaction(transaction_id: str, db: AsyncSession = Depends(get_async_primary_db)):
    repo = TransactionRepository(db)
    transaction = await repo.get_by_id(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

@router.post("/{transaction_id}/pay", description="Pilih metode pembayaran & generate payment instruction")
async def post_transaction_pay(transaction_id: str, db: AsyncSession = Depends(get_async_primary_db)):
    repo = TransactionRepository(db)
    return {}

@router.get("/{transaction_id}/status")
async def get_transaction_status(transaction_id: str, db: AsyncSession = Depends(get_async_primary_db)):
    repo = TransactionRepository(db)
    return {}

@router.post("/{transaction_id}/cancel")
async def post_transaction_cancel(transaction_id: str, db: AsyncSession = Depends(get_async_primary_db)):
    repo = TransactionRepository(db)
    return {}

@router.post("/{transaction_id}/refund", description="Request refund transaksi")
async def post_transaction_refund(transaction_id: str, db: AsyncSession = Depends(get_async_primary_db)):
    repo = TransactionRepository(db)
    return {}

@router.get("/{transaction_id}/invoice")
async def get_transaction_invoice(transaction_id: str, db: AsyncSession = Depends(get_async_primary_db)):
    repo = TransactionRepository(db)
    return {}


    