from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.domain.entity.product import Product
from app.infrastructure.database.repositories.base import BaseSQLRepository


class ProductRepository(BaseSQLRepository[Product, Product]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model_cls=Product, entity_cls=Product)

    async def get_by_code(self, product_code: str) -> Product | None:
        statement = select(self.model_cls).where(self.model_cls.product_code == product_code)
        result = await self.session.exec(statement)
        return self.to_domain(result.first())
    