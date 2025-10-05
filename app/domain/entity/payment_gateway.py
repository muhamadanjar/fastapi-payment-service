from sqlmodel import SQLModel, Field, Column, JSON
from datetime import datetime
from typing import Optional
from enum import Enum
import uuid

class PaymentGatewayRequest(SQLModel, table=True):
    __tablename__ = "payment_gateway_requests"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    transaction_id: str = Field(foreign_key="transactions.id", max_length=36, index=True)
    gateway_id: str = Field(foreign_key="payment_gateways.id", max_length=36, index=True)
    request_type: RequestType
    request_method: str = Field(max_length=10)
    request_url: str
    request_headers: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    request_payload: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    response_status_code: Optional[int] = None
    response_headers: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    response_payload: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    response_time_ms: Optional[int] = None
    is_success: bool = Field(default=False)
    error_message: Optional[str] = None
    idempotency_key: Optional[str] = Field(default=None, max_length=255, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PaymentGatewayCallback(SQLModel, table=True):
    __tablename__ = "payment_gateway_callbacks"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    transaction_id: str = Field(foreign_key="transactions.id", max_length=36, index=True)
    gateway_id: str = Field(foreign_key="payment_gateways.id", max_length=36, index=True)
    callback_type: CallbackType
    raw_payload: dict = Field(sa_column=Column(JSON))
    signature: Optional[str] = Field(default=None, max_length=500)
    is_signature_valid: bool = Field(default=False)
    is_processed: bool = Field(default=False, index=True)
    processed_at: Optional[datetime] = None
    ip_address: Optional[str] = Field(default=None, max_length=50)
    user_agent: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

