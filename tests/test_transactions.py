import pytest
from httpx import AsyncClient

from app.domain.entity.transactions import Transaction
from app.domain.entity.enums import TransactionStatus
from tests.fixtures.db_fixtures import (  # noqa: F401
    application,
    payment_method,
    gateway,
    gateway_credential,
    product,
    pending_transaction,
    paid_transaction,
)


class TestTransactionCreate:
    async def test_create_transaction(self, client: AsyncClient, application):
        """Create a new transaction with pending status."""
        response = await client.post(
            "/api/transactions/",
            json={
                "application_id": application.id,
                "user_id": "user-new",
                "subtotal": 100_000,
                "discount_amount": 0,
                "currency": "IDR",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["total_amount"] == 100_000
        assert data["id"] is not None
        assert data["transaction_code"].startswith("TRX-")
        assert data["invoice_number"].startswith("INV-")


class TestTransactionGet:
    async def test_get_transaction_by_id(self, client: AsyncClient, pending_transaction):
        """Retrieve a transaction by ID."""
        response = await client.get(
            f"/api/transactions/{pending_transaction.id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == pending_transaction.id
        assert data["status"] == "pending"
        assert data["transaction_code"] == pending_transaction.transaction_code

    async def test_get_transaction_not_found(self, client: AsyncClient):
        """Get non-existent transaction returns 404."""
        response = await client.get("/api/transactions/nonexistent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestTransactionPay:
    async def test_pay_transaction_transitions_to_awaiting(
        self, client: AsyncClient, pending_transaction, payment_method, db_session
    ):
        """Pay a pending transaction → awaiting_payment status."""
        response = await client.post(
            f"/api/transactions/{pending_transaction.id}/pay",
            json={
                "payment_method_id": payment_method.id,
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "awaiting_payment"
        assert data["payment_details"]["admin_fee"] == 4000.0
        assert data["payment_details"]["total_amount"] == 104_000.0
        assert data["payment_details"]["payment_reference"] is not None
        assert data["payment_details"]["payment_url"] is not None

        # Verify state persisted in DB
        refreshed = await db_session.get(Transaction, pending_transaction.id)
        assert refreshed.status == TransactionStatus.AWAITING_PAYMENT
        assert refreshed.admin_fee == 4000.0

    async def test_pay_already_paid_transaction_fails(
        self, client: AsyncClient, paid_transaction, payment_method
    ):
        """Cannot pay an already-paid transaction."""
        response = await client.post(
            f"/api/transactions/{paid_transaction.id}/pay",
            json={
                "payment_method_id": payment_method.id,
            }
        )
        assert response.status_code == 400
        assert "already paid" in response.json()["detail"].lower()


class TestTransactionCancel:
    async def test_cancel_pending_transaction(
        self, client: AsyncClient, pending_transaction, db_session
    ):
        """Cancel a pending transaction."""
        response = await client.post(
            f"/api/transactions/{pending_transaction.id}/cancel",
            json={"reason": "User changed mind"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"

        # Verify state persisted
        refreshed = await db_session.get(Transaction, pending_transaction.id)
        assert refreshed.status == TransactionStatus.CANCELLED

    async def test_cancel_paid_transaction_fails(
        self, client: AsyncClient, paid_transaction
    ):
        """Cannot cancel a paid transaction."""
        response = await client.post(
            f"/api/transactions/{paid_transaction.id}/cancel",
            json={"reason": "trying to cancel"}
        )
        assert response.status_code == 400
        assert "cannot be cancelled" in response.json()["detail"].lower()


class TestTransactionRefund:
    async def test_refund_paid_transaction(
        self, client: AsyncClient, paid_transaction, db_session
    ):
        """Refund a paid transaction."""
        response = await client.post(
            f"/api/transactions/{paid_transaction.id}/refund",
            json={
                "refund_amount": 100_000,
                "reason": "Requested by user"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "refunded"
        assert data["refund_amount"] == 100_000

        # Verify state persisted
        refreshed = await db_session.get(Transaction, paid_transaction.id)
        assert refreshed.status == TransactionStatus.REFUNDED

    async def test_refund_amount_exceeds_total(
        self, client: AsyncClient, paid_transaction
    ):
        """Cannot refund more than total amount."""
        response = await client.post(
            f"/api/transactions/{paid_transaction.id}/refund",
            json={
                "refund_amount": 999_999,
            }
        )
        assert response.status_code == 400
        assert "exceeds" in response.json()["detail"].lower()
