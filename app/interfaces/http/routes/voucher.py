from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.infrastructure.database.depedencies import get_db, get_primary_db
from app.domain.repository.transactions import TransactionRepository

router = APIRouter()

@router.get('/')
def get_all(db: Session = Depends(get_primary_db)):
    repo = TransactionRepository(db)
    return repo.get_all(skip=0, limit=10)

@router.get('/{id}')
def get_detail(id: str, db: Session = Depends(get_primary_db)):
    repo = TransactionRepository(db)
    return repo.get_all(skip=0, limit=10)

@router.put('/{id}')
def put_detail(id: str, db: Session = Depends(get_primary_db)):
    repo = TransactionRepository(db)
    return repo.get_all(skip=0, limit=10)

@router.post('{id}/eligible-users')
def post_eligible_users(id: str):
    return {}

@router.post('{id}/conditions')
def post_eligible_users(id: str):
    return {}

@router.post('{id}/validate')
def post_validate(id:str):
    return {}

@router.get('my-vouchers')
def get_myvoucher():
    return []

@router.post('{id}/claim')
def post_claim(id: str):
    return []

@router.get('public')
def get_public():
    return []
