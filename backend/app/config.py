import os
from typing import Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env file from backend directory or project root
load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = "ProcureAI Backend"
    API_V1_STR: str = "/api"
    DEBUG: bool = True

    # Database Settings
    DB_USER: str = "root"
    DB_PASSWORD: str = "root"
    DB_HOST: str = "localhost"
    DB_PORT: str = "3306"
    DB_NAME: str = "procureai"
    DATABASE_URL: Optional[str] = None

    # AI Service Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"
    USE_MOCK_AI: bool = True

    @property
    def sync_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        # Default MySQL URL
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="allow",
    )


settings = Settings()

