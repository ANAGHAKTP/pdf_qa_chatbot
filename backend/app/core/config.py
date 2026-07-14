import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Project Info
    PROJECT_NAME: str = "DOCMind Enterprise"
    API_V1_STR: str = "/api/v1"

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "docmind"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""

    # Chroma
    CHROMADB_HOST: str = "localhost"
    CHROMADB_PORT: int = 8000

    # JWT Authentication
    JWT_SECRET: str = "428f526b1c54b2b6279bc90666bbdbf472851cf57cd8746b107bc5a4b7eb25ff"
    JWT_REFRESH_SECRET: str = "7f5df59929f64ebc3bfae68f3a3a5d898495fb2db4deca5ccbc6beea7cd46358"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # NVIDIA NIM API
    NVIDIA_API_KEY: str = ""
    LLM_MODEL: str = "meta/llama-3.1-8b-instruct"
    EMBEDDING_MODEL: str = "nvidia/nv-embedqa-e5-v5"
    RERANK_MODEL: str = "nvidia/reranking-nv-embed-rerank-large"

    # Storage
    USE_S3: bool = False
    UPLOAD_DIR: str = "./data/uploads"
    AWS_BUCKET_NAME: str = "docmind-enterprise-bucket"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://localhost:8000,http://localhost:3001"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)


settings = Settings()
