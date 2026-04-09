from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.domain.entity.product import Product as ProductEntity
from app.infrastructure.database.repositories.base import BaseSQLRepository

# NOTE:
# Saat ini SQLModel table dan domain entity masih memakai class yang sama.
# Alias ini dipakai untuk memperjelas niat pemisahan layer.
ProductModel = ProductEntity


class ProductRepository(BaseSQLRepository[ProductModel, ProductEntity]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model_cls=ProductModel, entity_cls=ProductEntity)

    async def get_by_code(self, product_code: str) -> ProductEntity | None:
        statement = select(self.model_cls).where(self.model_cls.product_code == product_code)
        result = await self.session.exec(statement)
        return self.to_domain(result.first())
    