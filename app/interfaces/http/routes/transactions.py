from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.infrastructure.database.depedencies import get_db, get_primary_db
from app.domain.repository.transactions import TransactionRepository

router = APIRouter()


@router.get('/')
def get_all(db: Session = Depends(get_primary_db)):
    repo = TransactionRepository(db)
    return repo.get_all(skip=0, limit=10)


@router.post('/')
def post_transaction(db: Session = Depends(get_primary_db)):
    repo = TransactionRepository(db)
    return {}

@router.get('/{transaction_id}')
def get_transaction(transaction_id:str, db: Session = Depends(get_primary_db)):
    repo = TransactionRepository(db)
    return {}

@router.post('/{transaction_id}/pay', description=" Pilih metode pembayaran & generate payment instruction")
def post_transaction_pay(transaction_id:str, db: Session = Depends(get_primary_db)):
    repo = TransactionRepository(db)
    return {}

@router.get('/{transaction_id}/status')
def get_transaction_status(transaction_id:str, db: Session = Depends(get_primary_db)):
    repo = TransactionRepository(db)
    return {}

@router.post('/{transaction_id}/cancel')
def post_transaction_cancel(transaction_id:str, db: Session = Depends(get_primary_db)):
    repo = TransactionRepository(db)
    return {}

@router.post('/{transaction_id}/refund', description=' Request refund transaksi')
def post_transaction_refund(transaction_id:str, db: Session = Depends(get_primary_db)):
    repo = TransactionRepository(db)
    return {}

@router.post('/{transaction_id}/refund')
def get_transaction_invoice(transaction_id:str, db: Session = Depends(get_primary_db)):
    repo = TransactionRepository(db)
    return {}


    