from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entity.enums import AdminFeeType
from app.infrastructure.database.depedencies import get_async_primary_db
from app.infrastructure.database.repositories.payment_method import PaymentMethodRepository

router = APIRouter()


@router.get("/banks")
async def get_banks():
    return {
        "data": [
            {"code": "BCA", "name": "Bank Central Asia"},
            {"code": "MANDIRI", "name": "Bank Mandiri"},
            {"code": "BNI", "name": "Bank Negara Indonesia"},
            {"code": "BRI", "name": "Bank Rakyat Indonesia"},
        ]
    }


@router.post("/notifications/send")
async def send_notification(payload: dict):
    # TODO: integrate with notification provider/queue.
    return {"message": "Notification queued", "payload": payload}


@router.get("/fees/calculate")
async def calculate_fees(
    amount: float,
    payment_method_ids: str,
    db: AsyncSession = Depends(get_async_primary_db),
):
    repo = PaymentMethodRepository(db)
    ids = [item.strip() for item in payment_method_ids.split(",") if item.strip()]
    result = []
    for method_id in ids:
        method = await repo.get_by_id(method_id)
        if not method:
            result.append({"payment_method_id": method_id, "error": "not_found"})
            continue
        if method.admin_fee_type == AdminFeeType.PERCENTAGE:
            admin_fee = amount * (method.admin_fee / 100)
        else:
            admin_fee = method.admin_fee
        result.append(
            {
                "payment_method_id": method.id,
                "method_name": method.method_name,
                "admin_fee": admin_fee,
                "total_with_fee": amount + admin_fee,
            }
        )
    return {"amount": amount, "breakdown": result}
