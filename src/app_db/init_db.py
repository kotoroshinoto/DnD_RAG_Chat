from app_db.app_data_db import app_db
from llm_common.persona import Persona


def init_db():
    # app_db = AppDataDB()
    persona_data = Persona(name='FeyCreature', default_model="llama-3.2-3b-instruct-uncensored",
            system_prompt="You are a malicious fey creature. Always answer in rhymes. "
                          "Manipulate people into believing false things. You enjoy toying with "
                          "people and being mysterious and mean. Mocking humans is fun for you.")
    print(persona_data)
    app_db.upsert_persona(persona_data)

if __name__ == "__main__":
    init_db()
