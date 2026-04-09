from datetime import datetime

from pydantic import BaseModel


class ApplicationUpdateRequest(BaseModel):
    callback_url: str | None = None
    status: str | None = None
    name: str | None = None
    metadata: dict | None = None


class ForceTransactionStatusRequest(BaseModel):
    new_status: str
    reason: str | None = None


class AssignVoucherUsersRequest(BaseModel):
    user_ids: list[str]
    application_id: str
    expires_at: datetime | None = None
