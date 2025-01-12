from urlpath import URL
from data_management.data_models.dnd_pydantic_base.base_model import DnDAppBaseModel


class LargeLanguageModelEndpoints(DnDAppBaseModel):
    base_url: str
    version_str: str
    
    @property
    def base(self) -> URL:
        return URL(self.base_url) / self.version_str
    
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
