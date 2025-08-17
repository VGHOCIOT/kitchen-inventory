from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    DATABASE_URL: str
    ECHO_SQL: bool = Field(False, env='SQLALCHEMY_ECHO')
    
    class Config:
        env_file = ".env"

settings = Settings()