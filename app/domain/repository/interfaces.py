from typing import TypeVar, Generic, Optional, List, Union
from abc import ABC, abstractmethod
from uuid import UUID
T = TypeVar('T')


class IRepository(Generic[T], ABC):
    """Base repository interface."""
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity."""
        pass
    
    @abstractmethod
    async def get_by_id(self, id: Union[str, UUID]) -> Optional[T]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination."""
        pass
    
    @abstractmethod
    async def update(self, id: Union[str, UUID], entity: T) -> Optional[T]:
        """Update an entity."""
        pass
    
    @abstractmethod
    async def delete(self, id: Union[str, UUID]) -> bool:
        """Delete an entity."""
        pass

