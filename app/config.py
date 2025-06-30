"""
Configuration management for the Grafana to Kibana converter
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings

# Explicitly load .env file early
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
except ImportError:
    pass  # If python-dotenv is not installed, rely on pydantic-settings or os.environ


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # LLM Configuration
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_ai_api_key: Optional[str] = None
    
    # LLM Settings
    llm_provider: str = "openai"  # openai, anthropic, google
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4000
    
    # Application Settings
    environment: str = "development"
    log_level: str = "info"
    debug: bool = False
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # File Storage
    upload_dir: str = "uploads"
    download_dir: str = "downloads"
    max_file_size: int = 10485760  # 10MB
    
    # Security
    secret_key: Optional[str] = None
    cors_origins: Optional[str] = None
    
    # Database (for future use)
    database_url: Optional[str] = None
    redis_url: Optional[str] = None
    
    # LLM Features
    enable_llm_conversion: bool = False
    enable_smart_query_translation: bool = False
    enable_intelligent_mapping: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
print(f"[DEBUG] OPENAI_API_KEY loaded: {settings.openai_api_key}")
print(f"[DEBUG] LLM_MODEL loaded: {settings.llm_model!r}")


def get_llm_config():
    """Get LLM configuration based on provider"""
    if not settings.enable_llm_conversion:
        return None
    
    config = {
        "provider": settings.llm_provider,
        "model": settings.llm_model,
        "temperature": settings.llm_temperature,
        "max_tokens": settings.llm_max_tokens,
    }
    
    if settings.llm_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when using OpenAI")
        config["api_key"] = settings.openai_api_key
    elif settings.llm_provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when using Anthropic")
        config["api_key"] = settings.anthropic_api_key
    elif settings.llm_provider == "google":
        if not settings.google_ai_api_key:
            raise ValueError("GOOGLE_AI_API_KEY is required when using Google AI")
        config["api_key"] = settings.google_ai_api_key
    else:
        raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
    
    return config


def is_llm_enabled():
    """Check if LLM features are enabled"""
    return settings.enable_llm_conversion and any([
        settings.openai_api_key,
        settings.anthropic_api_key,
        settings.google_ai_api_key
    ]) 