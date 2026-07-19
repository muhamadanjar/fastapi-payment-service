from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_roles
from app.domain.entity.payments import PaymentGatewayCredential
from app.domain.schema.payment_gateway_schema import (
    PaymentGatewayCredentialCreateRequest,
    PaymentGatewayCredentialResponse,
    PaymentGatewayResponse,
    PaymentGatewayToggleRequest,
)
from app.infrastructure.database.depedencies import get_async_primary_db
from app.infrastructure.database.repositories.payment_gateway import (
    PaymentGatewayCredentialRepository,
    PaymentGatewayRepository,
    PaymentGatewayRequestRepository,
)

# Admin-only: gateway config + credential management.
gateway_router = APIRouter(dependencies=[Depends(require_roles())])
gateway_request_router = APIRouter(dependencies=[Depends(require_roles())])


@gateway_router.get("/gateways")
async def get_gateways(db: AsyncSession = Depends(get_async_primary_db)):
    repo = PaymentGatewayRepository(db)
    data = await repo.get_all(skip=0, limit=200)
    return {"data": [PaymentGatewayResponse.model_validate(item) for item in data]}


@gateway_router.post("/gateways/{id}/credentials")
async def create_gateway_credentials(
    id: str,
    payload: PaymentGatewayCredentialCreateRequest,
    db: AsyncSession = Depends(get_async_primary_db),
):
    gateway_repo = PaymentGatewayRepository(db)
    credential_repo = PaymentGatewayCredentialRepository(db)

    gateway = await gateway_repo.get_by_id(id)
    if not gateway:
        raise HTTPException(status_code=404, detail="Gateway not found")

    credential = PaymentGatewayCredential(gateway_id=id, **payload.model_dump())
    saved = await credential_repo.create(credential)
    return PaymentGatewayCredentialResponse.model_validate(saved)


@gateway_router.put("/gateways/{id}/toggle")
async def toggle_gateway(
    id: str,
    payload: PaymentGatewayToggleRequest,
    db: AsyncSession = Depends(get_async_primary_db),
):
    repo = PaymentGatewayRepository(db)
    updated = await repo.update(id, {"is_active": payload.is_active, "updated_at": datetime.utcnow()})
    if not updated:
        raise HTTPException(status_code=404, detail="Gateway not found")
    return PaymentGatewayResponse.model_validate(updated)


@gateway_request_router.get("/gateway-requests")
async def get_gateway_requests(
    gateway_id: str | None = None,
    request_type: str | None = None,
    is_success: bool | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_async_primary_db),
):
    repo = PaymentGatewayRequestRepository(db)
    page = max(page, 1)
    limit = max(min(limit, 100), 1)
    skip = (page - 1) * limit

    conditions: list = []
    if gateway_id:
        conditions.append(["gateway_id", "=", gateway_id])
    if request_type:
        conditions.append(["request_type", "=", request_type])
    if is_success is not None:
        conditions.append(["is_success", "=", is_success])
    if date_from:
        conditions.append(["created_at", ">=", date_from])
    if date_to:
        conditions.append(["created_at", "<=", date_to])

    criteria = {"and": conditions} if conditions else None
    result = await repo.paginate(skip=skip, limit=limit, criteria=criteria, sortby=[["created_at", "desc"]])
    return {"data": result["data"], "meta": result["metas"]}
