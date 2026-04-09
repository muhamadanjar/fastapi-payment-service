from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.domain.entity.payments import PaymentMethod as PaymentMethodEntity
from app.infrastructure.database.repositories.base import BaseSQLRepository

PaymentMethodModel = PaymentMethodEntity


class PaymentMethodRepository(BaseSQLRepository[PaymentMethodModel, PaymentMethodEntity]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model_cls=PaymentMethodModel, entity_cls=PaymentMethodEntity)

    async def get_active(self, method_type: str | None = None) -> list[PaymentMethodEntity]:
        statement = select(self.model_cls).where(self.model_cls.is_active == True)  # noqa: E712
        if method_type:
            statement = statement.where(self.model_cls.method_type == method_type)
        result = await self.session.exec(statement)
        return self.to_domain(result.all())
