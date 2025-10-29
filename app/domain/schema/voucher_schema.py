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