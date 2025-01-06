from urlpath import URL
from pydantic import BaseModel


class LargeLanguageModelEndpoints(BaseModel):
    base_url: str
    version_str: str
    
    class Config:
        arbitrary_types_allowed = True
    
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
