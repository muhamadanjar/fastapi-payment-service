from app.domain.entity.product import Product
from app.domain.repository.base import BaseRepository
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Session

class ProductRepository(BaseRepository[Product]):
    def __init__(self, session: Session):
        self.session = session
        self.model = Product