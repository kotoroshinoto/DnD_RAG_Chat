from sqlalchemy.orm import declarative_base
from sqlalchemy import MetaData

MetadataDnDAppDB = MetaData()
DeclarativeBaseDnDAppDB = declarative_base(metadata=MetadataDnDAppDB)

# SQLAlchemy setup


# SQLAlchemy setup

__all__ = [
    'DeclarativeBaseDnDAppDB'
]
