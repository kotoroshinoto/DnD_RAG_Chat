from sqlite3 import IntegrityError
from typing import List

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app_db.decl_base import DeclarativeBaseDnDAppDB
from llm_common.persona import PersonaTable, Persona
from log.logger import logger


class AppDataDB:
    def __init__(self):
        self._engine = create_engine('sqlite:///dnd_rag_data.db', echo=True)
        self._session_mkr = sessionmaker(bind=self._engine)
        self._session = self._session_mkr()
        DeclarativeBaseDnDAppDB.metadata.create_all(self._engine)
    
    @property
    def engine(self):
        return self._engine
    
    @property
    def session(self):
        return self._session
    
    @property
    def session_mkr(self):
        return self._session_mkr
    
    def contains_persona(self, name: str) -> bool:
        result = self._session.query(PersonaTable).filter_by(name=name).all()
        return len(result) > 0
    
    def fetch_persona(self, name: str) -> Persona:
        result = self._session.query(PersonaTable).filter_by(name=name).first()
        return Persona.model_validate(result)
    
    def get_personas(self) -> List[Persona]:
        all_personas = self._session.query(PersonaTable).all()
        return [Persona.model_validate(persona) for persona in all_personas]
    
    def upsert_persona(self, persona_data: Persona):
        try:
            # Check if persona exists by name
            existing_persona = self.session.query(PersonaTable).filter_by(
                name=persona_data.name).first()
            
            if existing_persona:
                # Update the existing persona
                logger.info(f"Persona '{persona_data.name}' exists, updating.")
                existing_persona.default_model = persona_data.default_model
                existing_persona.system_prompt = persona_data.system_prompt
            else:
                # Add a new persona
                logger.info(f"Persona '{persona_data.name}' does not exist, adding.")
                persona_db = PersonaTable(name=persona_data.name,
                        default_model=persona_data.default_model,
                        system_prompt=persona_data.system_prompt)
                self.session.add(persona_db)
            
            # Commit changes
            self.session.commit()
            logger.info(f"Persona '{persona_data.name}' upserted successfully!")
        
        except IntegrityError as e:
            self.session.rollback()
            logger.error(f"Error during database operation: {e}")
            raise
