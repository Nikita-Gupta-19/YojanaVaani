from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "YojanaVaani Backend"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    
    # Database Settings
    POSTGRES_USER: str = "yojana"
    POSTGRES_PASSWORD: str = "yojana123"
    POSTGRES_SERVER: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "yojanavaani"
    DATABASE_URL: Optional[str] = None

    # External APIs and Services
    MYSCHEME_API_KEY: str = "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()
