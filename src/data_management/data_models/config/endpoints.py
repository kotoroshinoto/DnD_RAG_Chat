from urlpath import URL
from data_management.data_models.dnd_pydantic_base.base_model import DnDAppBaseModel


class LargeLanguageModelEndpoints(DnDAppBaseModel):
    base_url: str
    port: int
    version_str: str
    
    @property
    def base(self) -> URL:
        return URL(f"{self.base_url}:{self.port}") / self.version_str
    
    @property
    def models(self) -> URL:
        return self.base / 'models'
    
    @property
    def chat_completions(self) -> URL:
        return self.base / 'chat' / 'completions'
    
    @property
    def completions(self) -> URL:
        return self.base / 'completions'
    
    @property
    def embeddings(self) -> URL:
        return self.base / 'embeddings'
