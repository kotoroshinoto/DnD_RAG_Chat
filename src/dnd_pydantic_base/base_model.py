from pydantic import BaseModel, ConfigDict


class DnDAppBaseModel(BaseModel):
    model_config = ConfigDict(
            arbitrary_types_allowed=True,
            from_attributes=True,
    )
