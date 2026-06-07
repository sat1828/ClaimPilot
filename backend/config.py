from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    app_env: str = "development"
    secret_key: str = "change-this-to-a-random-secret-key"
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql+asyncpg://claimpilot:claimpilot@postgres:5432/claimpilot"
    database_sync_url: str = "postgresql://claimpilot:claimpilot@postgres:5432/claimpilot"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Anthropic
    anthropic_api_key: Optional[str] = None

    # OpenAI
    openai_api_key: Optional[str] = None

    # Pinecone
    pinecone_api_key: Optional[str] = None
    pinecone_index_name: str = "claimpilot-policies"
    pinecone_environment: str = "us-east-1-aws"

    # Tavily
    tavily_api_key: Optional[str] = None

    # OpenWeatherMap
    openweathermap_api_key: Optional[str] = None

    # Google Maps
    google_maps_api_key: Optional[str] = None

    # SMTP
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    claim_inbox_email: str = "claims@claimpilot.local"

    # Model config
    claude_model: str = "claude-sonnet-4-20250514"
    whisper_model: str = "whisper-1"
    embedding_model: str = "text-embedding-3-large"

    # Pipeline
    max_agent_retries: int = 3
    fraud_escalation_threshold: float = 0.3
    low_confidence_threshold: float = 0.6
    auto_escalate_threshold: float = 0.4
    default_fraud_risk: float = 0.5

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
