"""Configuration management for Astarion."""

from functools import lru_cache
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Application settings
    app_name: str = Field("Astarion", description="Application name")
    app_version: str = Field("0.1.0", description="Application version")
    debug: bool = Field(False, description="Debug mode")
    log_level: str = Field("INFO", description="Logging level")
    
    # API settings
    api_host: str = Field("0.0.0.0", description="API host")
    api_port: int = Field(8000, description="API port")
    api_prefix: str = Field("/api/v1", description="API prefix")
    
    # LLM settings
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API key")
    default_llm_provider: str = Field("openai", description="Default LLM provider")
    default_llm_model: str = Field("gpt-4", description="Default LLM model")
    llm_temperature: float = Field(0.7, ge=0.0, le=2.0, description="LLM temperature")
    llm_max_tokens: int = Field(2000, ge=1, description="Max tokens for LLM response")
    
    # Database settings
    database_url: str = Field(
        "postgresql+asyncpg://astarion:astarion@localhost:5432/astarion",
        description="Database connection URL"
    )
    database_echo: bool = Field(False, description="Echo SQL queries")
    
    # Redis settings
    redis_url: str = Field("redis://localhost:6379/0", description="Redis connection URL")
    cache_ttl: int = Field(3600, description="Default cache TTL in seconds")
    
    # Qdrant settings
    qdrant_url: str = Field("http://localhost:6333", description="Qdrant URL")
    qdrant_api_key: Optional[str] = Field(None, description="Qdrant API key")
    qdrant_collection_name: str = Field("astarion_rules", description="Qdrant collection name")
    embedding_model: str = Field("BAAI/bge-small-en-v1.5", description="Embedding model")
    embedding_dimension: int = Field(384, description="Embedding dimension")
    
    # RAG settings
    chunk_size: int = Field(1000, description="Text chunk size for RAG")
    chunk_overlap: int = Field(200, description="Chunk overlap for RAG")
    retrieval_top_k: int = Field(5, description="Number of documents to retrieve")
    
    # MCP settings
    mcp_server_timeout: int = Field(30, description="MCP server timeout in seconds")
    mcp_max_retries: int = Field(3, description="Max retries for MCP calls")
    
    # Validation settings
    strict_mode: bool = Field(True, description="Strict validation mode")
    allow_homebrew: bool = Field(False, description="Allow homebrew content")
    max_validation_time: int = Field(60, description="Max validation time in seconds")
    
    # Security settings
    secret_key: str = Field("change-me-in-production", description="Secret key for JWT")
    access_token_expire_minutes: int = Field(30, description="Access token expiration")
    
    @field_validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {valid_levels}")
        return v.upper()
    
    @field_validator("default_llm_provider")
    def validate_llm_provider(cls, v: str) -> str:
        """Validate LLM provider."""
        valid_providers = ["openai", "anthropic", "local"]
        if v not in valid_providers:
            raise ValueError(f"Invalid LLM provider. Must be one of: {valid_providers}")
        return v
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration based on provider."""
        if self.default_llm_provider == "openai":
            if not self.openai_api_key:
                raise ValueError("OpenAI API key not set")
            return {
                "api_key": self.openai_api_key,
                "model": self.default_llm_model,
                "temperature": self.llm_temperature,
                "max_tokens": self.llm_max_tokens,
            }
        elif self.default_llm_provider == "anthropic":
            if not self.anthropic_api_key:
                raise ValueError("Anthropic API key not set")
            return {
                "api_key": self.anthropic_api_key,
                "model": self.default_llm_model,
                "temperature": self.llm_temperature,
                "max_tokens": self.llm_max_tokens,
            }
        else:
            # Local LLM configuration
            return {
                "model": self.default_llm_model,
                "temperature": self.llm_temperature,
                "max_tokens": self.llm_max_tokens,
            }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings() 