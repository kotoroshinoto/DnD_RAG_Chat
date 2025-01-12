import datetime
import uuid

from data_management.data_models.dnd_pydantic_base.base_model import DnDAppBaseModel


class Conversation(DnDAppBaseModel):
    session_id: uuid.UUID
    persona_name: str
    message_time: datetime.datetime
    conversation_sender: str
    conversation_content: str
