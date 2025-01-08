import datetime
import uuid

from dnd_pydantic_base.base_model import DnDAppBaseModel


class Conversation(DnDAppBaseModel):
    class Config:
        arbitrary_types_allowed = True
        from_attributes = True
    
    session_id: uuid.UUID
    persona_name: str
    message_time: datetime.datetime
    conversation_sender: str
    conversation_content: str
