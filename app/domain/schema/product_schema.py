
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ProductResponse(BaseModel):
    """Schema for quality rule response."""
    id: str
    application_id: str
    category_id: str
    product_code: str
    description: str
    price: str
    is_active: bool
    created_at: datetime
