"""SQLAlchemy models for Real Estate Opportunity Engine."""
import os
import uuid
from datetime import datetime, UTC
from typing import Optional, List
from sqlalchemy import (
    create_engine, Column, String, Float, Integer, Text, JSON, ForeignKey,
    DateTime, Index, event, func
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.pool import StaticPool

from realestate_engine.utils.config import config

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
    scrape_timestamp = Column(String, nullable=False, default=lambda: datetime.now(UTC).isoformat())
    raw_data = Column(JSON, nullable=False)
    is_sample = Column(Integer, default=0)  # 0 = real data, 1 = sample/fake data
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
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
    scrape_timestamp = Column(String, nullable=False, default=lambda: datetime.now(UTC).isoformat())
    titulo = Column(Text)
    descricao = Column(Text)
    preco_pedido = Column(Float, nullable=False)
    area_util_m2 = Column(Float, nullable=False)
    quartos = Column(Integer, nullable=False)
    casas_banho = Column(Integer)
    morada_raw = Column(Text)
    freguesia = Column(String)
    concelho = Column(String)
    distrito = Column(String)
    lat = Column(Float)
    lon = Column(Float)
    estado = Column(String)
    ano_construcao = Column(Integer)
    cert_energetico = Column(String)
    tipologia = Column(String)
    fotos_urls = Column(JSON)
    num_fotos = Column(Integer)
    agencia = Column(String)

    # Deduplication fingerprint (populated by ETL pipeline)
    fingerprint = Column(String(32), index=True)

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
    
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    valuations = relationship("Valuation", back_populates="listing", cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="listing", cascade="all, delete-orphan")
    price_history = relationship("PriceHistory", back_populates="listing", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="listing", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_clean_listings_fingerprint", "fingerprint"),
        Index("idx_clean_listings_source_portal", "source_portal"),
        Index("idx_clean_listings_freguesia", "freguesia"),
        Index("idx_clean_listings_concelho", "concelho"),
        Index("idx_clean_listings_preco", "preco_pedido"),
        Index("idx_clean_listings_preco_m2", "preco_por_m2"),
        Index("idx_clean_listings_area", "area_util_m2"),
        Index("idx_clean_listings_tipologia", "tipologia"),
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
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
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
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
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
    cached_at = Column(DateTime, default=lambda: datetime.now(UTC))


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
    fetched_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
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
    recorded_at = Column(DateTime, default=lambda: datetime.now(UTC))


class ConfigEntry(Base):
    """System configuration entries."""
    __tablename__ = "config"
    
    key = Column(String, primary_key=True)
    value = Column(JSON)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class JobExecutionLog(Base):
    """Log of scheduled job executions."""
    __tablename__ = "job_execution_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_name = Column(String, nullable=False)
    started_at = Column(DateTime, default=lambda: datetime.now(UTC))
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
    added_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    __table_args__ = (
        Index("idx_watchlist_listing_id", "listing_id"),
        Index("idx_watchlist_user_id", "user_id"),
    )


def get_engine(database_url: Optional[str] = None):
    """Create SQLAlchemy engine."""
    url = database_url or config.database_url
    if url.startswith("sqlite"):
        is_memory = ":memory:" in url
        engine_kwargs = {
            "connect_args": {"check_same_thread": False},
            "echo": False,
        }
        if is_memory:
            engine_kwargs["poolclass"] = StaticPool
        engine = create_engine(
            url,
            **engine_kwargs,
        )
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            if not is_memory:
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA busy_timeout=5000")
            cursor.close()
        return engine
    return create_engine(
        url,
        echo=False,
        pool_pre_ping=True,
        pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
        pool_recycle=int(os.getenv("DB_POOL_RECYCLE_SECONDS", "1800")),
    )


def init_db(database_url: Optional[str] = None):
    """Initialize database tables."""
    engine = get_engine(database_url)
    Base.metadata.create_all(engine)
    return engine


def get_session_factory(engine):
    """Get session factory bound to engine."""
    return sessionmaker(bind=engine, expire_on_commit=False)
