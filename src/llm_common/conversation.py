import datetime
import uuid

from sqlalchemy import Column, DateTime, String

from app_db.decl_base import DeclarativeBaseDnDAppDB
from dnd_pydantic_base.base_model import DnDAppBaseModel
from llm_common.uuid_type import UUIDType


class Conversation(DnDAppBaseModel):
    session_id: uuid.UUID
    persona_name: str
    message_time: datetime.datetime
    conversation_sender: str
    conversation_content: str


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
