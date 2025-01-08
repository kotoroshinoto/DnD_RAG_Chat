from sqlalchemy import Column, String

from app_db.decl_base import DeclarativeBaseDnDAppDB
from dnd_pydantic_base.base_model import DnDAppBaseModel


class Persona(DnDAppBaseModel):
    name: str
    default_model: str
    system_prompt: str


class PersonaTable(DeclarativeBaseDnDAppDB):
    __tablename__ = 'personas'

    name = Column(String, nullable=False, primary_key=True)
    default_model = Column(String, nullable=False)
    system_prompt = Column(String, nullable=False)

    def __repr__(self):
        parts = [f'{x.name}={getattr(self, x.name)}' for x in self.__table__.columns]
        return f"<Persona({', '.join(parts)})>"
