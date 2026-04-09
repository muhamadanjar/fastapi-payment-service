from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.depedencies import get_async_primary_db
from app.infrastructure.database.repositories.transactions import TransactionRepository

router = APIRouter()

@router.get("/")
async def get_all(db: AsyncSession = Depends(get_async_primary_db)):
    repo = TransactionRepository(db)
    return await repo.get_all(skip=0, limit=10)

@router.get("/{id}")
async def get_detail(id: str, db: AsyncSession = Depends(get_async_primary_db)):
    repo = TransactionRepository(db)
    return await repo.get_all(skip=0, limit=10)

@router.put("/{id}")
async def put_detail(id: str, db: AsyncSession = Depends(get_async_primary_db)):
    repo = TransactionRepository(db)
    return await repo.get_all(skip=0, limit=10)

@router.post("/{id}/eligible-users")
def post_eligible_users(id: str):
    return {}

@router.post("/{id}/conditions")
def post_conditions(id: str):
    return {}

@router.post("/{id}/validate")
def post_validate(id:str):
    return {}

@router.get("/my-vouchers")
def get_myvoucher():
    return []

@router.post("/{id}/claim")
def post_claim(id: str):
    return []

@router.get("/public")
def get_public():
    return []
