from typing import Optional
from sqlalchemy import Column, String
import uuid

from app_db.decl_base import DeclarativeBaseDnDAppDB
from dnd_pydantic_base.base_model import DnDAppBaseModel
from llm_common.uuid_type import UUIDType


class SessionSettings(DnDAppBaseModel):
    session_id: uuid.UUID
    selected_persona_name: Optional[str]
    custom_mode_model: str
    custom_mode_system_prompt: str


class SessionSettingsTable(DeclarativeBaseDnDAppDB):
    __tablename__ = 'session_settings'

    session_id = Column(UUIDType, nullable=False, primary_key=True)
    selected_persona_name = Column(String, nullable=True)
    custom_mode_model = Column(String, nullable=False)
    custom_mode_system_prompt = Column(String, nullable=False)

    def __repr__(self):
        parts = [f'{x.name}={getattr(self, x.name)}' for x in self.__table__.columns]
        return f"<SessionSettings({', '.join(parts)})>"
