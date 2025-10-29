
from typing import List, Optional, Union
from sqlmodel import Session, select
from app.domain.entity.transactions import Transaction
from app.domain.repository.base import BaseRepository
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, session: Union[Session, AsyncSession]):
        super().__init__(session)
        self.model = Transaction
    
    def create(self, entity: Transaction) -> Transaction:
        """Sync create product"""
        if self._is_async():
            raise RuntimeError("Cannot use sync method with AsyncSession. Use create_async() instead.")
        
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def get_by_id(self, id: str) -> Optional[Transaction]:
        """Sync get product by id"""
        if self._is_async():
            raise RuntimeError("Cannot use sync method with AsyncSession. Use get_by_id_async() instead.")
        
        statement = select(Transaction).where(Transaction.id == id)
        result = self.session.exec(statement)
        return result.first()
    

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Transaction]:
        """Sync get all products"""
        if self._is_async():
            raise RuntimeError("Cannot use sync method with AsyncSession. Use get_all_async() instead.")
        
        statement = select(Transaction).offset(skip).limit(limit)
        result = self.session.exec(statement)
        return result.all()

    def update(self, id: str, entity: Union[Transaction, dict]) -> Optional[Transaction]:
        """Sync update product"""
        if self._is_async():
            raise RuntimeError("Cannot use sync method with AsyncSession. Use update_async() instead.")
        
        db_obj = self.get_by_id(id)
        if not db_obj:
            return None

        if isinstance(entity, dict):
            update_data = entity
        else:
            update_data = entity.model_dump(exclude_unset=True)

        try:
            for key, value in update_data.items():
                if hasattr(db_obj, key) and key != 'id':
                    setattr(db_obj, key, value)
            
            db_obj.updated_at = datetime.utcnow()
            
            self.session.add(db_obj)
            self.session.commit()
            self.session.refresh(db_obj)
            
            return db_obj
            
        except Exception as e:
            self.session.rollback()
            raise e


    def delete(self, id: str) -> bool:
        """Sync delete transaction"""
        if self._is_async():
            raise RuntimeError("Cannot use sync method with AsyncSession. Use delete_async() instead.")
        
        db_obj = self.get_by_id(id)
        if not db_obj:
            return False

        self.session.delete(db_obj)
        self.session.commit()
        return True
    
    async def create_async(self, entity: Transaction) -> Transaction:
        """Async create product"""
        if not self._is_async():
            raise RuntimeError("Cannot use async method with sync Session. Use create() instead.")
        
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def get_by_id_async(self, id: str) -> Optional[Transaction]:
        """Async get product by id"""
        if not self._is_async():
            raise RuntimeError("Cannot use async method with sync Session. Use get_by_id() instead.")
        
        statement = select(Transaction).where(Transaction.id == id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
    
    async def get_all_async(self, skip: int = 0, limit: int = 100) -> List[Transaction]:
        """Async get all products"""
        if not self._is_async():
            raise RuntimeError("Cannot use async method with sync Session. Use get_all() instead.")
        
        statement = select(Transaction).offset(skip).limit(limit)
        result = await self.session.execute(statement)
        return result.scalars().all()
    
    async def update_async(self, id: str, entity: Union[Transaction, dict]) -> Optional[Transaction]:
        """Async update product"""
        if not self._is_async():
            raise RuntimeError("Cannot use async method with sync Session. Use update() instead.")
        
        db_obj = await self.get_by_id_async(id)
        if not db_obj:
            return None

        if isinstance(entity, dict):
            update_data = entity
        else:
            update_data = entity.model_dump(exclude_unset=True)

        try:
            for key, value in update_data.items():
                if hasattr(db_obj, key) and key != 'id':
                    setattr(db_obj, key, value)
            
            db_obj.updated_at = datetime.utcnow()
            
            self.session.add(db_obj)
            await self.session.commit()
            await self.session.refresh(db_obj)
            
            return db_obj
            
        except Exception as e:
            await self.session.rollback()
            raise e

    async def delete_async(self, id: str) -> bool:
        """Async delete product"""
        if not self._is_async():
            raise RuntimeError("Cannot use async method with sync Session. Use delete() instead.")
        
        db_obj = await self.get_by_id_async(id)
        if not db_obj:
            return False

        await self.session.delete(db_obj)
        await self.session.commit()
        return True