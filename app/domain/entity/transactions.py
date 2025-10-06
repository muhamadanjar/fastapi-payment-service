from sqlmodel import SQLModel, Field, Column, JSON
from datetime import datetime
from typing import Optional
from enum import Enum
import uuid

from app.domain.entity.enums import ChangedBy, TransactionStatus


class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    application_id: str = Field(max_length=36, index=True)
    user_id: str = Field(max_length=36, index=True)
    transaction_code: str = Field(unique=True, max_length=100, index=True)
    invoice_number: str = Field(unique=True, max_length=100, index=True)
    payment_method_id: Optional[str] = Field(default=None, foreign_key="payment_methods.id", max_length=36, index=True)
    gateway_id: Optional[str] = Field(default=None, foreign_key="payment_gateways.id", max_length=36, index=True)
    voucher_id: Optional[str] = Field(default=None, foreign_key="vouchers.id", max_length=36, index=True)
    status: TransactionStatus = Field(default=TransactionStatus.PENDING, index=True)
    subtotal: float = Field(ge=0)
    discount_amount: float = Field(default=0, ge=0)
    admin_fee: float = Field(default=0, ge=0)
    total_amount: float = Field(ge=0)
    currency: str = Field(default="IDR", max_length=3)
    payment_url: Optional[str] = Field(default=None, max_length=500)
    payment_token: Optional[str] = Field(default=None, max_length=500)
    payment_reference: Optional[str] = Field(default=None, max_length=255, index=True)
    va_number: Optional[str] = Field(default=None, max_length=100)
    qr_code_url: Optional[str] = Field(default=None, max_length=500)
    paid_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None
    notes: Optional[str] = None
    extra_data: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TransactionItem(SQLModel, table=True):
    __tablename__ = "transaction_items"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    transaction_id: str = Field(foreign_key="transactions.id", max_length=36, index=True)
    product_id: str = Field(foreign_key="products.id", max_length=36, index=True)
    product_name: str = Field(max_length=255)
    product_code: str = Field(max_length=100)
    quantity: int = Field(gt=0)
    unit_price: float = Field(ge=0)
    subtotal: float = Field(ge=0)
    item_metadata: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TransactionLog(SQLModel, table=True):
    __tablename__ = "transaction_logs"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    transaction_id: str = Field(foreign_key="transactions.id", max_length=36, index=True)
    previous_status: Optional[TransactionStatus] = None
    new_status: TransactionStatus
    changed_by: ChangedBy
    gateway_callback_id: Optional[str] = Field(default=None, foreign_key="payment_gateway_callbacks.id", max_length=36)
    notes: Optional[str] = None
    log_metadata: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
