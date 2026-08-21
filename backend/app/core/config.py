from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.local", ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Server Configuration
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://localhost:3000"]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() in ("development", "dev", "local")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    # LLM Provider
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.1-flash-lite"
    EMBEDDING_MODEL: str = "gemini-embedding-001"

    # Persistence URLs
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/portfolio_db"
    MONGO_URI: str = "mongodb://localhost:27017/portfolio_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"

    # Notification Webhooks
    DISCORD_WEBHOOK_URL: str = ""
    ADMIN_SECRET_KEY: str = "change_this_in_production"


settings = Settings()

