from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Powered Data Intelligence Platform"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # JWT & Security
    SECRET_KEY: str = "dev_supersecretkey_change_in_production_at_least_32_characters_long_123456"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "data_intelligence_db"
    DATABASE_URL: str = ""

    # AI & LLM Provider Configuration
    AI_PROVIDER: str = "gemini"  # "gemini", "groq", or "mock"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # AI Planning Limits
    AI_PLANNING_MAX_RETRIES: int = 2
    AI_PLANNING_TIMEOUT_SECONDS: int = 60
    AI_PLANNING_MAX_QUERIES: int = 15
    AI_PLANNING_MAX_FIELDS: int = 40
    AI_PLANNING_MAX_RECORDS: int = 10000

    # Phase 3: Search & Extraction Services
    TAVILY_API_KEY: str = ""
    FIRECRAWL_API_KEY: str = ""

    # Phase 3: Redis & Celery Background Processing
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Phase 3: Collection Engine Limits
    COLLECTION_MAX_QUERIES: int = 15
    COLLECTION_MAX_RESULTS_PER_QUERY: int = 10
    COLLECTION_MAX_SOURCES_PER_JOB: int = 100
    COLLECTION_MAX_RECORDS_PER_JOB: int = 1000
    COLLECTION_MAX_RETRIES: int = 3
    COLLECTION_CONCURRENCY: int = 3
    COLLECTION_REQUEST_TIMEOUT_SECONDS: int = 60
    COLLECTION_MAX_CONTENT_LENGTH: int = 50000

    # Phase 4: Dataset Processing & Export Storage
    DATASET_MAX_RECORDS_FOR_SYNC: int = 5000
    DATASET_PROFILE_BATCH_SIZE: int = 1000
    DATASET_EXPORT_MAX_RECORDS: int = 100000
    DATASET_EXPORT_MAX_FILE_SIZE_MB: int = 100
    DATASET_VERSIONING_ENABLED: bool = True
    EXPORT_STORAGE_DIR: str = "./storage/exports"
    EXPORT_FILE_RETENTION_HOURS: int = 24

    # CORS
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    def get_database_url(self) -> str:
        url = self.DATABASE_URL
        if not url:
            return (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )

        # Normalize and sanitize URL
        import urllib.parse
        clean_url = url.strip().strip("'\"")
        parsed = urllib.parse.urlsplit(clean_url)
        scheme = parsed.scheme.lower()

        # Convert standard postgres schemes to asyncpg
        if scheme in ("postgres", "postgresql"):
            new_scheme = "postgresql+asyncpg"
        elif scheme in ("postgresql+psycopg", "postgresql+psycopg2"):
            new_scheme = "postgresql+asyncpg"
        elif scheme == "sqlite":
            new_scheme = "sqlite+aiosqlite"
        else:
            new_scheme = scheme

        # Strip unsupported asyncpg query params (such as sslmode or channel_binding)
        # asyncpg handles SSL via connection arguments (e.g., connect_args={"ssl": "require"})
        query_params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        query_params.pop("sslmode", None)
        query_params.pop("channel_binding", None)

        new_query = urllib.parse.urlencode(query_params, doseq=True) if query_params else ""
        return urllib.parse.urlunsplit((new_scheme, parsed.netloc, parsed.path, new_query, parsed.fragment))

    def get_sync_database_url(self) -> str:
        async_url = self.get_database_url()
        import urllib.parse
        parsed = urllib.parse.urlsplit(async_url)
        scheme = parsed.scheme.lower()

        if "+asyncpg" in scheme:
            new_scheme = scheme.replace("+asyncpg", "")
        elif "+aiosqlite" in scheme:
            new_scheme = scheme.replace("+aiosqlite", "")
        elif scheme == "postgres":
            new_scheme = "postgresql"
        else:
            new_scheme = scheme

        return urllib.parse.urlunsplit((new_scheme, parsed.netloc, parsed.path, parsed.query, parsed.fragment))

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )


settings = Settings()
