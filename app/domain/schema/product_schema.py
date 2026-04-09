from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ProductCreate(BaseModel):
    application_id: str
    category_id: Optional[str] = None
    product_code: str
    product_name: str
    description: Optional[str] = None
    price: float
    currency: str = "IDR"
    stock: int = 0
    is_active: bool = True
    product_metadata: Optional[dict] = None


class ProductUpdate(BaseModel):
    category_id: Optional[str] = None
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    stock: Optional[int] = None
    is_active: Optional[bool] = None
    product_metadata: Optional[dict] = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    application_id: str
    category_id: Optional[str] = None
    product_code: str
    product_name: str
    description: Optional[str] = None
    price: float
    currency: str
    stock: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
