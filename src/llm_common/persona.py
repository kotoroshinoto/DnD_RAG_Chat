from sqlalchemy import Column, String
from dnd_pydantic_base.base_model import DnDAppBaseModel


class Persona(DnDAppBaseModel):
    class Config:
        arbitrary_types_allowed = True
        from_attributes = True
    name: str
    default_model: str
    system_prompt: str
