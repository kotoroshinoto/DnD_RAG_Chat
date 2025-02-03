import datetime
import uuid

from pydantic import Field, UUID4


from data_management.data_models.dnd_pydantic_base.base_model import DnDAppBaseModel
from beartype.typing import Set, Dict, List, Optional, Tuple, Union, Sequence, Any, Generic, Generator, AsyncGenerator, TypeVar, Type, TypeIs
from beartype import beartype


class Document(DnDAppBaseModel):
    id: UUID4 = Field(default_factory=uuid.uuid4)