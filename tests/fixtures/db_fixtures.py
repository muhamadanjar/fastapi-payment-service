import pytest_asyncio
from datetime import datetime, timedelta

from app.domain.entity.application import Application
from app.domain.entity.product import Product, ProductCategory
from app.domain.entity.payments import (
    PaymentMethod,
    PaymentGateway,
    PaymentGatewayCredential,
)
from app.domain.entity.transactions import Transaction
from app.domain.entity.enums import (
    AdminFeeType,
    GatewayType,
    MethodType,
    TransactionStatus,
)


@pytest_asyncio.fixture
async def application(db_session):
    """Test application with app_key and app_secret."""
    app = Application(
        app_name="Test App",
        app_key="app-001",
        app_secret="secret-001",
        callback_url="http://localhost:8000/callback",
        status="active",
    )
    db_session.add(app)
    await db_session.commit()
    await db_session.refresh(app)
    return app


@pytest_asyncio.fixture
async def payment_method(db_session):
    """BCA Virtual Account payment method with fixed 4000 admin fee."""
    method = PaymentMethod(
        method_code="BCA_VA",
        method_name="BCA Virtual Account",
        method_type=MethodType.VIRTUAL_ACCOUNT,
        provider="BCA",
        is_active=True,
        admin_fee=4000.0,
        admin_fee_type=AdminFeeType.FIXED,
    )
    db_session.add(method)
    await db_session.commit()
    await db_session.refresh(method)
    return method


@pytest_asyncio.fixture
async def gateway(db_session):
    """Midtrans payment gateway."""
    gw = PaymentGateway(
        gateway_code="midtrans",
        gateway_name="Midtrans",
        gateway_type=GatewayType.MIDTRANS,
        base_url="https://api.sandbox.midtrans.com",
        is_active=True,
        is_sandbox=True,
        priority=1,
    )
    db_session.add(gw)
    await db_session.commit()
    await db_session.refresh(gw)
    return gw


@pytest_asyncio.fixture
async def xendit_gateway(db_session):
    """Xendit payment gateway."""
    gw = PaymentGateway(
        gateway_code="xendit",
        gateway_name="Xendit",
        gateway_type=GatewayType.XENDIT,
        base_url="https://api.xendit.co",
        is_active=True,
        is_sandbox=True,
        priority=2,
    )
    db_session.add(gw)
    await db_session.commit()
    await db_session.refresh(gw)
    return gw


@pytest_asyncio.fixture
async def gateway_credential(db_session, gateway, application):
    """Midtrans gateway credential for the test application."""
    cred = PaymentGatewayCredential(
        application_id=application.id,
        gateway_id=gateway.id,
        api_key="test-server-key-abc123",
        api_secret="test-secret-xyz",
        webhook_secret="xendit-callback-token-xyz",
        is_active=True,
    )
    db_session.add(cred)
    await db_session.commit()
    await db_session.refresh(cred)
    return cred


@pytest_asyncio.fixture
async def xendit_credential(db_session, xendit_gateway, application):
    """Xendit gateway credential for the test application."""
    cred = PaymentGatewayCredential(
        application_id=application.id,
        gateway_id=xendit_gateway.id,
        api_key="test-xendit-key",
        webhook_secret="xendit-callback-token-xyz",
        is_active=True,
    )
    db_session.add(cred)
    await db_session.commit()
    await db_session.refresh(cred)
    return cred


@pytest_asyncio.fixture
async def product(db_session, application):
    """Test product."""
    p = Product(
        application_id=application.id,
        product_code="PROD-001",
        product_name="Test Product",
        description="A test product",
        price=100_000.0,
        currency="IDR",
        stock=10,
        is_active=True,
    )
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)
    return p


@pytest_asyncio.fixture
async def pending_transaction(db_session, application):
    """Transaction in PENDING status."""
    tx = Transaction(
        application_id=application.id,
        user_id="user-001",
        transaction_code="TRX-TESTPENDING001",
        invoice_number="INV-TESTPENDING001",
        status=TransactionStatus.PENDING,
        subtotal=100_000.0,
        discount_amount=0.0,
        admin_fee=0.0,
        total_amount=100_000.0,
        currency="IDR",
    )
    db_session.add(tx)
    await db_session.commit()
    await db_session.refresh(tx)
    return tx


@pytest_asyncio.fixture
async def awaiting_transaction(db_session, application, gateway):
    """Transaction in AWAITING_PAYMENT status, ready for webhook."""
    tx = Transaction(
        application_id=application.id,
        user_id="user-002",
        transaction_code="TRX-AWAITING001",
        invoice_number="INV-AWAITING001",
        status=TransactionStatus.AWAITING_PAYMENT,
        gateway_id=gateway.id,
        payment_reference="PAY-TESTKEY123456789012",
        subtotal=100_000.0,
        discount_amount=0.0,
        admin_fee=4000.0,
        total_amount=104_000.0,
        currency="IDR",
        expired_at=datetime.utcnow() + timedelta(hours=24),
    )
    db_session.add(tx)
    await db_session.commit()
    await db_session.refresh(tx)
    return tx


@pytest_asyncio.fixture
async def paid_transaction(db_session, application):
    """Transaction in PAID status."""
    tx = Transaction(
        application_id=application.id,
        user_id="user-003",
        transaction_code="TRX-PAID001",
        invoice_number="INV-PAID001",
        status=TransactionStatus.PAID,
        subtotal=100_000.0,
        discount_amount=0.0,
        admin_fee=4000.0,
        total_amount=104_000.0,
        currency="IDR",
        paid_at=datetime.utcnow(),
    )
    db_session.add(tx)
    await db_session.commit()
    await db_session.refresh(tx)
    return tx
