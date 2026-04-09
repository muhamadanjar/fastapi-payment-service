from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TransactionCreateRequest(BaseModel):
    application_id: str
    user_id: str
    subtotal: float = Field(ge=0)
    discount_amount: float = Field(default=0, ge=0)
    voucher_id: Optional[str] = None
    notes: Optional[str] = None
    currency: str = "IDR"


class TransactionPayRequest(BaseModel):
    payment_method_id: str
    gateway_id: Optional[str] = None


class TransactionCancelRequest(BaseModel):
    reason: Optional[str] = None


class TransactionRefundRequest(BaseModel):
    refund_amount: float = Field(ge=0)
    reason: Optional[str] = None
    notes: Optional[str] = None


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    application_id: str
    user_id: str
    transaction_code: str
    invoice_number: str
    payment_method_id: Optional[str] = None
    gateway_id: Optional[str] = None
    voucher_id: Optional[str] = None
    status: str
    subtotal: float
    discount_amount: float
    admin_fee: float
    total_amount: float
    currency: str
    payment_url: Optional[str] = None
    payment_reference: Optional[str] = None
    paid_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
