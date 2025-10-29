from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.depedencies import (
    get_primary_db,
    get_async_primary_db,
    get_replica_db,
    get_analytics_db
)
from app.domain.repository.product import ProductRepository
from app.domain.entity.product import Product

router = APIRouter(prefix="/products", tags=["Products"])


@router.get('/')
def get_all(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_primary_db)
):
    print(db)
    repo = ProductRepository(db)
    result = repo.get_all(skip=skip, limit=limit)
    
    return {
        'data': result
    }


@router.post("/")
def post_data(product: Product, db: Session = Depends(get_primary_db)):
    repo = ProductRepository(db)
    result = repo.create(product)
    return {'data': result}

@router.put("/{product_id}")
def update(
    product_id: str, 
    product: Product, 
    db: Session = Depends(get_primary_db)
):
    repo = ProductRepository(db)
    result = repo.update(product_id, product)
    
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {'data': result}


@router.delete("/{product_id}")
def delete(product_id: str, db: Session = Depends(get_primary_db)):
    repo = ProductRepository(db)
    success = repo.delete(product_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {'message': 'Product deleted successfully'}


