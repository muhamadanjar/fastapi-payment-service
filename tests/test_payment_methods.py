from httpx import AsyncClient

from tests.fixtures.db_fixtures import (  # noqa: F401
    payment_method,
)


class TestPaymentMethodList:
    async def test_list_payment_methods(self, client: AsyncClient, payment_method):
        """List all active payment methods."""
        response = await client.get("/api/payment-methods/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "data" in data
        methods = data["data"]
        assert len(methods) > 0

        # Verify fixture payment method is in the list
        method_ids = [m["id"] for m in methods]
        assert payment_method.id in method_ids


class TestCalculateFee:
    async def test_calculate_fee_fixed_amount(
        self, client: AsyncClient, payment_method
    ):
        """Calculate fee for a fixed-fee payment method."""
        response = await client.post(
            f"/api/payment-methods/{payment_method.id}/calculate-fee",
            json={"amount": 100_000}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["admin_fee"] == 4000.0  # Fixed fee
        assert data["total_with_fee"] == 104_000.0
