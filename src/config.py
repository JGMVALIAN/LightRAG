"""
Configuration management for Spanish Legal RAG System
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")
    openai_embedding_model: str = Field(default="text-embedding-3-large", env="OPENAI_EMBEDDING_MODEL")

    # Database Configuration
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_db: str = Field(default="legal_rag", env="POSTGRES_DB")
    postgres_user: str = Field(default="legal_rag_user", env="POSTGRES_USER")
    postgres_password: str = Field(..., env="POSTGRES_PASSWORD")

    # Neo4j Configuration
    neo4j_uri: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", env="NEO4J_USER")
    neo4j_password: str = Field(..., env="NEO4J_PASSWORD")

    # Milvus Configuration
    milvus_host: str = Field(default="localhost", env="MILVUS_HOST")
    milvus_port: int = Field(default=19530, env="MILVUS_PORT")

    # Redis Configuration
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: str = Field(..., env="REDIS_PASSWORD")
    redis_db: int = Field(default=0, env="REDIS_DB")

    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=4, env="API_WORKERS")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # LightRAG Configuration
    lightrag_working_dir: str = Field(default="./data/lightrag", env="LIGHTRAG_WORKING_DIR")
    chunk_token_size: int = Field(default=1200, env="CHUNK_TOKEN_SIZE")
    chunk_overlap_size: int = Field(default=100, env="CHUNK_OVERLAP_SIZE")
    max_async: int = Field(default=4, env="MAX_ASYNC")
    max_tokens: int = Field(default=32000, env="MAX_TOKENS")

    # Spanish Legal Corpus
    boe_base_url: str = Field(default="https://www.boe.es", env="BOE_BASE_URL")
    cendoj_base_url: str = Field(default="https://www.poderjudicial.es", env="CENDOJ_BASE_URL")

    # Monitoring
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    grafana_port: int = Field(default=3000, env="GRAFANA_PORT")
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")

    # Security (ENS Compliance)
    enable_audit_log: bool = Field(default=True, env="ENABLE_AUDIT_LOG")
    encryption_key_path: Optional[str] = Field(default=None, env="ENCRYPTION_KEY_PATH")
    hsm_enabled: bool = Field(default=False, env="HSM_ENABLED")
    hsm_pkcs11_lib: Optional[str] = Field(default=None, env="HSM_PKCS11_LIB")

    # Feature Flags
    enable_cache: bool = Field(default=True, env="ENABLE_CACHE")
    cache_ttl_seconds: int = Field(default=3600, env="CACHE_TTL_SECONDS")
    enable_legal_reasoning: bool = Field(default=True, env="ENABLE_LEGAL_REASONING")
    enable_citation_validation: bool = Field(default=True, env="ENABLE_CITATION_VALIDATION")
    enable_temporal_analysis: bool = Field(default=True, env="ENABLE_TEMPORAL_ANALYSIS")

    @property
    def postgres_url(self) -> str:
        """PostgreSQL connection URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def redis_url(self) -> str:
        """Redis connection URL"""
        return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
