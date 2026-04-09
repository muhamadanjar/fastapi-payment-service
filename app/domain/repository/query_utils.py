"""
Query utilities for building and merging filter criteria.

This module provides utilities for working with Odoo-style domain criteria
in a clean, reusable way without HTTP dependencies.
"""


def merge_criteria(base: dict, extra: dict, default_operator: str = "and") -> dict:
    """
    Merge dua criteria dict dengan format Odoo domain.
    
    Format domain: 
    - {"and": [[field, operator, value], ...]}
    - {"or": [[field, operator, value], ...]}
    
    Args:
        base: Dict criteria pertama
        extra: Dict criteria kedua  
        default_operator: Operator default ("and" atau "or")
    
    Returns:
        Dict hasil merge
    """
    # Handle empty cases
    if not base:
        return extra if extra else {}
    if not extra:
        return base
    
    # Extract operators and conditions
    base_op = _get_operator(base)
    extra_op = _get_operator(extra)
    base_conditions = _get_conditions(base, base_op)
    extra_conditions = _get_conditions(extra, extra_op)
    
    # Merge logic
    if base_op == extra_op:
        # Operator sama: gabungkan conditions
        merged_conditions = base_conditions + extra_conditions
        return {base_op: merged_conditions}
    
    elif base_op == "and" and extra_op == "or":
        # base=AND, extra=OR: wrap dengan AND
        return {"and": base_conditions + [{"or": extra_conditions}]}
    
    elif base_op == "or" and extra_op == "and":
        # base=OR, extra=AND: wrap dengan AND
        return {"and": [{"or": base_conditions}] + extra_conditions}
    
    else:
        # Single conditions atau mixed: gunakan default operator
        return {default_operator: base_conditions + extra_conditions}


def _get_operator(criteria: dict) -> str:
    """Extract operator dari criteria dict"""
    if "and" in criteria:
        return "and"
    elif "or" in criteria:
        return "or"
    else:
        return "condition"  # Single condition


def _get_conditions(criteria: dict, operator: str) -> list:
    """Extract list kondisi dari criteria dict"""
    if operator in ["and", "or"]:
        conditions = criteria[operator]
        return conditions if isinstance(conditions, list) else [conditions]
    else:
        return [criteria]  # Single condition

    
def merge_criteria_advanced(base: dict, extra: dict, 
                          default_operator: str = "and",
                          optimize: bool = True) -> dict:
    """
    Version advanced dengan optimasi dan validasi.
    
    Args:
        base: Dict criteria pertama
        extra: Dict criteria kedua
        default_operator: Operator default  
        optimize: Apakah melakukan optimasi hasil
    
    Returns:
        Dict hasil merge yang sudah dioptimasi
    """
    if not _validate_criteria(base) or not _validate_criteria(extra):
        raise ValueError("Invalid criteria format")
    
    result = merge_criteria(base, extra, default_operator)
    
    if optimize:
        result = _optimize_criteria(result)
    
    return result


def _validate_criteria(criteria: dict) -> bool:
    """Validasi format criteria dict untuk Odoo domain"""
    if not criteria:
        return True
    
    operators = ["and", "or"]
    found_operators = [op for op in operators if op in criteria]
    
    # Maksimal 1 operator per dict
    if len(found_operators) > 1:
        return False
    
    # Validasi format domain conditions
    for op in found_operators:
        conditions = criteria[op]
        if not isinstance(conditions, list):
            return False
        
        # Setiap condition harus berupa list dengan 3 elements atau dict
        for condition in conditions:
            if isinstance(condition, list):
                if len(condition) != 3:
                    return False
            elif not isinstance(condition, dict):
                return False
    
    return True


def _optimize_criteria(criteria: dict) -> dict:
    """Optimasi criteria untuk mengurangi redundancy"""
    if not criteria:
        return criteria
    
    for op in ["and", "or"]:
        if op in criteria:
            conditions = criteria[op]
            
            # Flatten nested same operators
            flattened = []
            for condition in conditions:
                if isinstance(condition, dict) and op in condition:
                    flattened.extend(condition[op])
                else:
                    flattened.append(condition)
            
            # Remove duplicate domain conditions
            unique_conditions = _remove_duplicate_conditions(flattened)
            
            # Jika hanya 1 kondisi dan itu dict, return dict tersebut
            if len(unique_conditions) == 1 and isinstance(unique_conditions[0], dict):
                return unique_conditions[0]
            
            return {op: unique_conditions}
    
    return criteria


def _remove_duplicate_conditions(conditions: list) -> list:
    """Remove duplicate domain conditions"""
    unique = []
    seen = set()
    
    for condition in conditions:
        if isinstance(condition, list):
            # Convert list to tuple untuk bisa di-hash
            condition_key = tuple(condition)
            if condition_key not in seen:
                seen.add(condition_key)
                unique.append(condition)
        else:
            # Untuk dict, convert ke string representation
            condition_str = str(sorted(condition.items()))
            if condition_str not in seen:
                seen.add(condition_str)
                unique.append(condition)
    
    return unique


def add_condition(criteria: dict, field: str, operator: str, value, 
                 logic_operator: str = "and") -> dict:
    """
    Helper function untuk menambah single condition ke criteria.
    
    Args:
        criteria: Dict criteria existing
        field: Field name
        operator: Operator (=, !=, ilike, etc.)
        value: Value untuk comparison
        logic_operator: Logic operator untuk menggabungkan ("and" atau "or")
    
    Returns:
        Dict criteria yang sudah ditambah condition
    """
    new_condition = [field, operator, value]
    new_criteria = {logic_operator: [new_condition]}
    
    return merge_criteria_advanced(criteria, new_criteria)


def print_criteria_readable(criteria: dict, indent: int = 0) -> None:
    """Print criteria dalam format yang mudah dibaca"""
    prefix = "  " * indent
    
    if "and" in criteria:
        print(f"{prefix}AND:")
        for condition in criteria["and"]:
            if isinstance(condition, dict):
                print_criteria_readable(condition, indent + 1)
            else:
                print(f"{prefix}  - {condition}")
    
    elif "or" in criteria:
        print(f"{prefix}OR:")
        for condition in criteria["or"]:
            if isinstance(condition, dict):
                print_criteria_readable(condition, indent + 1)
            else:
                print(f"{prefix}  - {condition}")
    
    else:
        print(f"{prefix}CONDITION: {criteria}")
