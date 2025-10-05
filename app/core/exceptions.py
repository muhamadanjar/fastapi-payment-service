from typing import Optional, Dict, Any, Union
from starlette.status import HTTP_400_BAD_REQUEST


class AppException(Exception):
    def __init__(self, message: str, 
                error_code: Optional[str] = None,
                 status_code: int = HTTP_400_BAD_REQUEST, 
                 details: Optional[Dict[str, Any]] = None,):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"{self.status_code}: {self.message}"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message='{self.message}', status_code={self.status_code})"

class DatabaseError(AppException):
    """Base exception for database errors"""
    pass