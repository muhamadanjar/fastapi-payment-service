from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class VoucherValidateRequest(BaseModel):
    voucher_code: str
    user_id: str | None = None
    transaction_amount: float


class VoucherValidateResponse(BaseModel):
    is_valid: bool
    discount_amount: float = 0
    voucher_details: dict[str, Any] | None = None
    error_message: str | None = None


class VoucherCreateRequest(BaseModel):
    application_id: str
    voucher_code: str
    voucher_name: str
    description: str | None = None
    voucher_type: str
    discount_type: str
    discount_value: float
    max_discount: float | None = None
    min_transaction: float = 0
    usage_limit: int | None = None
    usage_limit_per_user: int | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    is_active: bool = True
    is_auto_apply: bool = False
    applicable_products: dict | None = None


class VoucherUpdateRequest(BaseModel):
    voucher_name: str | None = None
    description: str | None = None
    discount_value: float | None = None
    max_discount: float | None = None
    min_transaction: float | None = None
    usage_limit: int | None = None
    usage_limit_per_user: int | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    is_active: bool | None = None
    is_auto_apply: bool | None = None
    applicable_products: dict | None = None


class VoucherConditionCreateRequest(BaseModel):
    condition_type: str
    operator: str
    condition_value: dict[str, Any]
    is_required: bool = True


class VoucherClaimRequest(BaseModel):
    user_id: str


class VoucherResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    application_id: str
    voucher_code: str
    voucher_name: str
    description: str | None = None
    voucher_type: str
    discount_type: str
    discount_value: float
    max_discount: float | None = None
    min_transaction: float
    usage_limit: int | None = None
    usage_count: int
    usage_limit_per_user: int | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    is_active: bool
    is_auto_apply: bool
    created_at: datetime
    updated_at: datetime
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class VoucherResponse(BaseModel):
    """Schema for quality rule response."""
    id: str
    application_id: str
    voucher_code: str
    created_at: datetime


class VoucherCreate(BaseModel):
    voucher_code: str
    voucher_name: str
    discount_value: float


class VoucherRead(VoucherCreate):
    created_at: datetime