
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.domain.entity.transactions import Transaction, TransactionItem, TransactionLog
from app.infrastructure.database.depedencies import get_db
from app.domain.repository.product import ProductRepository

router = APIRouter()


@router.get('/')
def get_all(db: Session = Depends(get_db)):
    repo = ProductRepository(db)