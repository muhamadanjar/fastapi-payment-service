import secrets

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.domain.entity.application import Application as ApplicationEntity
from app.infrastructure.database.repositories.base import BaseSQLRepository

ApplicationModel = ApplicationEntity


class ApplicationRepository(BaseSQLRepository[ApplicationModel, ApplicationEntity]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model_cls=ApplicationModel, entity_cls=ApplicationEntity)

    async def regenerate_keys(self, app_id: str) -> ApplicationEntity | None:
        app = await self.get_by_id(app_id)
        if not app:
            return None
        updated = await self.update(
            app_id,
            {
                "app_key": f"app_{secrets.token_hex(8)}",
                "app_secret": secrets.token_hex(24),
            },
        )
        return updated

    async def get_by_key(self, app_key: str) -> ApplicationEntity | None:
        statement = select(self.model_cls).where(self.model_cls.app_key == app_key)
        result = await self.session.exec(statement)
        return self.to_domain(result.first())
