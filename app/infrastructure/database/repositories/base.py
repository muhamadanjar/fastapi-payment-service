from typing import Generic, TypeVar, Optional, List, Any, Union
from uuid import UUID
from math import ceil

from sqlmodel import select, func, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.inspection import inspect as sa_inspect
from app.domain.repository.interfaces import IRepository
from app.domain.repository.query_builder import QueryBuilder
from app.core.logging import get_logger


M = TypeVar('M', bound=SQLModel)
E = TypeVar('E')

logger = get_logger(__name__, log_file="repository.log")

class BaseSQLRepository(IRepository[E], Generic[M, E]):
    """
    Base repository implementation using SQLModel.
    Provides common CRUD operations and query building capabilities.
    """
    
    def __init__(self, session: AsyncSession, model_cls: type[M], entity_cls: type[E]):
        self.session = session
        self.model_cls = model_cls
        self.entity_cls = entity_cls
        self.query_builder = QueryBuilder(model_cls)

    def to_domain(self, model: Union[M, List[M], None]) -> Union[E, List[E], None]:
        """
        Convert DB Model to Domain Entity.
        
        Safely handles SQLAlchemy models with lazy-loaded relationships.
        Only includes attributes that are already loaded to avoid MissingGreenlet errors.
        """
        if model is None:
            return None
        if isinstance(model, list):
            return [self._model_to_entity(m) for m in model]
        return self._model_to_entity(model)
    
    def _model_to_dict(self, model: Any) -> Any:
        """
        Recursively convert a SQLModel (or any object) to a dictionary,
        including only attributes that are already loaded in SQLAlchemy.
        """
        if isinstance(model, list):
            return [self._model_to_dict(item) for item in model]
        
        # Check if it's a SQLModel instance with SQLAlchemy state
        if not isinstance(model, SQLModel):
            return model
            
        try:
            mapper = sa_inspect(model)
        except Exception:
            # Not an inspected SQLAlchemy object, return as is (e.g. dict, primitive)
            return model
            
        data = {}
        # Iterate over all attributes defined in the mapper
        for attr in mapper.attrs:
            # Only include attributes that are already loaded to avoid MissingGreenlet errors
            if attr.key not in mapper.unloaded:
                try:
                    value = getattr(model, attr.key)
                    # Recursively convert nested models/lists of models
                    data[attr.key] = self._model_to_dict(value)
                except Exception:
                    # Skip attributes that can't be accessed
                    continue
        return data

    def _model_to_entity(self, model: M) -> E:
        """
        Convert a single model instance to entity.
        This uses _model_to_dict to ensure only loaded data reached Pydantic.
        """
        data = self._model_to_dict(model)
        return self.entity_cls.model_validate(data)

    
    def _get_cleaned_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Filter out ALL relationship fields to prevent incomplete objects from reaching SQLAlchemy.
        Relationships must be set explicitly via FKs or dedicated sync methods.
        """
        try:
            mapper = sa_inspect(self.model_cls)
            relationship_keys = mapper.relationships.keys()
            # Skip all relationship fields — they cannot be set from DTOs
            filtered_data = {k: v for k, v in data.items() if k not in relationship_keys}
            return filtered_data
        except Exception:
            # Fallback for non-inspected models or other errors
            return data

    def to_model(self, entity: E) -> M:
        """Convert Domain Entity to DB Model. Excludes relationships to avoid incomplete objects."""
        if isinstance(entity, dict):
            data = entity
        elif hasattr(entity, 'model_dump'):
            data = entity.model_dump(exclude_unset=True)
        else:
            data = entity.dict()

        # Filter out relationships — they must be set explicitly via FKs, not from entity data
        try:
            mapper = sa_inspect(self.model_cls)
            relationship_keys = set(mapper.relationships.keys())
            data = {k: v for k, v in data.items() if k not in relationship_keys}
        except Exception:
            pass

        cleaned_data = self._get_cleaned_data(data)
        return self.model_cls(**cleaned_data)
    
    async def create(self, entity: E) -> E:
        """Create a new entity."""
        model = self.to_model(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self.to_domain(model)
    
    async def get_by_id(self, id: Union[str, UUID]) -> Optional[E]:
        """Get entity by ID."""
        statement = select(self.model_cls).where(self.model_cls.id == id)
        result = await self.session.exec(statement)
        return self.to_domain(result.first())
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[E]:
        """Get all entities with pagination."""
        statement = select(self.model_cls).offset(skip).limit(limit)
        result = await self.session.exec(statement)
        return self.to_domain(result.all())
    
    async def update(self, id: Union[str, UUID], entity: E) -> Optional[E]:
        """
        Update an entity.
        """
        # Fetch existing model (not entity)
        statement = select(self.model_cls).where(self.model_cls.id == id)
        result = await self.session.exec(statement)
        db_obj = result.first()

        if not db_obj:
            return None
            
        # Prepare update data
        if hasattr(entity, 'model_dump'):
            update_data = entity.model_dump(exclude_unset=True)
        elif hasattr(entity, 'dict'):
            update_data = entity.dict(exclude_unset=True)
        else:
            update_data = entity
        
        # Get relationship keys to exclude from update
        mapper = sa_inspect(self.model_cls)
        relationship_keys = mapper.relationships.keys()

        for key, value in update_data.items():
            if key in relationship_keys:
                continue
            if hasattr(db_obj, key):
                setattr(db_obj, key, value)
            
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return self.to_domain(db_obj)
    
    async def delete(self, id: Union[str, UUID]) -> bool:
        """Delete an entity."""
        statement = select(self.model_cls).where(self.model_cls.id == id)
        result = await self.session.exec(statement)
        db_obj = result.first()
        
        if not db_obj:
            return False
            
        await self.session.delete(db_obj)
        await self.session.commit()
        return True

    def get_load_options(self, load: list[str]) -> list[Any]:
        """Override in repository child for relation definitions."""
        return []

    def build_filter_query(self, load: Optional[List[str]] = None, **filters):
        """Build query with flexible criteria format using QueryBuilder."""
        logger.info("Build filter query: %s", filters)
        return self.query_builder.build_filter_query(
            load=load or [],
            get_load_options_func=self.get_load_options,
            **filters
        )

    async def filter_data(self, **filters):
        """Filter data based on criteria."""
        query = self.build_filter_query(**filters)
        result = await self.session.exec(query)
        return self.to_domain(result.all())

    async def count_filtered(self, **filters):
        """Count filtered results."""
        query = self.build_filter_query(**filters)
        count_query = query.with_only_columns(func.count()).order_by(None)
        result = await self.session.exec(count_query)
        return result.one()

    async def paginate(self, skip: int = 0, limit: int = 10, **filters):
        """Paginate filtered results."""
        # Base query
        query = self.build_filter_query(**filters)

        logger.info("Filter query: %s", filters)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.exec(count_query)
        total = count_result.one() or 0
        
        # Paginated query
        query = query.offset(skip).limit(limit)
        result = await self.session.exec(query)
        data = result.all() # These are Models

        return {
            "data": self.to_domain(data),
            "metas": {
                "total": total,
                "per_page": limit,
                "current_page": (skip // limit) + 1,
                "total_pages": ceil(total / limit) if limit else 1,
            }
        }

    async def exists(self, **kwargs) -> bool:
        """Check if entity exists based on given criteria."""
        stmt = select(self.model_cls).where(
            *[getattr(self.model_cls, k) == v for k, v in kwargs.items()]
        )
        result = await self.session.exec(stmt)
        return result.first() is not None

    async def get_or_create(self, defaults: Optional[dict] = None, **kwargs) -> tuple[E, bool]:
        """Get an existing entity or create a new one if it doesn't exist."""
        stmt = select(self.model_cls).where(
            *[getattr(self.model_cls, k) == v for k, v in kwargs.items()]
        )
        result = await self.session.exec(stmt)
        instance = result.first()
        
        if instance:
            return self.to_domain(instance), False
        
        # Create new instance
        params = {**kwargs, **(defaults or {})}
        cleaned_params = self._get_cleaned_data(params)
        instance = self.model_cls(**cleaned_params)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return self.to_domain(instance), True

    async def update_or_create(self, defaults: Optional[dict] = None, **kwargs) -> tuple[E, bool]:
        """Update an existing entity or create a new one if it doesn't exist."""
        stmt = select(self.model_cls).where(
            *[getattr(self.model_cls, k) == v for k, v in kwargs.items()]
        )
        result = await self.session.exec(stmt)
        instance = result.first()
        
        if instance:
            # Update existing instance
            for key, value in (defaults or {}).items():
                setattr(instance, key, value)
            self.session.add(instance)
            await self.session.commit()
            await self.session.refresh(instance)
            return self.to_domain(instance), False
        
        # Create new instance
        params = {**kwargs, **(defaults or {})}
        cleaned_params = self._get_cleaned_data(params)
        instance = self.model_cls(**cleaned_params)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return self.to_domain(instance), True

