from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    PROJECT_NAME: str = Field(default="DSPy Prompt Engineer", description="Project name")
    DEBUG: bool = Field(default=False, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    API_V1_STR: str = Field(default="/api/v1", description="API version prefix")
    
    DATABASE_URL: str = Field(..., description="Async database URL")
    DATABASE_URL_SYNC: str = Field(..., description="Sync database URL")
    
    REDIS_URL: str = Field(..., description="Redis URL")
    
    MINIO_ENDPOINT: str = Field(..., description="MinIO endpoint")
    MINIO_ACCESS_KEY: str = Field(..., description="MinIO access key")
    MINIO_SECRET_KEY: str = Field(..., description="MinIO secret key")
    MINIO_BUCKET_NAME: str = Field(default="dspy-datasets", description="MinIO bucket name")
    MINIO_SECURE: bool = Field(default=False, description="Use HTTPS for MinIO")
    
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    OPENAI_MODEL: str = Field(default="gpt-4-turbo-preview", description="OpenAI model")
    
    SECRET_KEY: str = Field(..., description="Secret key for JWT")
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Token expiration minutes")
    
    CELERY_BROKER_URL: str = Field(..., description="Celery broker URL")
    CELERY_RESULT_BACKEND: str = Field(..., description="Celery result backend URL")
    
    DSPY_MAX_TRAIN_SIZE: int = Field(default=1000, description="Max training examples for DSPy")
    DSPY_MAX_DEV_SIZE: int = Field(default=200, description="Max dev examples for DSPy")
    DSPY_OPTIMIZATION_ROUNDS: int = Field(default=10, description="DSPy optimization rounds")
    
    MAX_FILE_SIZE_MB: int = Field(default=100, description="Max file size in MB")
    MAX_CONCURRENT_TASKS: int = Field(default=5, description="Max concurrent Celery tasks")
    
    @property
    def database_url_async(self) -> str:
        """Get async database URL."""
        return self.DATABASE_URL
    
    @property
    def database_url_sync(self) -> str:
        """Get sync database URL."""
        return self.DATABASE_URL_SYNC


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

