from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core
    ENV: str = "dev"
    SECRET_KEY: str = "neuron-secret-key-12345"
    ACCESS_TTL_MIN: int = 15
    REFRESH_TTL_DAYS: int = 7
    CORS: Union[str, List[str]] = ["http://localhost:5173"]

    @field_validator("CORS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    # Postgres
    POSTGRES_USER: str = "neuron"
    POSTGRES_PASSWORD: str = "neuronpass"
    POSTGRES_DB: str = "neuron"
    DATABASE_URL: str = "postgresql+asyncpg://neuron:neuronpass@localhost:5432/neuron"

    # Neo4j
    NEO4J_AUTH: str = "neo4j/neuronpass"
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "neuronpass"

    # Qdrant / Redis / MinIO
    QDRANT_URL: str = "http://localhost:6333"
    REDIS_URL: str = "redis://localhost:6379/0"
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "neuron-iq"
    MINIO_SECURE: bool = False

    # LLM
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    LLM_PRIMARY: str = "gemini-2.0-flash"
    LLM_HEAVY: str = "gemini-2.0-pro"
    EMBED_MODEL: str = "text-embedding-3-large"


settings = Settings()
