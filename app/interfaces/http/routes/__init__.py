from fastapi import APIRouter
from .health import router as health_router
from .products import router as product_router
from .transactions import router as transaction_router
from .payment_method import router as payment_method_router
from .voucher import router as voucher_router
api_router = APIRouter()

# Include all routers with prefixes
api_router.include_router(health_router, prefix="/health", tags=["Health"])
api_router.include_router(product_router, prefix="/products", tags=["Products"])
api_router.include_router(transaction_router, prefix="/transactions", tags=["Transaction"])
api_router.include_router(payment_method_router, prefix="/payment-methods", tags=["Payment Method"])
api_router.include_router(voucher_router, prefix="/vouchers", tags=["Voucher"])