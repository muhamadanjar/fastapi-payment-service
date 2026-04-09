from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PaymentGatewayResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    gateway_code: str
    gateway_name: str
    gateway_type: str
    base_url: str
    is_active: bool
    is_sandbox: bool
    priority: int
    supported_methods: dict | None = None
    created_at: datetime
    updated_at: datetime


class PaymentGatewayToggleRequest(BaseModel):
    is_active: bool


class PaymentGatewayCredentialCreateRequest(BaseModel):
    application_id: str
    merchant_id: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    client_key: Optional[str] = None
    webhook_secret: Optional[str] = None
    additional_config: dict | None = None
    is_active: bool = True


class PaymentGatewayCredentialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    application_id: str
    gateway_id: str
    merchant_id: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    client_key: Optional[str] = None
    webhook_secret: Optional[str] = None
    additional_config: dict | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
