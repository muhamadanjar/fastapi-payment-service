from sqlmodel import SQLModel, Field, Column, JSON
from datetime import datetime
from typing import Optional
from enum import Enum
import uuid

from app.domain.entity.enums import ConditionType, DiscountType, OperatorType, VoucherType

class Voucher(SQLModel, table=True):
    __tablename__ = "vouchers"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    application_id: str = Field(max_length=36, index=True)
    voucher_code: str = Field(unique=True, max_length=100, index=True)
    voucher_name: str = Field(max_length=255)
    description: Optional[str] = None
    voucher_type: VoucherType
    discount_type: DiscountType
    discount_value: float = Field(ge=0)
    max_discount: Optional[float] = Field(default=None, ge=0)
    min_transaction: float = Field(default=0, ge=0)
    usage_limit: Optional[int] = Field(default=None, ge=0)
    usage_count: int = Field(default=0, ge=0)
    usage_limit_per_user: Optional[int] = Field(default=None, ge=0)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: bool = Field(default=True)
    is_auto_apply: bool = Field(default=False)
    applicable_products: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class VoucherCondition(SQLModel, table=True):
    __tablename__ = "voucher_conditions"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    voucher_id: str = Field(foreign_key="vouchers.id", max_length=36, index=True)
    condition_type: ConditionType
    operator: OperatorType
    condition_value: dict = Field(sa_column=Column(JSON))
    is_required: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class VoucherEligibleUser(SQLModel, table=True):
    __tablename__ = "voucher_eligible_users"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    voucher_id: str = Field(foreign_key="vouchers.id", max_length=36, index=True)
    user_id: str = Field(max_length=36, index=True)
    application_id: str = Field(max_length=36, index=True)
    eligible_at: datetime = Field(default_factory=datetime.utcnow)
    notified_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_claimed: bool = Field(default=False)
    claimed_at: Optional[datetime] = None


class VoucherUsage(SQLModel, table=True):
    __tablename__ = "voucher_usage"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    voucher_id: str = Field(foreign_key="vouchers.id", max_length=36, index=True)
    user_id: str = Field(max_length=36, index=True)
    application_id: str = Field(max_length=36, index=True)
    transaction_id: str = Field(foreign_key="transactions.id", max_length=36, index=True)
    used_at: datetime = Field(default_factory=datetime.utcnow)

