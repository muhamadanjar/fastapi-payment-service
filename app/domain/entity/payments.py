from sqlmodel import SQLModel, Field, Column, JSON
from datetime import datetime
from typing import Optional
from enum import Enum
import uuid

class PaymentMethod(SQLModel, table=True):
    __tablename__ = "payment_methods"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    method_code: str = Field(unique=True, max_length=100, index=True)
    method_name: str = Field(max_length=255)
    method_type: MethodType
    provider: Optional[str] = Field(default=None, max_length=100)
    icon_url: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    admin_fee: float = Field(default=0, ge=0)
    admin_fee_type: AdminFeeType = Field(default=AdminFeeType.FIXED)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PaymentGateway(SQLModel, table=True):
    __tablename__ = "payment_gateways"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    gateway_code: str = Field(unique=True, max_length=100, index=True)
    gateway_name: str = Field(max_length=255)
    gateway_type: GatewayType
    base_url: str = Field(max_length=500)
    is_active: bool = Field(default=True)
    is_sandbox: bool = Field(default=False)
    priority: int = Field(default=0)
    supported_methods: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PaymentGatewayCredential(SQLModel, table=True):
    __tablename__ = "payment_gateway_credentials"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    application_id: str = Field(foreign_key="applications.id", max_length=36, index=True)
    gateway_id: str = Field(foreign_key="payment_gateways.id", max_length=36, index=True)
    merchant_id: Optional[str] = Field(default=None, max_length=255)
    api_key: Optional[str] = Field(default=None, max_length=500)
    api_secret: Optional[str] = Field(default=None, max_length=500)
    client_key: Optional[str] = Field(default=None, max_length=500)
    webhook_secret: Optional[str] = Field(default=None, max_length=500)
    additional_config: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PaymentMethodGateway(SQLModel, table=True):
    __tablename__ = "payment_method_gateways"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    payment_method_id: str = Field(foreign_key="payment_methods.id", max_length=36, index=True)
    gateway_id: str = Field(foreign_key="payment_gateways.id", max_length=36, index=True)
    gateway_method_code: str = Field(max_length=100)
    is_active: bool = Field(default=True)
    processing_time_minutes: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)