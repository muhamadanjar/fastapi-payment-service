from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.domain.entity.payments import (
    PaymentGateway as PaymentGatewayEntity,
    PaymentGatewayCredential as PaymentGatewayCredentialEntity,
)
from app.domain.entity.payment_gateway import (
    PaymentGatewayCallback as PaymentGatewayCallbackEntity,
    PaymentGatewayRequest as PaymentGatewayRequestEntity,
)
from app.infrastructure.database.repositories.base import BaseSQLRepository

PaymentGatewayModel = PaymentGatewayEntity
PaymentGatewayCredentialModel = PaymentGatewayCredentialEntity
PaymentGatewayRequestModel = PaymentGatewayRequestEntity
PaymentGatewayCallbackModel = PaymentGatewayCallbackEntity


class PaymentGatewayRepository(BaseSQLRepository[PaymentGatewayModel, PaymentGatewayEntity]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model_cls=PaymentGatewayModel, entity_cls=PaymentGatewayEntity)

    async def list_active(self) -> list[PaymentGatewayEntity]:
        statement = select(self.model_cls).where(self.model_cls.is_active == True).order_by(self.model_cls.priority.asc())  # noqa: E712
        result = await self.session.exec(statement)
        return self.to_domain(result.all())

    async def get_by_code(self, gateway_code: str) -> PaymentGatewayEntity | None:
        statement = select(self.model_cls).where(self.model_cls.gateway_code == gateway_code)
        result = await self.session.exec(statement)
        return self.to_domain(result.first())


class PaymentGatewayCredentialRepository(
    BaseSQLRepository[PaymentGatewayCredentialModel, PaymentGatewayCredentialEntity]
):
    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session,
            model_cls=PaymentGatewayCredentialModel,
            entity_cls=PaymentGatewayCredentialEntity,
        )

    async def list_by_application(self, application_id: str) -> list[PaymentGatewayCredentialEntity]:
        statement = select(self.model_cls).where(self.model_cls.application_id == application_id)
        result = await self.session.exec(statement)
        return self.to_domain(result.all())

    async def get_active_credential(
        self,
        application_id: str,
        gateway_id: str,
    ) -> PaymentGatewayCredentialEntity | None:
        statement = select(self.model_cls).where(
            self.model_cls.application_id == application_id,
            self.model_cls.gateway_id == gateway_id,
            self.model_cls.is_active == True,  # noqa: E712
        )
        result = await self.session.exec(statement)
        return self.to_domain(result.first())


class PaymentGatewayRequestRepository(BaseSQLRepository[PaymentGatewayRequestModel, PaymentGatewayRequestEntity]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model_cls=PaymentGatewayRequestModel, entity_cls=PaymentGatewayRequestEntity)


class PaymentGatewayCallbackRepository(BaseSQLRepository[PaymentGatewayCallbackModel, PaymentGatewayCallbackEntity]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model_cls=PaymentGatewayCallbackModel, entity_cls=PaymentGatewayCallbackEntity)
