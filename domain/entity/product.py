from sqlmodel import SQLModel, Field, Column, JSON
from datetime import datetime
from typing import Optional
from enum import Enum
import uuid


class ProductCategory(SQLModel, table=True):
    __tablename__ = "product_categories"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    category_name: str = Field(max_length=255)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Product(SQLModel, table=True):
    __tablename__ = "products"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    application_id: str = Field(foreign_key="applications.id", max_length=36, index=True)
    category_id: Optional[str] = Field(default=None, foreign_key="product_categories.id", max_length=36, index=True)
    product_code: str = Field(max_length=100, index=True)
    product_name: str = Field(max_length=255)
    description: Optional[str] = None
    price: float = Field(ge=0)
    currency: str = Field(default="IDR", max_length=3)
    stock: int = Field(default=0, ge=0)
    is_active: bool = Field(default=True)
    metadata: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)