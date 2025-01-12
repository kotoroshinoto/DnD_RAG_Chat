import uuid
from typing import Any, Optional, Type

from sqlalchemy import CHAR, Dialect, TypeDecorator


class UUIDType(TypeDecorator):
    impl = CHAR(36)
    
    def process_bind_param(self, value: Optional[Any], dialect: Dialect) -> Optional[str]:
        if value is None:
            return None
        return str(value) if isinstance(value, uuid.UUID) else str(uuid.UUID(value))
    
    def process_result_value(self, value: Optional[str], dialect: Dialect) -> Optional[uuid.UUID]:
        if value is None:
            return None
        return uuid.UUID(value)
    
    def process_literal_param(self, value: Optional[uuid.UUID], dialect: Dialect) -> Optional[str]:
        if value is None:
            return None
        return str(value) if isinstance(value, uuid.UUID) else str(uuid.UUID(value))
    
    @property
    def python_type(self) -> Type[uuid.UUID]:
        return uuid.UUID
