import hashlib
from httpx import AsyncClient

from app.domain.entity.transactions import Transaction
from app.domain.entity.enums import TransactionStatus
from tests.fixtures.db_fixtures import (  # noqa: F401
    gateway_credential,
    xendit_credential,
    awaiting_transaction,
)


class TestMidtransWebhook:
    async def test_midtrans_webhook_valid_signature(
        self, client: AsyncClient, awaiting_transaction, gateway_credential, db_session
    ):
        """Midtrans webhook with valid signature → transaction settled."""
        order_id = awaiting_transaction.invoice_number
        status_code = "200"
        gross_amount = "104000.00"
        server_key = gateway_credential.api_key

        # Compute expected signature (Midtrans SHA512)
        expected_signature = hashlib.sha512(
            f"{order_id}{status_code}{gross_amount}{server_key}".encode()
        ).hexdigest()

        response = await client.post(
            f"/webhook/payment/midtrans",
            json={
                "order_id": order_id,
                "status_code": status_code,
                "gross_amount": gross_amount,
                "transaction_status": "settlement",
            },
            headers={"signature_key": expected_signature}
        )
        assert response.status_code == 200
        assert response.json()["message"] == "accepted"

        # Verify transaction status updated in DB
        refreshed = await db_session.get(Transaction, awaiting_transaction.id)
        assert refreshed.status == TransactionStatus.SETTLEMENT
        assert refreshed.paid_at is not None

    async def test_midtrans_webhook_invalid_signature(
        self, client: AsyncClient, awaiting_transaction, gateway_credential, db_session
    ):
        """Midtrans webhook with invalid signature → 401, no status change."""
        order_id = awaiting_transaction.invoice_number

        response = await client.post(
            f"/webhook/payment/midtrans",
            json={
                "order_id": order_id,
                "status_code": "200",
                "gross_amount": "104000.00",
                "transaction_status": "settlement",
            },
            headers={"signature_key": "wrong-signature-xyz"}
        )
        assert response.status_code == 401
        assert "Invalid webhook signature" in response.json()["detail"]

        # Verify transaction status unchanged
        refreshed = await db_session.get(Transaction, awaiting_transaction.id)
        assert refreshed.status == TransactionStatus.AWAITING_PAYMENT
        assert refreshed.paid_at is None


class TestXenditWebhook:
    async def test_xendit_webhook_valid_token(
        self, client: AsyncClient, db_session
    ):
        """Xendit webhook with valid token → transaction paid."""
        # Create an awaiting transaction for Xendit
        from app.domain.entity.transactions import Transaction
        from app.domain.entity.enums import TransactionStatus
        from datetime import datetime, timedelta

        app_id = (await db_session.execute(
            __import__("sqlmodel").select(
                __import__("app.domain.entity.application", fromlist=["Application"]).Application
            )
        )).scalars().first()

        tx = Transaction(
            application_id=app_id.id,
            user_id="user-xendit",
            transaction_code="TRX-XENDIT001",
            invoice_number="INV-XENDIT001",
            status=TransactionStatus.AWAITING_PAYMENT,
            subtotal=50_000.0,
            discount_amount=0.0,
            admin_fee=0.0,
            total_amount=50_000.0,
            currency="IDR",
            expired_at=datetime.utcnow() + timedelta(hours=24),
        )
        db_session.add(tx)
        await db_session.commit()
        await db_session.refresh(tx)

        response = await client.post(
            f"/webhook/payment/xendit",
            json={
                "external_id": tx.invoice_number,
                "status": "paid",
            },
            headers={"x-callback-token": "xendit-callback-token-xyz"}
        )
        assert response.status_code == 200
        assert response.json()["message"] == "accepted"

        # Verify transaction status updated
        refreshed = await db_session.get(Transaction, tx.id)
        assert refreshed.status == TransactionStatus.PAID
        assert refreshed.paid_at is not None

    async def test_xendit_webhook_invalid_token(
        self, client: AsyncClient, awaiting_transaction
    ):
        """Xendit webhook with invalid token → 401."""
        response = await client.post(
            f"/webhook/payment/xendit",
            json={
                "external_id": awaiting_transaction.invoice_number,
                "status": "paid",
            },
            headers={"x-callback-token": "wrong-token"}
        )
        assert response.status_code == 401
        assert "Invalid webhook signature" in response.json()["detail"]


class TestWebhookErrors:
    async def test_webhook_unknown_gateway(self, client: AsyncClient):
        """Webhook for non-existent gateway → 404."""
        response = await client.post(
            "/webhook/payment/nonexistent-gateway",
            json={
                "order_id": "order-123",
                "status_code": "200",
            }
        )
        assert response.status_code == 404
        assert "Gateway not found" in response.json()["detail"]
