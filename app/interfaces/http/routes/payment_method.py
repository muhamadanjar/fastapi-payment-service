
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.infrastructure.database.depedencies import get_db, get_primary_db

router = APIRouter()


@router.get('/', name="List metode pembayaran available")
def get_all(db: Session = Depends(get_primary_db)):
    return {}

@router.get('/{id}', name="Detail metode pembayaran")
def get_detail(id:str, db: Session = Depends(get_primary_db)):
    return {}

@router.post('/{id}/calculate-fee', name="Hitung admin fee untuk amount tertentu")
def get_all(id:str, db: Session = Depends(get_primary_db)):
    return {}