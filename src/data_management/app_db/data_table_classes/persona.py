from sqlalchemy import Column, String

from data_management.app_db.decl_base import DeclarativeBaseDnDAppDB


class PersonaTable(DeclarativeBaseDnDAppDB):
    __tablename__ = 'personas'

    name = Column(String, nullable=False, primary_key=True)
    default_model = Column(String, nullable=False)
    system_prompt = Column(String, nullable=False)

    def __repr__(self):
        parts = [f'{x.name}={getattr(self, x.name)}' for x in self.__table__.columns]
        return f"<Persona({', '.join(parts)})>"
