from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.domain.entity.transactions import Transaction as TransactionEntity
from app.infrastructure.database.repositories.base import BaseSQLRepository

TransactionModel = TransactionEntity


class TransactionRepository(BaseSQLRepository[TransactionModel, TransactionEntity]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model_cls=TransactionModel, entity_cls=TransactionEntity)

    async def get_by_invoice_number(self, invoice_number: str) -> TransactionEntity | None:
        statement = select(self.model_cls).where(self.model_cls.invoice_number == invoice_number)
        result = await self.session.exec(statement)
        return self.to_domain(result.first())

    async def get_by_transaction_code(self, transaction_code: str) -> TransactionEntity | None:
        statement = select(self.model_cls).where(self.model_cls.transaction_code == transaction_code)
        result = await self.session.exec(statement)
        return self.to_domain(result.first())

    async def get_by_payment_reference(self, payment_reference: str) -> TransactionEntity | None:
        statement = select(self.model_cls).where(self.model_cls.payment_reference == payment_reference)
        result = await self.session.exec(statement)
        return self.to_domain(result.first())