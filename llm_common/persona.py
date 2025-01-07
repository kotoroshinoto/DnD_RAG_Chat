from pydantic import BaseModel
from sqlalchemy import Column, String

from app_db.decl_base import DeclarativeBaseDnDAppDB


# SQLAlchemy setup
class PersonaTable(DeclarativeBaseDnDAppDB):
    __tablename__ = 'personas'

    name = Column(String, nullable=False, primary_key=True)
    default_model = Column(String, nullable=False)
    system_prompt = Column(String, nullable=False)

    def __repr__(self):
        return f"<Persona(name={self.name}, default_model={self.default_model}, system_prompt={self.system_prompt})>"
    

class Persona(BaseModel):
    class Config:
        arbitrary_types_allowed = True
        from_attributes = True
    name: str
    default_model: str
    system_prompt: str


