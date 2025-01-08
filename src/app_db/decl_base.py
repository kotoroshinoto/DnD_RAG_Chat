from typing import Optional
from typing import Any, Type
import uuid

from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy import Column, Dialect, String, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy import MetaData


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


MetadataDnDAppDB = MetaData()
DeclarativeBaseDnDAppDB = declarative_base(metadata=MetadataDnDAppDB)

# SQLAlchemy setup
class PersonaTable(DeclarativeBaseDnDAppDB):
    __tablename__ = 'personas'

    name = Column(String, nullable=False, primary_key=True)
    default_model = Column(String, nullable=False)
    system_prompt = Column(String, nullable=False)

    def __repr__(self):
        return f"<Persona(name={self.name}, default_model={self.default_model}, system_prompt={self.system_prompt})>"


# SQLAlchemy setup
class ConversationTable(DeclarativeBaseDnDAppDB):
    __tablename__ = 'conversations'
    
    session_id = Column(UUIDType, nullable=False, primary_key=True)
    persona_name = Column(String, nullable=False, primary_key=True)
    message_time = Column(DateTime, nullable=False, primary_key=True)
    conversation_sender = Column(String, nullable=False, primary_key=True)
    conversation_content = Column(String, nullable=False)
    
    def __repr__(self):
        parts = [f'{x.name}={getattr(self, x.name)}' for x in self.__table__.columns]
        return f"<Conversation({', '.join(parts)})>"

__all__ = [
    'DeclarativeBaseDnDAppDB',
    'PersonaTable',
    'ConversationTable'
]
