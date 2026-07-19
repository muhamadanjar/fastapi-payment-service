from fastapi import APIRouter, Depends
from app.core.auth import get_current_user, require_roles
from .health import router as health_router
from .admin_config import router as admin_config_router
from .products import router as product_router
from .transactions import router as transaction_router
from .payment_method import router as payment_method_router
from .payment_gateway import gateway_request_router, gateway_router
from .reports_analytics import analytics_router, reports_router
from .utilities import router as utilities_router
from .voucher import router as voucher_router
from .webhook import callback_router as webhook_callback_router
from .webhook import management_router as webhook_management_router

# All /api/* endpoints require a valid authenticated principal.
api_router = APIRouter(prefix="/api", dependencies=[Depends(get_current_user)])
public_router = APIRouter()

# Include all routers with prefixes
api_router.include_router(health_router, prefix="/health", tags=["Health"])
api_router.include_router(product_router, prefix="/products", tags=["Products"])
api_router.include_router(transaction_router, prefix="/transactions", tags=["Transaction"])
api_router.include_router(payment_method_router, prefix="/payment-methods", tags=["Payment Method"])
api_router.include_router(voucher_router, prefix="/vouchers", tags=["Voucher"])
api_router.include_router(webhook_management_router, prefix="/webhooks", tags=["Webhook"])
api_router.include_router(gateway_router, prefix="/admin", tags=["Admin Gateway"])
api_router.include_router(gateway_request_router, prefix="/admin", tags=["Admin Gateway"])
api_router.include_router(admin_config_router, prefix="/admin", tags=["Admin Configuration"])
api_router.include_router(reports_router, prefix="/reports", tags=["Reports"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(utilities_router, tags=["Utilities"])

# Gateway callbacks are intentionally outside /api.
public_router.include_router(webhook_callback_router, prefix="/webhook", tags=["Webhook"])