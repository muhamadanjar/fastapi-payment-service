"""
Query builder utilities for domain layer.

This module provides query building functionality without presentation layer dependencies.
"""
from typing import Any, Dict, List, Union
from sqlmodel import and_, asc, desc, inspect, or_, select, func
from app.core.exceptions import BadRequestError
from app.core.logging import get_logger

logger = get_logger(__name__, log_file="query_builder.log")


class QueryBuilderException(Exception):
    """Exception raised by query builder."""
    pass


class QueryBuilder:
    """Query builder for flexible filtering and sorting."""
    
    def __init__(self, model: type):
        self.model = model
    
    def get_column_by_path(self, path: str):
        """Get column from nested path (e.g., 'user.email')."""
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
                # Get related model and continue to next column
                rel = mapper.relationships[part]
                current_model = rel.mapper.class_
            else:
                raise QueryBuilderException(
                    f"'{part}' is not a valid field or relation on '{current_model.__name__}'"
                )
        
        if column is None:
            raise QueryBuilderException(f"Column not found for path '{path}'")

        return column

    def apply_operator(self, column, operator: str, value: Any):
        """Apply operator to column with value."""
        try:
            # Get python type for conversion
            try:
                python_type = column.type.python_type
            except (NotImplementedError, AttributeError):
                python_type = str  # fallback

            is_subquery = hasattr(value, 'c') or hasattr(value, 'subquery') or hasattr(value, 'statement')

            # Convert value to appropriate type
            if not is_subquery:
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
                # Relaxed check to allow SQLAlchemy subqueries/selectables
                if not isinstance(value, (list, tuple)) and not hasattr(value, 'c') and not hasattr(value, 'subquery'):
                     # If it's not a list/tuple and doesn't look like a query/selectable, it *might* be invalid,
                     # but we'll let SQLAlchemy handle the final validation or error if it's incompatible.
                     pass
                return column.in_(value)
            elif operator in ['not_in']:
                 # Relaxed check to allow SQLAlchemy subqueries
                return ~column.in_(value)
            elif operator in ['is_null']:
                return column.is_(None)
            elif operator in ['is_not_null']:
                return column.is_not(None)
            else:
                raise QueryBuilderException(f"Unsupported operator: {operator}")

        except Exception as e:
            raise QueryBuilderException(
                f"Error applying operator '{operator}' to field '{column}' with value '{value}': {str(e)}"
            )

    def parse_condition(self, condition: Union[List, Dict]) -> Any:
        """Parse single condition from array or dict format."""
        
        if isinstance(condition, dict):
            # Old dict format: {'field': 'name', 'operator': '=', 'value': 'john'}
            if 'field' not in condition:
                raise QueryBuilderException("Dict condition must have 'field' key")
            
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
                raise QueryBuilderException(
                    "Array condition must have 2 or 3 elements: [field, value] or [field, operator, value]"
                )
        else:
            raise QueryBuilderException("Condition must be either dict or array format")

        # Get column and apply operator
        column = self.get_column_by_path(field)
        return self.apply_operator(column, operator, value)

    def parse_criteria(self, criteria: Union[Dict, List, str]) -> Any:
        """Parse criteria recursively."""
        
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
        
        raise QueryBuilderException("Invalid criteria format")

    def parse_legacy_criteria(self, criteria: str) -> Any:
        """Parse legacy string criteria format for backward compatibility."""
        def parse_condition_str(param: str):
            if ':' not in param:
                raise QueryBuilderException(f"Invalid format: '{param}'")
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
                raise QueryBuilderException(f"Invalid value '{raw_value}' for field '{field_path}'")

        # Parse legacy format
        if criteria.startswith("and(") and criteria.endswith(")"):
            raw = criteria[4:-1]
            return and_(*[parse_condition_str(p.strip()) for p in raw.split(',')])
        if criteria.startswith("or(") and criteria.endswith(")"):
            raw = criteria[3:-1]
            return or_(*[parse_condition_str(p.strip()) for p in raw.split(',')])
        return and_(*[parse_condition_str(p.strip()) for p in criteria.split(',')])

    def parse_sortby(self, sortby: Union[str, List]) -> List[Any]:
        """Parse sortby parameter into SQLAlchemy order_by items."""
        order_by_items = []
        normalized_sorts = []
        
        if isinstance(sortby, str):
            # Legacy string format: "field:asc,field2:desc"
            for param in sortby.split(','):
                if ':' not in param:
                    raise QueryBuilderException(f"Invalid sortby format: '{param}'")
                normalized_sorts.append(param.split(':', 1))
        elif isinstance(sortby, list):
            # Array format: [['field', 'asc'], ['field2', 'desc']]
            normalized_sorts = sortby
        else:
             raise QueryBuilderException("Sortby must be either string or array format")
        
        for sort_item in normalized_sorts:
            if len(sort_item) != 2:
                raise QueryBuilderException("Sort item must have exactly 2 elements: [field, direction]")
            
            field_path, direction = sort_item
            column = self.get_column_by_path(field_path)
            
            if direction == 'asc':
                order_by_items.append(asc(column))
            elif direction == 'desc':
                order_by_items.append(desc(column))
            else:
                raise QueryBuilderException(f"Invalid sort order '{direction}'")
                
        return order_by_items

    def build_filter_query(self, load: List[str] = [], get_load_options_func=None, **filters):
        """
        Build query with flexible criteria format.
        
        Examples:
        ## New array format
        criteria = {
            'and': [
                ['name', 'like', 'john'],
                ['age', '>=', 18],
                ['is_active', True]  # Short form
            ]
        }
        
        ## Legacy string format (still supported)
        criteria = "name:john,age:18"
        
        ## Mixed format
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

        logger.info("QB Filters: %s", filters)
        logger.info("QB Criteria: %s", criteria)
        logger.info("QB Sortby: %s", sortby)
        # Load eager relations (to be implemented by subclasses)
        if get_load_options_func:
            load_options = get_load_options_func(load)
        else:
            load_options = self.get_load_options(load)
        if load_options:
            query = query.options(*load_options)

        # Apply criteria
        if criteria:
            try:
                where_clause = self.parse_criteria(criteria)
                query = query.where(where_clause)
            except QueryBuilderException as e:
                # Convert to HTTPException at presentation layer
                raise BadRequestError(message=str(e))

        # Apply sorting
        if sortby:
            try:
                order_by_items = self.parse_sortby(sortby)
                if order_by_items:
                    query = query.order_by(*order_by_items)
            except QueryBuilderException as e:
                # Convert to HTTPException at presentation layer
                raise BadRequestError(message=str(e))

        return query
    
    def get_load_options(self, load: list[str]) -> list[Any]:
        """Override in repository child for relation definitions."""
        return []

