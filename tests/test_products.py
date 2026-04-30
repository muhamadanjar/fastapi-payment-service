import pytest
from httpx import AsyncClient

from app.domain.entity.product import Product
from tests.fixtures.db_fixtures import (  # noqa: F401
    application,
    product,
)


class TestProductCreate:
    async def test_create_product(self, client: AsyncClient, application):
        """Create a new product."""
        response = await client.post(
            "/api/products/",
            json={
                "application_id": application.id,
                "product_code": "NEW-PROD-001",
                "product_name": "New Test Product",
                "price": 50_000,
                "currency": "IDR",
                "stock": 5,
                "is_active": True,
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] is not None
        assert data["product_code"] == "NEW-PROD-001"
        assert data["product_name"] == "New Test Product"
        assert data["price"] == 50_000
        assert data["is_active"] is True


class TestProductGet:
    async def test_get_product_by_id(self, client: AsyncClient, product):
        """Retrieve a product by ID."""
        response = await client.get(f"/api/products/{product.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == product.id
        assert data["product_code"] == product.product_code
        assert data["product_name"] == product.product_name


class TestProductDelete:
    async def test_delete_product_soft_delete(
        self, client: AsyncClient, product, db_session
    ):
        """Delete (soft delete) a product."""
        response = await client.delete(f"/api/products/{product.id}")
        assert response.status_code == 200

        # Verify soft delete: is_active should be False
        refreshed = await db_session.get(Product, product.id)
        assert refreshed.is_active is False
