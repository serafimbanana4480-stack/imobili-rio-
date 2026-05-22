"""Configuration management for Real Estate Opportunity Engine."""
import os
from dataclasses import dataclass, field
from typing import List, Optional
from dotenv import load_dotenv
from loguru import logger

load_dotenv()


@dataclass
class Config:
    """Application configuration loaded from environment variables."""
    
    # Telegram
    telegram_bot_token: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    telegram_chat_id: str = field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", ""))
    
    # Database (PostgreSQL is the supported production backend).
    # SQLite is accepted only as a local-dev fallback and must be opted-in
    # explicitly via DATABASE_URL=sqlite:///...; see .env.example.
    database_url: str = field(default_factory=lambda: os.getenv(
        "DATABASE_URL",
        "postgresql://realestate:realestate_secure_2026@localhost:5432/realestate",
    ))
    scheduler_db_url: str = field(default_factory=lambda: os.getenv(
        "SCHEDULER_DB_URL",
        "postgresql://realestate:realestate_secure_2026@localhost:5432/realestate",
    ))

    # Redis — required for cache, rate-limit and (future) queues.
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    redis_required: bool = field(default_factory=lambda: os.getenv("REDIS_REQUIRED", "false").lower() == "true")
    
    # Logging
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    
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
    
    # Scoring thresholds
    min_score_notification: float = 8.0
    max_daily_notifications: int = 50
    
    # Paths
    data_dir: str = "data"
    db_dir: str = "data/db"
    backup_dir: str = "data/backups"
    cache_dir: str = "data/cache"
    
    # Environment
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    
    # Feature flags
    enable_kafka_streaming: bool = field(default_factory=lambda: os.getenv("ENABLE_KAFKA", "false").lower() == "true")
    kafka_bootstrap_servers: str = field(default_factory=lambda: os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"))
    
    # Prometheus
    prometheus_port: int = field(default_factory=lambda: int(os.getenv("PROMETHEUS_PORT", "8000")))
    
    def __post_init__(self):
        """Ensure directories exist and validate configuration."""
        for d in [self.data_dir, self.db_dir, self.backup_dir, self.cache_dir]:
            os.makedirs(d, exist_ok=True)
        
        # Validate proxy configuration in production
        if self.environment == "production":
            if not self.residential_proxy_url and not self.proxy_list:
                raise RuntimeError(
                    "CRITICAL: Proxy must be configured in production. "
                    "Set RESIDENTIAL_PROXY_URL or PROXY_LIST environment variable."
                )
            logger.info(
                f"Production mode: Using {'residential proxy' if self.residential_proxy_url else 'proxy list'} "
                f"({len(self.proxy_list) if self.proxy_list else 0} proxies)"
            )
        else:
            # Warn in development if no proxy
            if not self.residential_proxy_url and not self.proxy_list:
                logger.warning(
                    "Development mode: No proxy configured. "
                    "Scraping will use real IP (acceptable for dev, NOT for production)"
                )


# Global config instance
config = Config()
