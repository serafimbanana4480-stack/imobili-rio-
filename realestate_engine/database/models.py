"""SQLAlchemy models for Real Estate Opportunity Engine."""
import os
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    create_engine, Column, String, Float, Integer, Text, JSON, ForeignKey,
    DateTime, Index, event
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.pool import QueuePool, StaticPool

from realestate_engine.utils.config import config

UTC = timezone.utc

Base = declarative_base()


def generate_uuid() -> str:
    """Generate a unique identifier."""
    return str(uuid.uuid4())


class RawListing(Base):
    """Raw listing scraped from portals."""
    __tablename__ = "raw_listings"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    source_portal = Column(String, nullable=False)
    source_id = Column(String, nullable=False)
    source_url = Column(Text, nullable=False)
    scrape_timestamp = Column(String, nullable=False)
    raw_data = Column(JSON, nullable=False)
    is_sample = Column(Integer, default=0)  # 0 = real data, 1 = sample/fake data
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index("idx_raw_listings_source_portal", "source_portal"),
        Index("idx_raw_listings_scrape_timestamp", "scrape_timestamp"),
        Index("idx_raw_listings_source_id", "source_id"),
    )


class CleanListing(Base):
    """Clean, normalized listing after ETL."""
    __tablename__ = "clean_listings"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    source_portal = Column(String, nullable=False)
    source_id = Column(String, nullable=False)
    source_url = Column(Text, nullable=False)
    scrape_timestamp = Column(String, nullable=False)
    titulo = Column(Text)
    descricao = Column(Text)
    preco_pedido = Column(Float, nullable=False)
    area_util_m2 = Column(Float, nullable=False)
    area_bruta_m2 = Column(Float)
    quartos = Column(Integer, nullable=False)
    casas_banho = Column(Integer)
    morada_raw = Column(Text)
    morada = Column(Text)
    freguesia = Column(String)
    concelho = Column(String)
    distrito = Column(String)
    lat = Column(Float)
    lon = Column(Float)
    estado = Column(String)
    ano_construcao = Column(Integer)
    cert_energetico = Column(String)
    certificado_energetico = Column(String)
    tipologia = Column(String)
    fotos_urls = Column(JSON)
    fotos = Column(JSON)
    num_fotos = Column(Integer)
    agencia = Column(String)

    # Amenities (extracted by enricher.enrich_amenities)
    tem_garagem = Column(Integer)
    tem_piscina = Column(Integer)
    tem_vista_mar = Column(Integer)
    tem_vista_rio = Column(Integer)
    tem_elevador = Column(Integer)
    tem_terraco = Column(Integer)
    tem_jardim = Column(Integer)
    tem_ac = Column(Integer)
    andar = Column(Integer)

    # NEW: Additional amenities extracted from description
    cozinha_separada = Column(Integer)
    tem_maquina_lavar = Column(Integer)
    tem_maquina_louca = Column(Integer)
    tem_frigorifico = Column(Integer)
    tem_fogao = Column(Integer)
    tem_forno = Column(Integer)
    tem_estores_anti_roubo = Column(Integer)
    tem_monitorizacao = Column(Integer)
    tem_videoporteiro = Column(Integer)
    tem_internet = Column(Integer)
    tem_tv_cabo = Column(Integer)
    tem_telefone = Column(Integer)
    acessibilidade_mobilidade = Column(Integer)
    tem_aquecimento = Column(Integer)
    despesas_condominio = Column(Float)
    tipo_anunciante = Column(String)  # profissional vs particular

    preco_por_m2 = Column(Float)
    ine_preco_medio_m2 = Column(Float)
    ine_tendencia_mensal = Column(Float)
    dist_metro_m = Column(Float)
    dist_escola_m = Column(Float)
    dist_comercio_m = Column(Float)
    is_active = Column(Integer, default=1)  # 1 = active, 0 = inactive/dead
    is_duplicate = Column(Integer, default=0) # 1 = duplicate, 0 = unique
    duplicate_of_id = Column(String, ForeignKey("clean_listings.id"))
    is_sample = Column(Integer, default=0)  # 0 = real data, 1 = sample/fake data
    
    # Computer Vision features
    image_quality_score = Column(Float)
    image_blur_score = Column(Float)
    image_brightness_score = Column(Float)
    image_phash = Column(String(64))
    detected_rooms = Column(JSON)
    room_detection_confidence = Column(Float)
    cv_features = Column(JSON)
    
    # Advanced NLP features
    bert_sentiment_score = Column(Float)
    bert_sentiment_label = Column(String(20))
    extracted_entities = Column(JSON)
    description_summary = Column(Text)
    description_quality_bert_score = Column(Float)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    valuations = relationship("Valuation", back_populates="listing", cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="listing", cascade="all, delete-orphan")
    price_history = relationship("PriceHistory", back_populates="listing", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="listing", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_clean_listings_source_portal", "source_portal"),
        Index("idx_clean_listings_freguesia", "freguesia"),
        Index("idx_clean_listings_concelho", "concelho"),
        Index("idx_clean_listings_preco_area", "preco_pedido", "area_util_m2"),
        Index("idx_clean_listings_freguesia_quartos", "freguesia", "quartos"),
        Index("idx_clean_listings_tipologia_preco", "tipologia", "preco_pedido"),
        Index("idx_clean_listings_lat_lon", "lat", "lon"),
        Index("idx_clean_listings_scrape_portal", "scrape_timestamp", "source_portal"),
        Index("idx_clean_listings_preco", "preco_pedido"),
        Index("idx_clean_listings_preco_m2", "preco_por_m2"),
        Index("idx_clean_listings_area", "area_util_m2"),
        Index("idx_clean_listings_tipologia", "tipologia"),
        Index("idx_clean_listings_estado", "estado"),
        Index("idx_clean_listings_ano_construcao", "ano_construcao"),
        Index("idx_clean_listings_agencia", "agencia"),
        Index("idx_clean_listings_is_sample", "is_sample"),
        Index("idx_clean_listings_created_at", "created_at"),
        Index("idx_clean_listings_concelho_preco", "concelho", "preco_pedido"),
        Index("idx_clean_listings_freguesia_area", "freguesia", "area_util_m2"),
        Index("idx_clean_listings_portal_estado", "source_portal", "estado"),
        Index("idx_image_phash", "image_phash"),
        Index("idx_bert_sentiment", "bert_sentiment_score"),
        Index("idx_image_quality", "image_quality_score"),
    )


class Valuation(Base):
    """Valuation estimate for a listing."""
    __tablename__ = "valuations"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    listing_id = Column(String, ForeignKey("clean_listings.id", ondelete="CASCADE"), nullable=False)
    valor_justo = Column(Float)
    hedonic_value = Column(Float)
    comps_value = Column(Float)
    ine_value = Column(Float)
    xgboost_value = Column(Float)
    xgboost_explanation = Column(JSON)
    ci_lower = Column(Float)
    ci_upper = Column(Float)
    discount = Column(Float)
    confianca = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    listing = relationship("CleanListing", back_populates="valuations")
    
    __table_args__ = (
        Index("idx_valuations_listing_id", "listing_id"),
        Index("idx_valuations_valor_justo", "valor_justo"),
    )


class Score(Base):
    """Opportunity score for a listing."""
    __tablename__ = "scores"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    listing_id = Column(String, ForeignKey("clean_listings.id", ondelete="CASCADE"), nullable=False)
    score_total = Column(Float, nullable=False)
    score_discount = Column(Float)
    score_location = Column(Float)
    score_condition = Column(Float)
    score_amenities = Column(Float)
    score_liquidity = Column(Float)
    score_freshness = Column(Float)
    classificacao = Column(String)
    rationale = Column(Text)
    red_flags = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    listing = relationship("CleanListing", back_populates="scores")
    
    __table_args__ = (
        Index("idx_scores_listing_id", "listing_id"),
        Index("idx_scores_score_total", "score_total"),
    )


class PriceHistory(Base):
    """Price history for listings."""
    __tablename__ = "price_history"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    listing_id = Column(String, ForeignKey("clean_listings.id", ondelete="CASCADE"), nullable=False)
    preco = Column(Float, nullable=False)
    data = Column(String, nullable=False)
    source = Column(String)
    
    listing = relationship("CleanListing", back_populates="price_history")
    
    __table_args__ = (
        Index("idx_price_history_listing_id", "listing_id"),
        Index("idx_price_history_data", "data"),
    )


class Notification(Base):
    """Notification history."""
    __tablename__ = "notifications"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    listing_id = Column(String, ForeignKey("clean_listings.id", ondelete="CASCADE"), nullable=False)
    telegram_chat_id = Column(String)
    telegram_message_id = Column(String)
    message = Column(Text)
    sent_at = Column(DateTime)
    status = Column(String, default="pending")
    error_message = Column(Text)
    
    listing = relationship("CleanListing", back_populates="notifications")
    
    __table_args__ = (
        Index("idx_notifications_listing_id", "listing_id"),
        Index("idx_notifications_status", "status"),
    )


class GeocodingCache(Base):
    """Cache for geocoding results."""
    __tablename__ = "geocoding_cache"
    
    address_hash = Column(String, primary_key=True)
    address_raw = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    concelho = Column(String)
    freguesia = Column(String)
    precision = Column(String)
    provider = Column(String)
    cached_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class INEData(Base):
    """Historical INE data by region."""
    __tablename__ = "ine_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    concelho = Column(String, nullable=False)
    tipo_imovel = Column(String)
    ano = Column(Integer)
    trimestre = Column(Integer)
    preco_mediano_m2 = Column(Float)
    variacao_homologa_pct = Column(Float)
    num_transacoes = Column(Integer)
    fonte = Column(String, default="INE API")
    fetched_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index("idx_ine_data_concelho", "concelho"),
    )


class SystemMetrics(Base):
    """System performance metrics."""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float)
    metric_text = Column(Text)
    portal = Column(String)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ConfigEntry(Base):
    """System configuration entries."""
    __tablename__ = "config"
    
    key = Column(String, primary_key=True)
    value = Column(JSON)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class JobExecutionLog(Base):
    """Log of scheduled job executions."""
    __tablename__ = "job_execution_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_name = Column(String, nullable=False)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    finished_at = Column(DateTime)
    status = Column(String)
    error_message = Column(Text)
    records_processed = Column(Integer, default=0)
    
    __table_args__ = (
        Index("idx_job_log_job_name", "job_name"),
        Index("idx_job_log_started_at", "started_at"),
    )


class Watchlist(Base):
    """User watchlist for tracking properties of interest."""
    __tablename__ = "watchlist"

    id = Column(String, primary_key=True, default=generate_uuid)
    listing_id = Column(String, nullable=False)  # Foreign key to clean_listings
    user_id = Column(String, nullable=False, default="default")  # For future multi-user support
    notes = Column(Text)
    tags = Column(JSON)  # Array of tags for categorization
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_watchlist_listing_id", "listing_id"),
        Index("idx_watchlist_user_id", "user_id"),
    )


class FailedRecord(Base):
    """Dead letter queue for failed ETL records."""
    __tablename__ = "failed_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_portal = Column(String(50), nullable=False, index=True)
    source_id = Column(String(255), nullable=False, index=True)
    raw_data = Column(JSON, nullable=False)
    stage = Column(String(50), nullable=False)  # normalization, deduplication, geocoding, enrichment, validation
    failure_reason = Column(String(100), nullable=False)
    error_message = Column(Text, nullable=False)
    error_details = Column(Text)
    retry_count = Column(Integer, default=0)
    resolved = Column(Integer, default=0)  # 0 = unresolved, 1 = resolved
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_failed_records_source", "source_portal", "source_id"),
        Index("idx_failed_records_stage", "stage"),
        Index("idx_failed_records_resolved", "resolved"),
    )


class ModelVersion(Base):
    """Model version tracking for ML models."""
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(100), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    trained_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    is_active = Column(Integer, default=1)  # 1 = active, 0 = inactive

    # Metrics
    train_mae = Column(Float)
    train_rmse = Column(Float)
    train_r2 = Column(Float)
    test_mae = Column(Float)
    test_rmse = Column(Float)
    test_r2 = Column(Float)
    overfitting = Column(Integer, default=0)  # 1 = overfitting detected

    # Model metadata
    n_samples = Column(Integer)
    n_features = Column(Integer)
    best_iteration = Column(Integer)
    feature_importance = Column(JSON)  # Dict of feature: importance

    # Artifact path
    model_path = Column(String(500))

    __table_args__ = (
        Index("idx_model_versions_name", "model_name"),
        Index("idx_model_versions_active", "is_active"),
    )


class WeightChangeAudit(Base):
    """Audit trail for scoring weight changes."""
    __tablename__ = "weight_change_audit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    changed_by = Column(String(100), nullable=False)
    reason = Column(Text)
    old_weights = Column(JSON, nullable=False)
    new_weights = Column(JSON, nullable=False)
    diff = Column(JSON)  # Difference between old and new weights
    checksum = Column(String(64))  # SHA256 checksum for integrity

    __table_args__ = (
        Index("idx_weight_change_timestamp", "timestamp"),
        Index("idx_weight_change_by", "changed_by"),
    )


def get_engine(database_url: Optional[str] = None):
    """Create SQLAlchemy engine with optimized connection pooling."""
    url = database_url or config.database_url
    if url.startswith("sqlite"):
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
            pool_pre_ping=True,  # Verify connections before using
        )
        # Enable WAL mode + performance PRAGMAs for SQLite
        from sqlalchemy import event
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")          # 10-20x faster writes
            cursor.execute("PRAGMA synchronous=NORMAL")         # Safe with WAL, no fsync wait
            cursor.execute("PRAGMA cache_size=-65536")          # 64 MB page cache
            cursor.execute("PRAGMA temp_store=MEMORY")          # Temp tables in RAM
            cursor.execute("PRAGMA mmap_size=268435456")        # 256 MB memory-mapped I/O
            cursor.execute("PRAGMA journal_size_limit=6291456") # 6 MB WAL limit
            cursor.execute("PRAGMA wal_autocheckpoint=1000")    # Checkpoint every 1000 pages
            cursor.close()
        return engine
    # PostgreSQL with optimized connection pooling
    pool_size = int(os.environ.get("DB_POOL_SIZE", "10"))
    max_overflow = int(os.environ.get("DB_MAX_OVERFLOW", "20"))
    pool_recycle = int(os.environ.get("DB_POOL_RECYCLE", "3600"))  # 1 hour
    
    return create_engine(
        url,
        echo=False,
        pool_pre_ping=True,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_recycle=pool_recycle,
        poolclass=QueuePool
    )


def init_db(database_url: Optional[str] = None):
    """Initialize database tables."""
    engine = get_engine(database_url)
    Base.metadata.create_all(engine)
    return engine


def get_session_factory(engine):
    """Get session factory bound to engine."""
    return sessionmaker(bind=engine, expire_on_commit=False)
