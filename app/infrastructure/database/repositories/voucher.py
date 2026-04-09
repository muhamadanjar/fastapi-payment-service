from datetime import datetime

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.domain.entity.voucher import (
    Voucher as VoucherEntity,
    VoucherCondition as VoucherConditionEntity,
    VoucherEligibleUser as VoucherEligibleUserEntity,
)
from app.infrastructure.database.repositories.base import BaseSQLRepository

VoucherModel = VoucherEntity
VoucherConditionModel = VoucherConditionEntity
VoucherEligibleUserModel = VoucherEligibleUserEntity


class VoucherRepository(BaseSQLRepository[VoucherModel, VoucherEntity]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model_cls=VoucherModel, entity_cls=VoucherEntity)

    async def get_by_code(self, voucher_code: str) -> VoucherEntity | None:
        statement = select(self.model_cls).where(self.model_cls.voucher_code == voucher_code)
        result = await self.session.exec(statement)
        return self.to_domain(result.first())

    async def get_active_public(self) -> list[VoucherEntity]:
        now = datetime.utcnow()
        statement = select(self.model_cls).where(
            self.model_cls.is_active == True,  # noqa: E712
            self.model_cls.voucher_type == "public",
            (self.model_cls.valid_from.is_(None) | (self.model_cls.valid_from <= now)),
            (self.model_cls.valid_until.is_(None) | (self.model_cls.valid_until >= now)),
        )
        result = await self.session.exec(statement)
        return self.to_domain(result.all())


class VoucherConditionRepository(BaseSQLRepository[VoucherConditionModel, VoucherConditionEntity]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model_cls=VoucherConditionModel, entity_cls=VoucherConditionEntity)

    async def list_by_voucher(self, voucher_id: str) -> list[VoucherConditionEntity]:
        statement = select(self.model_cls).where(self.model_cls.voucher_id == voucher_id)
        result = await self.session.exec(statement)
        return self.to_domain(result.all())


class VoucherEligibleUserRepository(BaseSQLRepository[VoucherEligibleUserModel, VoucherEligibleUserEntity]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model_cls=VoucherEligibleUserModel, entity_cls=VoucherEligibleUserEntity)

    async def list_by_user(
        self,
        user_id: str | None = None,
        is_claimed: bool | None = None,
        is_expired: bool | None = None,
    ) -> list[VoucherEligibleUserEntity]:
        now = datetime.utcnow()
        statement = select(self.model_cls)
        if user_id:
            statement = statement.where(self.model_cls.user_id == user_id)
        if is_claimed is not None:
            statement = statement.where(self.model_cls.is_claimed == is_claimed)
        if is_expired is True:
            statement = statement.where(self.model_cls.expires_at.is_not(None), self.model_cls.expires_at < now)
        elif is_expired is False:
            statement = statement.where(self.model_cls.expires_at.is_(None) | (self.model_cls.expires_at >= now))
        result = await self.session.exec(statement)
        return self.to_domain(result.all())

    async def get_by_voucher_and_user(self, voucher_id: str, user_id: str) -> VoucherEligibleUserEntity | None:
        statement = select(self.model_cls).where(
            self.model_cls.voucher_id == voucher_id,
            self.model_cls.user_id == user_id,
        )
        result = await self.session.exec(statement)
        return self.to_domain(result.first())

    async def list_by_voucher(self, voucher_id: str) -> list[VoucherEligibleUserEntity]:
        statement = select(self.model_cls).where(self.model_cls.voucher_id == voucher_id)
        result = await self.session.exec(statement)
        return self.to_domain(result.all())
