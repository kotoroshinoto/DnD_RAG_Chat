from data_management.data_models.dnd_pydantic_base.base_model import DnDAppBaseModel


class Persona(DnDAppBaseModel):
    name: str
    default_model: str
    system_prompt: str
