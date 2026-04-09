from pydantic import BaseModel, ConfigDict, Field


class CalculateFeeRequest(BaseModel):
    amount: float = Field(gt=0)


class CalculateFeeResponse(BaseModel):
    payment_method_id: str
    amount: float
    admin_fee: float
    total_with_fee: float


class PaymentMethodResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    method_code: str
    method_name: str
    method_type: str
    provider: str | None = None
    icon_url: str | None = None
    is_active: bool
    admin_fee: float
    admin_fee_type: str
