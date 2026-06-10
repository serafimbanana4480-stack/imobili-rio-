"""Configuration management for Real Estate Opportunity Engine."""
import os
from dataclasses import dataclass, field
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Application configuration loaded from environment variables."""
    
    environment: str = field(default_factory=lambda: os.getenv("APP_ENV", "development").lower())
    
    # Telegram
    telegram_bot_token: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    telegram_chat_id: str = field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", ""))
    
    # Database (PostgreSQL is the supported production backend).
    # SQLite is accepted only as a local-dev fallback and must be opted-in
    # explicitly via DATABASE_URL=sqlite:///...; see .env.example.
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", ""))
    scheduler_db_url: str = field(default_factory=lambda: os.getenv("SCHEDULER_DB_URL", ""))

    # Redis — required for cache, rate-limit and (future) queues.
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    redis_required: bool = field(default_factory=lambda: os.getenv("REDIS_REQUIRED", "false").lower() == "true")
    cache_backend: str = field(default_factory=lambda: os.getenv("CACHE_BACKEND", "auto").lower())
    
    # Logging
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    json_logs: bool = field(default_factory=lambda: os.getenv("JSON_LOGS", "false").lower() == "true")
    log_retention_days: int = field(default_factory=lambda: int(os.getenv("LOG_RETENTION_DAYS", "30")))
    log_rotation_size: str = field(default_factory=lambda: os.getenv("LOG_ROTATION_SIZE", "50 MB"))
    
    # API binding
    api_bind_host: str = field(default_factory=lambda: os.getenv("API_BIND_HOST", "127.0.0.1"))
    api_auth_required: bool = field(default_factory=lambda: os.getenv("API_AUTH_REQUIRED", "false").lower() == "true")
    jwt_secret_key: str = field(default_factory=lambda: os.getenv("JWT_SECRET_KEY", ""))
    jwt_algorithm: str = field(default_factory=lambda: os.getenv("JWT_ALGORITHM", "HS256"))
    jwt_access_token_expire_minutes: int = field(default_factory=lambda: int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440")))
    api_cors_origins: List[str] = field(default_factory=lambda: [
        origin.strip() for origin in os.getenv(
            "API_CORS_ORIGINS",
            "http://localhost:8501,http://127.0.0.1:8501,http://localhost:3000,http://127.0.0.1:3000",
        ).split(",") if origin.strip()
    ])
    api_allow_credentials: bool = field(default_factory=lambda: os.getenv("API_ALLOW_CREDENTIALS", "true").lower() == "true")
    trusted_hosts: List[str] = field(default_factory=lambda: [
        host.strip() for host in os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1").split(",") if host.strip()
    ])
    
    # Scheduler Intervals
    scraping_interval_minutes: int = field(default_factory=lambda: int(os.getenv("SCRAPING_INTERVAL_MINUTES", "30")))
    etl_interval_minutes: int = field(default_factory=lambda: int(os.getenv("ETL_INTERVAL_MINUTES", "32")))
    valuation_interval_minutes: int = field(default_factory=lambda: int(os.getenv("VALUATION_INTERVAL_MINUTES", "35")))
    scoring_interval_minutes: int = field(default_factory=lambda: int(os.getenv("SCORING_INTERVAL_MINUTES", "38")))
    notification_interval_minutes: int = field(default_factory=lambda: int(os.getenv("NOTIFICATION_INTERVAL_MINUTES", "60")))
    
    # Proxies
    proxy_list: List[str] = field(default_factory=lambda: [
        p.strip() for p in os.getenv("PROXY_LIST", "").split(",") if p.strip()
    ])
    residential_proxy_url: str = field(default_factory=lambda: os.getenv("RESIDENTIAL_PROXY_URL", ""))
    
    # Scoring thresholds (configurable via env for tuning)
    min_score_notification: float = field(default_factory=lambda: float(os.getenv("MIN_SCORE_NOTIFICATION", "8.0")))
    max_daily_notifications: int = field(default_factory=lambda: int(os.getenv("MAX_DAILY_NOTIFICATIONS", "50")))
    
    # Red flag thresholds
    red_flag_price_m2_critical: float = field(default_factory=lambda: float(os.getenv("RED_FLAG_PRICE_M2_CRITICAL", "400")))
    red_flag_price_m2_warning: float = field(default_factory=lambda: float(os.getenv("RED_FLAG_PRICE_M2_WARNING", "700")))
    red_flag_overpriced_severe: float = field(default_factory=lambda: float(os.getenv("RED_FLAG_OVERPRICED_SEVERE", "-0.25")))
    red_flag_overpriced_moderate: float = field(default_factory=lambda: float(os.getenv("RED_FLAG_OVERPRICED_MODERATE", "-0.15")))
    
    # Scoring caps
    score_cap_no_photos: float = field(default_factory=lambda: float(os.getenv("SCORE_CAP_NO_PHOTOS", "5.0")))
    score_cap_no_coords: float = field(default_factory=lambda: float(os.getenv("SCORE_CAP_NO_COORDS", "7.2")))
    score_cap_with_flags: float = field(default_factory=lambda: float(os.getenv("SCORE_CAP_WITH_FLAGS", "8.0")))
    
    # Imperdível thresholds
    imperdivel_min_score: float = field(default_factory=lambda: float(os.getenv("IMPERDIVEL_MIN_SCORE", "9.0")))
    imperdivel_min_discount_pct: float = field(default_factory=lambda: float(os.getenv("IMPERDIVEL_MIN_DISCOUNT_PCT", "15.0")))
    
    # Paths
    data_dir: str = field(default_factory=lambda: os.getenv("DATA_DIR", "data"))
    db_dir: str = field(default_factory=lambda: os.getenv("DB_DIR", "data/db"))
    backup_dir: str = field(default_factory=lambda: os.getenv("BACKUP_DIR", "data/backups"))
    cache_dir: str = field(default_factory=lambda: os.getenv("CACHE_DIR", "data/cache"))
    
    # Feature flags
    enable_kafka_streaming: bool = field(default_factory=lambda: os.getenv("ENABLE_KAFKA", "false").lower() == "true")
    kafka_bootstrap_servers: str = field(default_factory=lambda: os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"))
    
    # Prometheus
    prometheus_port: int = field(default_factory=lambda: int(os.getenv("PROMETHEUS_PORT", "9090")))
    
    # Admin credentials (for simple built-in auth)
    admin_username: str = field(default_factory=lambda: os.getenv("ADMIN_USERNAME", ""))
    admin_password: str = field(default_factory=lambda: os.getenv("ADMIN_PASSWORD", ""))
    admin_password_hash: str = field(default_factory=lambda: os.getenv("ADMIN_PASSWORD_HASH", ""))
    
    @property
    def is_production(self) -> bool:
        """Return whether the application is running in production mode."""
        return self.environment in {"prod", "production"}
    
    def __post_init__(self):
        """Ensure directories exist and validate production settings."""
        for d in [self.data_dir, self.db_dir, self.backup_dir, self.cache_dir]:
            os.makedirs(d, exist_ok=True)
        if self.is_production and self.api_auth_required and not self.jwt_secret_key:
            raise RuntimeError("JWT_SECRET_KEY must be set when API_AUTH_REQUIRED=true in production")
        if self.is_production and self.api_auth_required and len(self.jwt_secret_key) < 32:
            raise RuntimeError("JWT_SECRET_KEY must be at least 32 characters in production")
        if self.is_production and "*" in self.api_cors_origins:
            raise RuntimeError("API_CORS_ORIGINS cannot contain '*' in production")
        if self.is_production and not self.database_url:
            raise RuntimeError("DATABASE_URL must be set in production")


# Global config instance
config = Config()
