from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.depedencies import (
    get_async_primary_db,
)
from app.infrastructure.database.repositories.product import ProductRepository
from app.domain.entity.product import Product
from app.domain.schema.product_schema import ProductCreate, ProductResponse, ProductUpdate

router = APIRouter(tags=["Products"])


@router.get("/")
async def get_all(
    page: int = 1,
    limit: int = 20,
    category_id: Optional[str] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_async_primary_db),
):
    repo = ProductRepository(db)
    page = max(page, 1)
    limit = max(min(limit, 100), 1)
    skip = (page - 1) * limit

    conditions: list[Any] = []
    if category_id:
        conditions.append(["category_id", "=", category_id])
    if is_active is not None:
        conditions.append(["is_active", "=", is_active])
    if search:
        conditions.append(
            {
                "or": [
                    ["product_name", "ilike", search],
                    ["product_code", "ilike", search],
                ]
            }
        )

    criteria = {"and": conditions} if conditions else None
    result = await repo.paginate(skip=skip, limit=limit, criteria=criteria, sortby=[["created_at", "desc"]])

    return {
        "data": [ProductResponse.model_validate(item) for item in result["data"]],
        "meta": result["metas"],
    }


@router.get("/{product_id}", response_model=ProductResponse)
async def get_detail(product_id: str, db: AsyncSession = Depends(get_async_primary_db)):
    repo = ProductRepository(db)
    product = await repo.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductResponse.model_validate(product)


@router.post("/", response_model=ProductResponse)
async def post_data(product: ProductCreate, db: AsyncSession = Depends(get_async_primary_db)):
    repo = ProductRepository(db)
    payload = Product(**product.model_dump())
    result = await repo.create(payload)
    return ProductResponse.model_validate(result)


@router.put("/{product_id}")
async def update(
    product_id: str,
    product: ProductUpdate,
    db: AsyncSession = Depends(get_async_primary_db),
):
    repo = ProductRepository(db)
    update_data = product.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    update_data["updated_at"] = datetime.utcnow()

    result = await repo.update(product_id, update_data)

    if not result:
        raise HTTPException(status_code=404, detail="Product not found")

    return {"data": ProductResponse.model_validate(result)}


@router.delete("/{product_id}")
async def delete(product_id: str, db: AsyncSession = Depends(get_async_primary_db)):
    repo = ProductRepository(db)

    existing = await repo.get_by_id(product_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")

    await repo.update(product_id, {"is_active": False, "updated_at": datetime.utcnow()})
    return {"message": "Product deactivated successfully"}


