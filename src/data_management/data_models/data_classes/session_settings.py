import uuid
from typing import Optional

from data_management.data_models.dnd_pydantic_base.base_model import DnDAppBaseModel


class SessionSettings(DnDAppBaseModel):
    session_id: uuid.UUID
    selected_persona_name: Optional[str]
    custom_mode_model: str
    custom_mode_system_prompt: str
