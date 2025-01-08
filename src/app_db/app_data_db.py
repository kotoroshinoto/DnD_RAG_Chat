""""""
import uuid
from sqlite3 import IntegrityError
from typing import List

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app_db.decl_base import DeclarativeBaseDnDAppDB
from llm_common.persona import Persona, PersonaTable
from llm_common.conversation import Conversation, ConversationTable
from log.logger import logger


class AppDataDB:
    """"""
    def __init__(self):
        """"""
        self._engine = create_engine('sqlite:///dnd_rag_data.db', echo=True)
        self._session_mkr = sessionmaker(bind=self._engine)
        self._session = self._session_mkr()
        DeclarativeBaseDnDAppDB.metadata.create_all(self._engine)

    @property
    def engine(self):
        """"""
        return self._engine

    @property
    def session(self):
        """"""
        return self._session

    @property
    def session_mkr(self):
        """"""
        return self._session_mkr

    def contains_persona(self, name: str) -> bool:
        """"""
        result = self._session.query(PersonaTable).filter_by(name=name).all()
        return len(result) > 0

    def fetch_persona(self, name: str) -> Persona:
        """"""
        result = self._session.query(PersonaTable).filter_by(name=name).first()
        return Persona.model_validate(result)

    def get_personas(self) -> List[Persona]:
        """"""
        all_personas = self._session.query(PersonaTable).all()
        return [Persona.model_validate(persona) for persona in all_personas]

    def upsert_persona(self, persona_data: Persona):
        """"""
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
                persona_db = PersonaTable(
                    name=persona_data.name,
                    default_model=persona_data.default_model,
                    system_prompt=persona_data.system_prompt
                )
                self.session.add(persona_db)

            # Commit changes
            self.session.commit()
            logger.info(f"Persona '{persona_data.name}' upserted successfully!")

        except IntegrityError as e:
            self.session.rollback()
            logger.error(f"Error during database operation: {e}")
            # raise e

    def get_conversation_history(
        self,
        session_id: uuid.UUID,
        persona_name: str
    ) -> List[Conversation]:
        """"""
        result = self.session.query(ConversationTable).filter_by(
            session_id=session_id,
            persona_name=persona_name
        ).order_by(ConversationTable.message_time.asc()).all()
        return [
            Conversation.model_validate(x) for x in result
        ]

    def get_conversation_entry(
        self,
        session_id: uuid.UUID,
        persona_name: str,
        message_time: str,
        conversation_sender: str
    ) -> Conversation:
        """"""
        result = self.session.query(ConversationTable).filter_by(
            session_id=session_id,
            persona_name=persona_name,
            message_time=message_time,
            conversation_sender=conversation_sender
        ).first()
        return Conversation.model_validate(result)

    def upsert_conversation_entry(self, conversation: Conversation):
        """"""
        try:
            existing_conversation = self.session.query(ConversationTable).filter_by(
                session_id=conversation.session_id,
                persona_name=conversation.persona_name,
                message_time=conversation.message_time,
                conversation_sender=conversation.conversation_sender,
            ).all()

            if existing_conversation:
                logger.info(f"Conversation '{conversation}' exists, updating.")
                existing_conversation.conversation_content = conversation.conversation_content
            else:
                logger.info(f"Conversation '{conversation}' does not exist, creating.")
                conversation_db = ConversationTable(
                    session_id=conversation.session_id,
                    persona_name=conversation.persona_name,
                    message_time=conversation.message_time,
                    conversation_sender=conversation.conversation_sender,
                    conversation_content=conversation.conversation_content,
                )
                self.session.add(conversation_db)

            self.session.commit()
            logger.info(f"Conversation '{conversation}' upserted successfully!")
        except IntegrityError as e:
            self.session.rollback()
            logger.error(f"Error during database operation: {e}")
            # raise e

app_db = AppDataDB()
