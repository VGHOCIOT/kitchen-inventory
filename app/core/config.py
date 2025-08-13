from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://admin:secret@db:5432/inventory"
    echo_sql: bool = Field(False, env='SQLALCHEMY_ECHO')
    
    class Config:
        env_file = ".env"

settings = Settings()