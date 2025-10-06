from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Any, Dict, Union
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import and_, asc, desc, inspect, or_, select, func
from math import ceil

T = TypeVar('T')

class BaseRepository(Generic[T], ABC):

    model: type[T]

    @abstractmethod
    async def create(self, entity: T) -> T:
        pass
    
    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional[T]:
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        pass
    
    @abstractmethod
    async def update(self, id: UUID, entity: T) -> Optional[T]:
        pass
    
    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        pass

    def get_load_options(self, load: list[str]) -> list[Any]:
        """Override di repo child untuk definisi relasi"""
        return []

    def get_column_by_path(self, path: str):
        """Ambil kolom dari nested path (misal: 'user.email')"""
        parts = path.split('.')
        current_model = self.model
        column = None

        for idx, part in enumerate(parts):
            mapper = inspect(current_model)
            if part in mapper.columns:
                column = mapper.columns[part]
                if idx == len(parts) - 1:  # Last part, should be column
                    break
            elif part in mapper.relationships:
                # Ambil model relasi dan lanjutkan ke kolom berikutnya
                rel = mapper.relationships[part]
                current_model = rel.mapper.class_
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"'{part}' is not a valid field or relation on '{current_model.__name__}'"
                )
        
        if column is None:
            raise HTTPException(status_code=400, detail=f"Column not found for path '{path}'")

        return column

    def apply_operator(self, column, operator: str, value: Any):
        """Apply operator to column with value"""
        try:
            # Get python type for conversion
            try:
                python_type = column.type.python_type
            except (NotImplementedError, AttributeError):
                python_type = str  # fallback

            # Convert value to appropriate type
            if python_type is bool and not isinstance(value, bool):
                if isinstance(value, str):
                    value = value.lower() in ("true", "1", "yes")
                else:
                    value = bool(value)
            elif python_type is not str and not isinstance(value, python_type):
                try:
                    value = python_type(value)
                except (ValueError, TypeError):
                    # Keep original value if conversion fails
                    pass

            # Apply operator
            operator = operator.lower()
            if operator in ['=', '==', 'eq']:
                return column == value
            elif operator in ['!=', '<>', 'ne']:
                return column != value
            elif operator in ['>', 'gt']:
                return column > value
            elif operator in ['>=', 'gte']:
                return column >= value
            elif operator in ['<', 'lt']:
                return column < value
            elif operator in ['<=', 'lte']:
                return column <= value
            elif operator in ['like', 'ilike']:
                if operator == 'like':
                    return column.like(f"%{value}%")
                else:
                    return column.ilike(f"%{value}%")
            elif operator in ['not_like', 'not_ilike']:
                if operator == 'not_like':
                    return ~column.like(f"%{value}%")
                else:
                    return ~column.ilike(f"%{value}%")
            elif operator in ['in']:
                if not isinstance(value, (list, tuple)):
                    raise HTTPException(status_code=400, detail="'in' operator requires a list/array value")
                return column.in_(value)
            elif operator in ['not_in']:
                if not isinstance(value, (list, tuple)):
                    raise HTTPException(status_code=400, detail="'not_in' operator requires a list/array value")
                return ~column.in_(value)
            elif operator in ['is_null']:
                return column.is_(None)
            elif operator in ['is_not_null']:
                return column.is_not(None)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported operator: {operator}")

        except Exception as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Error applying operator '{operator}' to field '{column}' with value '{value}': {str(e)}"
            )

    def parse_condition(self, condition: Union[List, Dict]) -> Any:
        """Parse single condition from array or dict format"""
        
        if isinstance(condition, dict):
            # Old dict format: {'field': 'name', 'operator': '=', 'value': 'john'}
            if 'field' not in condition:
                raise HTTPException(status_code=400, detail="Dict condition must have 'field' key")
            
            field = condition['field']
            operator = condition.get('operator', '=')
            value = condition.get('value')
            
        elif isinstance(condition, list):
            # New array format
            if len(condition) == 2:
                # Short form: ['field', 'value'] - assumes '=' operator
                field, value = condition
                operator = '='
            elif len(condition) == 3:
                # Full form: ['field', 'operator', 'value']
                field, operator, value = condition
            else:
                raise HTTPException(
                    status_code=400, 
                    detail="Array condition must have 2 or 3 elements: [field, value] or [field, operator, value]"
                )
        else:
            raise HTTPException(
                status_code=400, 
                detail="Condition must be either dict or array format"
            )

        # Get column and apply operator
        column = self.get_column_by_path(field)
        return self.apply_operator(column, operator, value)

    def parse_criteria(self, criteria: Union[Dict, List, str]) -> Any:
        """Parse criteria recursively"""
        
        if isinstance(criteria, str):
            # Legacy string format support
            return self.parse_legacy_criteria(criteria)
        
        if isinstance(criteria, list):
            # If it's a simple array condition
            return self.parse_condition(criteria)
        
        if isinstance(criteria, dict):
            if 'and' in criteria:
                conditions = []
                for condition in criteria['and']:
                    conditions.append(self.parse_criteria(condition))
                return and_(*conditions)
            
            elif 'or' in criteria:
                conditions = []
                for condition in criteria['or']:
                    conditions.append(self.parse_criteria(condition))
                return or_(*conditions)
            
            else:
                # Single dict condition (old format)
                return self.parse_condition(criteria)
        
        raise HTTPException(status_code=400, detail="Invalid criteria format")

    def parse_legacy_criteria(self, criteria: str) -> Any:
        """Parse legacy string criteria format for backward compatibility"""
        def parse_condition_str(param: str):
            if ':' not in param:
                raise HTTPException(status_code=400, detail=f"Invalid format: '{param}'")
            field_path, raw_value = param.split(':', 1)
            column = self.get_column_by_path(field_path)
           
            try:
                python_type = column.type.python_type
            except (NotImplementedError, AttributeError):
                python_type = str

            try:
                if python_type is str:
                    return column.ilike(f"%{raw_value}%")
                if python_type is bool:
                    return column == (raw_value.lower() in ("true", "1", "yes"))
                return column == python_type(raw_value)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid value '{raw_value}' for field '{field_path}'")

        # Parse legacy format
        if criteria.startswith("and(") and criteria.endswith(")"):
            raw = criteria[4:-1]
            return and_(*[parse_condition_str(p.strip()) for p in raw.split(',')])
        if criteria.startswith("or(") and criteria.endswith(")"):
            raw = criteria[3:-1]
            return or_(*[parse_condition_str(p.strip()) for p in raw.split(',')])
        return and_(*[parse_condition_str(p.strip()) for p in criteria.split(',')])

    def build_filter_query(self, load: List[str] = [], **filters):
        """
        Build query with flexible criteria format.
        
        Examples:
        # New array format
        criteria = {
            'and': [
                ['name', 'like', 'john'],
                ['age', '>=', 18],
                ['is_active', True]  # Short form
            ]
        }
        
        # Legacy string format (still supported)
        criteria = "name:john,age:18"
        
        # Mixed format
        criteria = {
            'and': [
                ['name', 'like', 'john'],
                {'field': 'age', 'operator': '>=', 'value': 18}
            ]
        }
        """
        criteria = filters.get("criteria")
        sortby = filters.get("sortby", '')
        query = select(self.model)

        # Load eager relations
        load_options = self.get_load_options(load)
        if load_options:
            query = query.options(*load_options)

        # Apply criteria
        if criteria:
            where_clause = self.parse_criteria(criteria)
            query = query.where(where_clause)

        # Apply sorting
        if sortby:
            order_by_items = []
            # Support both string and array format for sortby
            if isinstance(sortby, str):
                # Legacy string format: "field:asc,field2:desc"
                for param in sortby.split(','):
                    if ':' not in param:
                        raise HTTPException(status_code=400, detail=f"Invalid sortby format: '{param}'")
                    field_path, direction = param.split(':', 1)
                    column = self.get_column_by_path(field_path)
                    if direction == 'asc':
                        order_by_items.append(asc(column))
                    elif direction == 'desc':
                        order_by_items.append(desc(column))
                    else:
                        raise HTTPException(status_code=400, detail=f"Invalid sort order '{direction}'")
            elif isinstance(sortby, list):
                # Array format: [['field', 'asc'], ['field2', 'desc']]
                for sort_item in sortby:
                    if len(sort_item) != 2:
                        raise HTTPException(status_code=400, detail="Sort item must have exactly 2 elements: [field, direction]")
                    field_path, direction = sort_item
                    column = self.get_column_by_path(field_path)
                    if direction == 'asc':
                        order_by_items.append(asc(column))
                    elif direction == 'desc':
                        order_by_items.append(desc(column))
                    else:
                        raise HTTPException(status_code=400, detail=f"Invalid sort order '{direction}'")
            
            if order_by_items:
                query = query.order_by(*order_by_items)

        return query

    async def filter_data(self, **filters):
        query = self.build_filter_query(**filters)
        result = await self.session.exec(query)
        return result.all()

    async def count_filtered(self, **filters):
        query = self.build_filter_query(**filters)
        count_query = query.with_only_columns(func.count()).order_by(None)
        result = await self.session.exec(count_query)
        return result.one()

    async def paginate(self, skip: int = 0, limit: int = 10, **filters):
        # Base query
        query = self.build_filter_query(**filters)

        # Count
        count_query = query.with_only_columns(func.count()).order_by(None)
        count_result = await self.session.exec(count_query)
        total = count_result.one()

        # Paginated query
        query = query.offset(skip).limit(limit)
        result = await self.session.exec(query)
        data = result.all()

        return {
            "data": data,
            "metas": {
                "total": total,
                "per_page": limit,
                "current_page": (skip // limit) + 1,
                "total_pages": ceil(total / limit) if limit else 1,
            }
        }