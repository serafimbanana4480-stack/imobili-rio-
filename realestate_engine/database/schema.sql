-- Real Estate Opportunity Engine - Database Schema (SQLite)

-- Raw listings from scraping
CREATE TABLE IF NOT EXISTS raw_listings (
    id TEXT PRIMARY KEY,
    source_portal TEXT NOT NULL,
    source_id TEXT NOT NULL,
    source_url TEXT NOT NULL,
    scrape_timestamp TEXT NOT NULL,
    raw_data JSON NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_raw_listings_source_portal ON raw_listings(source_portal);
CREATE INDEX IF NOT EXISTS idx_raw_listings_scrape_timestamp ON raw_listings(scrape_timestamp);
CREATE INDEX IF NOT EXISTS idx_raw_listings_source_id ON raw_listings(source_id);

-- Clean listings after ETL
CREATE TABLE IF NOT EXISTS clean_listings (
    id TEXT PRIMARY KEY,
    source_portal TEXT NOT NULL,
    source_id TEXT NOT NULL,
    source_url TEXT NOT NULL,
    scrape_timestamp TEXT NOT NULL,
    titulo TEXT,
    descricao TEXT,
    preco_pedido REAL NOT NULL,
    area_util_m2 REAL NOT NULL,
    quartos INTEGER NOT NULL,
    casas_banho INTEGER,
    morada_raw TEXT,
    freguesia TEXT,
    concelho TEXT,
    distrito TEXT,
    lat REAL,
    lon REAL,
    estado TEXT,
    ano_construcao INTEGER,
    cert_energetico TEXT,
    tipologia TEXT,
    fotos_urls JSON,
    num_fotos INTEGER,
    agencia TEXT,
    preco_por_m2 REAL,
    ine_preco_medio_m2 REAL,
    ine_tendencia_mensal REAL,
    dist_metro_m REAL,
    dist_escola_m REAL,
    dist_comercio_m REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_clean_listings_source_portal ON clean_listings(source_portal);
CREATE INDEX IF NOT EXISTS idx_clean_listings_freguesia ON clean_listings(freguesia);
CREATE INDEX IF NOT EXISTS idx_clean_listings_concelho ON clean_listings(concelho);
CREATE INDEX IF NOT EXISTS idx_clean_listings_preco ON clean_listings(preco_pedido);
CREATE INDEX IF NOT EXISTS idx_clean_listings_preco_m2 ON clean_listings(preco_por_m2);
CREATE INDEX IF NOT EXISTS idx_clean_listings_area ON clean_listings(area_util_m2);
CREATE INDEX IF NOT EXISTS idx_clean_listings_tipologia ON clean_listings(tipologia);

-- Valuations
CREATE TABLE IF NOT EXISTS valuations (
    id TEXT PRIMARY KEY,
    listing_id TEXT NOT NULL,
    valor_justo REAL,
    hedonic_value REAL,
    comps_value REAL,
    ine_value REAL,
    xgboost_value REAL,
    ci_lower REAL,
    ci_upper REAL,
    discount REAL,
    confianca REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (listing_id) REFERENCES clean_listings(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_valuations_listing_id ON valuations(listing_id);
CREATE INDEX IF NOT EXISTS idx_valuations_valor_justo ON valuations(valor_justo);

-- Scores
CREATE TABLE IF NOT EXISTS scores (
    id TEXT PRIMARY KEY,
    listing_id TEXT NOT NULL,
    score_total REAL NOT NULL,
    score_discount REAL,
    score_location REAL,
    score_condition REAL,
    score_liquidity REAL,
    score_freshness REAL,
    classificacao TEXT,
    rationale TEXT,
    red_flags JSON,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (listing_id) REFERENCES clean_listings(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_scores_listing_id ON scores(listing_id);
CREATE INDEX IF NOT EXISTS idx_scores_score_total ON scores(score_total);

-- Price history
CREATE TABLE IF NOT EXISTS price_history (
    id TEXT PRIMARY KEY,
    listing_id TEXT NOT NULL,
    preco REAL NOT NULL,
    data TEXT NOT NULL,
    source TEXT,
    FOREIGN KEY (listing_id) REFERENCES clean_listings(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_price_history_listing_id ON price_history(listing_id);
CREATE INDEX IF NOT EXISTS idx_price_history_data ON price_history(data);

-- Notifications
CREATE TABLE IF NOT EXISTS notifications (
    id TEXT PRIMARY KEY,
    listing_id TEXT NOT NULL,
    telegram_chat_id TEXT,
    telegram_message_id TEXT,
    message TEXT,
    sent_at TEXT,
    status TEXT DEFAULT 'pending',
    error_message TEXT,
    FOREIGN KEY (listing_id) REFERENCES clean_listings(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_notifications_listing_id ON notifications(listing_id);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status);

-- Config
CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value JSON,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Scheduler state / job execution log
CREATE TABLE IF NOT EXISTS job_execution_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_name TEXT NOT NULL,
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    finished_at TEXT,
    status TEXT,
    error_message TEXT,
    records_processed INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_job_log_job_name ON job_execution_log(job_name);
CREATE INDEX IF NOT EXISTS idx_job_log_started_at ON job_execution_log(started_at);
