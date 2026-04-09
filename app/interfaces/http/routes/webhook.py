from fastapi import APIRouter

# Public callback endpoints from payment gateways.
callback_router = APIRouter()

# Internal webhook management endpoints.
management_router = APIRouter()


@callback_router.post("/payment/{gateway_code}")
async def payment(gateway_code: str):
    return {"message": "accepted", "gateway_code": gateway_code}


@callback_router.post("/test")
async def test():
    return {"message": "webhook test accepted"}


@management_router.get("/logs")
async def logs():
    return {"data": []}


@management_router.post("/{id}/retry")
async def webhook_retry(id: str):
    return {"message": "retry requested", "webhook_id": id}