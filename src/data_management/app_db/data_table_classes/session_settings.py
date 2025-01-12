from sqlalchemy import Column, String

from data_management.app_db.decl_base import DeclarativeBaseDnDAppDB
from data_management.data_models.helper_classes.uuid_type import UUIDType


class SessionSettingsTable(DeclarativeBaseDnDAppDB):
    __tablename__ = 'session_settings.py'

    session_id = Column(UUIDType, nullable=False, primary_key=True)
    selected_persona_name = Column(String, nullable=True)
    custom_mode_model = Column(String, nullable=False)
    custom_mode_system_prompt = Column(String, nullable=False)

    def __repr__(self):
        parts = [f'{x.name}={getattr(self, x.name)}' for x in self.__table__.columns]
        return f"<SessionSettings({', '.join(parts)})>"
