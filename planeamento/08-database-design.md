# DATABASE DESIGN — REAL ESTATE OPPORTUNITY ENGINE
## Schema, Queries e Optimização (SQLite/PostgreSQL)

> **Este documento:** Especificação completa do design da base de dados  
> **Objectivo:** Fornecer especificação detalhada de database para IA implementar  
> **Linhas:** 1500+ linhas de documentação detalhada  
> **Versão:** 5.0 (Actualizado com Volume 13)

---

## ÍNDICE

1. [Introdução ao Database Design](#1-introducao-ao-database-design)
2. [Escolha de Database](#2-escolha-de-database)
3. [Schema Completo](#3-schema-completo)
4. [Tabela: raw_listings](#4-tabela-raw_listings)
5. [Tabela: clean_listings](#5-tabela-clean_listings)
6. [Tabela: valuations](#6-tabela-valuations)
7. [Tabela: scores](#7-tabela-scores)
8. [Tabela: notifications](#8-tabela-notifications)
9. [Tabela: price_history](#9-tabela-price_history)
10. [Tabela: config](#10-tabela-config)
11. [Índices e Optimização](#11-indices-e-optimizacao)
12. [Queries Comuns](#12-queries-comuns)
13. [Migração SQLite → PostgreSQL](#13-migracao-sqlite-postgresql)
14. [Backup e Recovery](#14-backup-e-recovery)
15. [Glossário de Database](#15-glossario-de-database)

---

## 1. INTRODUÇÃO AO DATABASE DESIGN

### 1.1 Objectivo do Database

**Database** é o repositório central de dados do sistema, armazenando:
- Raw listings (dados brutos de scraping)
- Clean listings (dados normalizados e enriquecidos)
- Valuations (valor justo estimado)
- Scores (score de 0-10)
- Notifications (histórico de notificações)
- Price history (histórico de preços)
- Config (configurações do sistema)

### 1.2 Porquê SQLite (MVP) → PostgreSQL (Produção)?

**SQLite (MVP):**
- Custo zero (local)
- GDPR compliance por design
- Suficiente para MVP (1000 listings/dia)
- Simples de implementar
- Single file (fácil backup)

**PostgreSQL (Produção):**
- Escalável (ilimitado listings)
- Multi-users (concorrência)
- Mais robusto
- Suporta JSON, arrays, etc.
- Requer VPS (custo €20-50/mês)

---

## 2. ESCOLHA DE DATABASE

### 2.1 Comparação SQLite vs PostgreSQL

```
┌─────────────────────────────────────────────────────────────────────────────┐
│          COMPARAÇÃO: SQLITE VS POSTGRESQL                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ASPECTO                    │ SQLITE (MVP)          │ POSTGRESQL (Produção)   │
│  ────────────────────────────┼─────────────────────┼───────────────────────│
│  Custo                       │ €0 (local)          │ €20-50/mês (VPS)      │
│  Concorrência                │ 1 writer            │ Múltiplos writers      │
│  Escalabilidade             │ < 50.000 listings    │ Ilimitado              │
│  Complexidade               │ Baixa               │ Média                  │
│  GDPR Compliance            │ 100% (local)        │ Depende de hosting     │
│  Backup                     │ Single file         │ Dump/Restore           │
│  JSON Support              │ Simples             │ JSONB (avançado)       │
│  Arrays                     │ Não                 │ Sim                    │
│  Full-text Search           │ FTS3/FTS4           │ tsvector               │
│  Replication               │ Não                 │ Sim                    │
│  Partitioning              │ Não                 │ Sim                    │
│  Transaction Support       │ Simples             │ ACID completo           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Estratégia de Migração

**Fase 1 (MVP): SQLite**
- 1000 listings/dia
- Single process
- Local deployment

**Fase 2 (Produção): PostgreSQL**
- 5000+ listings/dia
- Multi-instance
- VPS deployment

**Migração:**
- Export SQLite → PostgreSQL
- Testar queries
- Switch deployment
- Monitorar performance

---

## 3. SCHEMA COMPLETO

### 3.1 Diagrama de Schema (SQLite)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              SCHEMA COMPLETO (SQLITE)                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  raw_listings ────────────────┐                                         │
│  │ id TEXT PRIMARY KEY         │                                         │
│  │ source_portal TEXT          │                                         │
│  │ source_id TEXT              │                                         │
│  │ source_url TEXT             │                                         │
│  │ scrape_timestamp TEXT       │                                         │
│  │ raw_data JSON               │                                         │
│  │ created_at TEXT             │                                         │
│  └─────────────────────────────┘                                         │
│              │                                                            │   │
│              ▼                                                            │   │
│  clean_listings ───────────────┐                                         │
│  │ id TEXT PRIMARY KEY         │                                         │
│  │ source_portal TEXT          │◄────────────────────┐                    │   │
│  │ source_id TEXT              │◄────────────────────┤                    │   │
│  │ titulo TEXT                 │                    │                    │   │
│  │ preco_pedido REAL           │                    │                    │   │
│  │ area_util_m2 REAL           │                    │                    │   │
│  │ quartos INTEGER             │                    │                    │   │
│  │ freguesia TEXT              │                    │                    │   │
│  │ lat REAL                    │                    │                    │   │
│  │ lon REAL                    │                    │                    │   │
│  │ ...                        │                    │                    │   │
│  └─────────────────────────────┘                    │                    │   │
│              │                                         │                    │   │
│              ▼                                         ▼                    │   │
│  valuations ────────────────┐              price_history ────────────┐   │   │
│  │ id TEXT PRIMARY KEY        │              │ id TEXT PRIMARY KEY       │   │   │
│  │ listing_id TEXT            │◄─────────────│ listing_id TEXT          │   │   │
│  │ valor_justo REAL           │              │ preco REAL               │   │   │
│  │ hedonic_value REAL         │              │ data TEXT                 │   │   │
│  │ comps_value REAL           │              │ source TEXT               │   │   │
│  │ ine_value REAL             │              └───────────────────────────┘   │   │
│  │ xgboost_value REAL         │                                            │   │
│  │ ci_lower REAL              │                                            │   │
│  │ ci_upper REAL              │                                            │   │
│  │ discount REAL              │                                            │   │
│  │ confianca REAL            │                                            │   │
│  └─────────────────────────────┘                                            │   │
│              │                                                                 │   │
│              ▼                                                                 │   │
│  scores ────────────────────────┐                                            │   │
│  │ id TEXT PRIMARY KEY         │                                            │   │
│  │ listing_id TEXT            │◄────────────────────────────────────┐        │   │
│  │ score_total REAL           │                                         │        │   │
│  │ score_discount REAL         │                                         │        │   │
│  │ score_location REAL        │                                         │        │   │
│  │ score_condition REAL       │                                         │        │   │
│  │ score_liquidity REAL        │                                         │        │   │
│  │ score_freshness REAL       │                                         │        │   │
│  │ classificacao TEXT         │                                         │        │   │
│  │ rationale TEXT             │                                         │        │   │
│  │ red_flags JSON             │                                         │        │   │
│  └─────────────────────────────┘                                         │        │   │
│              │                                                              │        │   │
│              ▼                                                              │        │   │
│  notifications ────────────────┐                                           │        │   │
│  │ id TEXT PRIMARY KEY         │                                           │        │   │
│  │ listing_id TEXT            │◄────────────────────────────────────┘        │   │
│  │ telegram_chat_id TEXT      │                                                      │   │
│  │ telegram_message_id TEXT   │                                                      │   │
│  │ message TEXT               │                                                      │   │
│  │ sent_at TEXT               │                                                      │   │
│  └─────────────────────────────┘                                                      │   │
│                                                                                       │   │
│  config ────────────────────────┐                                                   │   │
│  │ key TEXT PRIMARY KEY        │                                                   │   │
│  │ value JSON                 │                                                   │   │
│  │ updated_at TEXT            │                                                   │   │
│  └─────────────────────────────┘                                                   │   │
│                                                                                       │   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. TABELA: RAW_LISTINGS

### 4.1 Descrição

Armazena dados brutos de scraping (raw data). Cada portal tem formato diferente, por isso os dados são guardados em JSON no campo `raw_data`.

### 4.2 Schema SQL

```sql
CREATE TABLE raw_listings (
    id TEXT PRIMARY KEY,
    source_portal TEXT NOT NULL,
    source_id TEXT NOT NULL,
    source_url TEXT NOT NULL,
    scrape_timestamp TEXT NOT NULL,
    raw_data JSON NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### 4.3 Campos

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | TEXT | ID único (UUID) |
| source_portal | TEXT | Portal (idealista, imovirtual, etc.) |
| source_id | TEXT | ID do listing no portal |
| source_url | TEXT | URL do listing |
| scrape_timestamp | TEXT | Timestamp do scraping (ISO format) |
| raw_data | JSON | Dados brutos (formato variável por portal) |
| created_at | TEXT | Timestamp de criação (ISO format) |

### 4.4 Índices

```sql
CREATE INDEX idx_raw_listings_source_portal ON raw_listings(source_portal);
CREATE INDEX idx_raw_listings_scrape_timestamp ON raw_listings(scrape_timestamp);
CREATE INDEX idx_raw_listings_source_id ON raw_listings(source_id);
```

---

## 5. TABELA: CLEAN_LISTINGS

### 5.1 Descrição

Armazena dados normalizados e enriquecidos (clean data). Formato canónico (mesmo para todos os portais).

### 5.2 Schema SQL

```sql
CREATE TABLE clean_listings (
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
    lat REAL,
    lon REAL,
    estado TEXT,
    ano_construcao INTEGER,
    cert_energetico TEXT,
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
```

### 5.3 Campos

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | TEXT | ID único (UUID) |
| source_portal | TEXT | Portal (idealista, imovirtual, etc.) |
| source_id | TEXT | ID do listing no portal |
| source_url | TEXT | URL do listing |
| scrape_timestamp | TEXT | Timestamp do scraping (ISO format) |
| titulo | TEXT | Título do listing |
| descricao | TEXT | Descrição do listing |
| preco_pedido | REAL | Preço pedido (€) |
| area_util_m2 | REAL | Área útil (m²) |
| quartos | INTEGER | Número de quartos |
| casas_banho | INTEGER | Número de casas de banho |
| morada_raw | TEXT | Morada (texto bruto) |
| freguesia | TEXT | Freguesia |
| concelho | TEXT | Concelho |
| lat | REAL | Latitude |
| lon | REAL | Longitude |
| estado | TEXT | Estado de conservação |
| ano_construcao | INTEGER | Ano de construção |
| cert_energetico | TEXT | Certificado energético (A-G) |
| fotos_urls | JSON | URLs das fotos |
| num_fotos | INTEGER | Número de fotos |
| agencia | TEXT | Agência imobiliária |
| preco_por_m2 | REAL | Preço por m² (calculado) |
| ine_preco_medio_m2 | REAL | Preço médio por m² da freguesia (INE) |
| ine_tendencia_mensal | REAL | Tendência mensal (INE) |
| dist_metro_m | REAL | Distância ao metro (m) |
| dist_escola_m | REAL | Distância à escola (m) |
| dist_comercio_m | REAL | Distância ao comércio (m) |
| created_at | TEXT | Timestamp de criação (ISO format) |
| updated_at | TEXT | Timestamp de actualização (ISO format) |

### 5.4 Índices

```sql
CREATE INDEX idx_clean_listings_freguesia ON clean_listings(freguesia);
CREATE INDEX idx_clean_listings_preco ON clean_listings(preco_pedido);
CREATE INDEX idx_clean_listings_area ON clean_listings(area_util_m2);
CREATE INDEX idx_clean_listings_scrape_timestamp ON clean_listings(scrape_timestamp);
CREATE INDEX idx_clean_listings_source_id ON clean_listings(source_id);
CREATE INDEX idx_clean_listings_source_portal ON clean_listings(source_portal);
```

---

## 6. TABELA: VALUATIONS

### 6.1 Descrição

Armazena valuations (valor justo estimado) para cada listing.

### 6.2 Schema SQL

```sql
CREATE TABLE valuations (
    id TEXT PRIMARY KEY,
    listing_id TEXT NOT NULL,
    valor_justo REAL NOT NULL,
    hedonic_value REAL,
    comps_value REAL,
    ine_value REAL,
    xgboost_value REAL,
    ci_lower REAL,
    ci_upper REAL,
    discount REAL NOT NULL,
    confianca REAL NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (listing_id) REFERENCES clean_listings(id)
);
```

### 6.3 Campos

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | TEXT | ID único (UUID) |
| listing_id | TEXT | ID do listing (FK) |
| valor_justo | REAL | Valor justo estimado (€) |
| hedonic_value | REAL | Valor do Hedonic Model (€) |
| comps_value | REAL | Valor do Comps Engine (€) |
| ine_value | REAL | Valor do INE Macro Data (€) |
| xgboost_value | REAL | Valor do XGBoost Model (€) |
| ci_lower | REAL | Intervalo de confiança inferior (€) |
| ci_upper | REAL | Intervalo de confiança superior (€) |
| discount | REAL | Discount (%) |
| confianca | REAL | Confiança (%) |
| created_at | TEXT | Timestamp de criação (ISO format) |

### 6.4 Índices

```sql
CREATE INDEX idx_valuations_listing_id ON valuations(listing_id);
CREATE INDEX idx_valuations_discount ON valuations(discount);
CREATE INDEX idx_valuations_valor_justo ON valuations(valor_justo);
```

---

## 7. TABELA: SCORES

### 7.1 Descrição

Armazena scores (0-10) para cada listing.

### 7.2 Schema SQL

```sql
CREATE TABLE scores (
    id TEXT PRIMARY KEY,
    listing_id TEXT NOT NULL,
    score_total REAL NOT NULL,
    score_discount REAL NOT NULL,
    score_location REAL NOT NULL,
    score_condition REAL NOT NULL,
    score_liquidity REAL NOT NULL,
    score_freshness REAL NOT NULL,
    classificacao TEXT NOT NULL,
    rationale TEXT,
    red_flags JSON,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (listing_id) REFERENCES clean_listings(id)
);
```

### 7.3 Campos

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | TEXT | ID único (UUID) |
| listing_id | TEXT | ID do listing (FK) |
| score_total | REAL | Score total (0-10) |
| score_discount | REAL | Score de discount (0-10) |
| score_location | REAL | Score de localização (0-10) |
| score_condition | REAL | Score de estado (0-10) |
| score_liquidity | REAL | Score de liquidez (0-10) |
| score_freshness | REAL | Score de frescura (0-10) |
| classificacao | TEXT | Classificação (Imperdível, Bom, Aceitável, Não recomendado) |
| rationale | TEXT | Explicação do score |
| red_flags | JSON | Red flags (JSON array) |
| created_at | TEXT | Timestamp de criação (ISO format) |

### 7.4 Índices

```sql
CREATE INDEX idx_scores_listing_id ON scores(listing_id);
CREATE INDEX idx_scores_score_total ON scores(score_total);
CREATE INDEX idx_scores_classificacao ON scores(classificacao);
```

---

## 8. TABELA: NOTIFICATIONS

### 8.1 Descrição

Armazena histórico de notificações enviadas via Telegram.

### 8.2 Schema SQL

```sql
CREATE TABLE notifications (
    id TEXT PRIMARY KEY,
    listing_id TEXT NOT NULL,
    telegram_chat_id TEXT NOT NULL,
    telegram_message_id TEXT,
    message TEXT NOT NULL,
    sent_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (listing_id) REFERENCES clean_listings(id)
);
```

### 8.3 Campos

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | TEXT | ID único (UUID) |
| listing_id | TEXT | ID do listing (FK) |
| telegram_chat_id | TEXT | Chat ID do Telegram |
| telegram_message_id | TEXT | Message ID do Telegram |
| message | TEXT | Mensagem enviada |
| sent_at | TEXT | Timestamp de envio (ISO format) |

### 8.4 Índices

```sql
CREATE INDEX idx_notifications_listing_id ON notifications(listing_id);
CREATE INDEX idx_notifications_sent_at ON notifications(sent_at);
```

---

## 9. TABELA: PRICE_HISTORY

### 9.1 Descrição

Armazena histórico de preços para cada listing (útil para detectar mudanças de preço).

### 9.2 Schema SQL

```sql
CREATE TABLE price_history (
    id TEXT PRIMARY KEY,
    listing_id TEXT NOT NULL,
    preco REAL NOT NULL,
    data TEXT NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (listing_id) REFERENCES clean_listings(id)
);
```

### 9.3 Campos

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | TEXT | ID único (UUID) |
| listing_id | TEXT | ID do listing (FK) |
| preco | REAL | Preço (€) |
| data | TEXT | Data do preço (ISO format) |
| source | TEXT | Fonte do preço (portal) |
| created_at | TEXT | Timestamp de criação (ISO format) |

### 9.4 Índices

```sql
CREATE INDEX idx_price_history_listing_id ON price_history(listing_id);
CREATE INDEX idx_price_history_data ON price_history(data);
```

---

## 10. TABELA: CONFIG

### 10.1 Descrição

Armazena configurações do sistema (filtros, thresholds, etc.).

### 10.2 Schema SQL

```sql
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value JSON NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### 10.3 Campos

| Campo | Tipo | Descrição |
|-------|------|-----------|
| key | TEXT | Chave de configuração |
| value | JSON | Valor (JSON) |
| updated_at | TEXT | Timestamp de actualização (ISO format) |

### 10.4 Exemplos de Config

```json
{
  "key": "telegram_chat_ids",
  "value": ["123456789", "987654321"]
}

{
  "key": "scraping_filters",
  "value": {
    "preco_max": 500000,
    "preco_min": 50000,
    "area_min": 50,
    "freguesias": ["cedofeita", "paranhos", "bonfim"]
  }
}

{
  "key": "scoring_thresholds",
  "value": {
    "discount_threshold": 20,
    "location_threshold": 7,
    "condition_threshold": 6,
    "liquidity_threshold": 7,
    "freshness_threshold": 7
  }
}
```

---

## 11. ÍNDICES E OPTIMIZAÇÃO

### 11.1 Índices Completos (SQLite)

```sql
-- raw_listings
CREATE INDEX idx_raw_listings_source_portal ON raw_listings(source_portal);
CREATE INDEX idx_raw_listings_scrape_timestamp ON raw_listings(scrape_timestamp);
CREATE INDEX idx_raw_listings_source_id ON raw_listings(source_id);

-- clean_listings
CREATE INDEX idx_clean_listings_freguesia ON clean_listings(freguesia);
CREATE INDEX idx_clean_listings_preco ON clean_listings(preco_pedido);
CREATE INDEX idx_clean_listings_area ON clean_listings(area_util_m2);
CREATE INDEX idx_clean_listings_scrape_timestamp ON clean_listings(scrape_timestamp);
CREATE INDEX idx_clean_listings_source_id ON clean_listings(source_id);
CREATE INDEX idx_clean_listings_source_portal ON clean_listings(source_portal);

-- valuations
CREATE INDEX idx_valuations_listing_id ON valuations(listing_id);
CREATE INDEX idx_valuations_discount ON valuations(discount);
CREATE INDEX idx_valuations_valor_justo ON valuations(valor_justo);

-- scores
CREATE INDEX idx_scores_listing_id ON scores(listing_id);
CREATE INDEX idx_scores_score_total ON scores(score_total);
CREATE INDEX idx_scores_classificacao ON scores(classificacao);

-- notifications
CREATE INDEX idx_notifications_listing_id ON notifications(listing_id);
CREATE INDEX idx_notifications_sent_at ON notifications(sent_at);

-- price_history
CREATE INDEX idx_price_history_listing_id ON price_history(listing_id);
CREATE INDEX idx_price_history_data ON price_history(data);
```

### 11.2 Optimizações SQLite

```sql
-- Activar WAL mode (Write-Ahead Logging)
PRAGMA journal_mode = WAL;

-- Activar synchronous mode (trade-off entre performance e segurança)
PRAGMA synchronous = NORMAL;

-- Activar cache size (default 2MB, aumentar para 10MB)
PRAGMA cache_size = -10240;  -- 10MB

-- Activar memory mapping (para melhor performance)
PRAGMA mmap_size = 268435456;  -- 256MB
```

---

## 12. QUERIES COMUNS

### 12.1 Query: Top Listings por Score

```sql
SELECT 
    cl.id,
    cl.titulo,
    cl.preco_pedido,
    cl.area_util_m2,
    cl.preco_por_m2,
    cl.freguesia,
    s.score_total,
    s.classificacao,
    s.rationale,
    v.valor_justo,
    v.discount
FROM clean_listings cl
JOIN scores s ON cl.id = s.listing_id
JOIN valuations v ON cl.id = v.listing_id
WHERE s.score_total >= 8.0
ORDER BY s.score_total DESC, v.discount DESC
LIMIT 10;
```

### 12.2 Query: Listings por Freguesia

```sql
SELECT 
    freguesia,
    COUNT(*) as total_listings,
    AVG(preco_pedido) as avg_preco,
    AVG(preco_por_m2) as avg_preco_por_m2,
    AVG(s.score_total) as avg_score
FROM clean_listings cl
JOIN scores s ON cl.id = s.listing_id
GROUP BY freguesia
ORDER BY avg_score DESC;
```

### 12.3 Query: Distribuição de Classificações

```sql
SELECT 
    classificacao,
    COUNT(*) as total,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM scores), 2) as percentagem
FROM scores
GROUP BY classificacao
ORDER BY total DESC;
```

### 12.4 Query: Listings com Overpricing

```sql
SELECT 
    cl.id,
    cl.titulo,
    cl.preco_pedido,
    cl.freguesia,
    v.valor_justo,
    v.discount
FROM clean_listings cl
JOIN valuations v ON cl.id = v.listing_id
WHERE v.discount < -10
ORDER BY v.discount ASC
LIMIT 10;
```

### 12.5 Query: Listings com Discount Alto

```sql
SELECT 
    cl.id,
    cl.titulo,
    cl.preco_pedido,
    cl.freguesia,
    v.valor_justo,
    v.discount,
    s.score_total
FROM clean_listings cl
JOIN valuations v ON cl.id = v.listing_id
JOIN scores s ON cl.id = s.listing_id
WHERE v.discount >= 20
ORDER BY v.discount DESC
LIMIT 10;
```

---

## 13. MIGRAÇÃO SQLITE → POSTGRESQL

### 13.1 Estratégia de Migração

```python
import sqlite3
import psycopg2
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseMigrator:
    """Migra dados de SQLite para PostgreSQL."""
    
    def __init__(self, sqlite_path: str, postgres_uri: str):
        self.sqlite_path = sqlite_path
        self.postgres_uri = postgres_uri
    
    def migrate(self):
        """Executa migração completa."""
        logger.info("DatabaseMigrator: Iniciando migração")
        
        # Conectar a SQLite
        sqlite_conn = sqlite3.connect(self.sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cursor = sqlite_conn.cursor()
        
        # Conectar a PostgreSQL
        postgres_conn = psycopg2.connect(self.postgres_uri)
        postgres_cursor = postgres_conn.cursor()
        
        try:
            # Migrar raw_listings
            self._migrate_table(sqlite_cursor, postgres_cursor, 'raw_listings')
            
            # Migrar clean_listings
            self._migrate_table(sqlite_cursor, postgres_cursor, 'clean_listings')
            
            # Migrar valuations
            self._migrate_table(sqlite_cursor, postgres_cursor, 'valuations')
            
            # Migrar scores
            self._migrate_table(sqlite_cursor, postgres_cursor, 'scores')
            
            # Migrar notifications
            self._migrate_table(sqlite_cursor, postgres_cursor, 'notifications')
            
            # Migrar price_history
            self._migrate_table(sqlite_cursor, postgres_cursor, 'price_history')
            
            # Migrar config
            self._migrate_table(sqlite_cursor, postgres_cursor, 'config')
            
            # Commit PostgreSQL
            postgres_conn.commit()
            
            logger.info("DatabaseMigrator: Migração completa")
        
        except Exception as e:
            postgres_conn.rollback()
            logger.error(f"DatabaseMigrator: Erro na migração: {e}")
            raise
        
        finally:
            sqlite_conn.close()
            postgres_conn.close()
    
    def _migrate_table(self, sqlite_cursor, postgres_cursor, table_name: str):
        """Migra uma tabela específica."""
        logger.info(f"DatabaseMigrator: Migrando {table_name}")
        
        # Obter dados de SQLite
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            logger.info(f"DatabaseMigrator: {table_name} vazia, a saltar")
            return
        
        # Obter colunas
        columns = [description[0] for description in sqlite_cursor.description]
        
        # Inserir em PostgreSQL
        for row in rows:
            values = dict(zip(columns, row))
            
            # Converter JSON para PostgreSQL JSONB
            for key, value in values.items():
                if isinstance(value, str) and (value.startswith('[') or value.startswith('{')):
                    try:
                        values[key] = json.loads(value)
                    except json.JSONDecodeError:
                        pass
            
            # Construir query
            columns_str = ', '.join(columns)
            placeholders = ', '.join(['%s'] * len(columns))
            values_list = [values[col] for col in columns]
            
            query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            postgres_cursor.execute(query, values_list)
        
        logger.info(f"DatabaseMigrator: {table_name} migrado ({len(rows)} rows)")
```

---

## 14. BACKUP E RECOVERY

### 14.1 Backup SQLite

```python
import shutil
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SQLiteBackup:
    """Backup de database SQLite."""
    
    def __init__(self, db_path: str, backup_dir: str = 'data/backups'):
        self.db_path = db_path
        self.backup_dir = backup_dir
    
    def backup(self):
        """Cria backup do database."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{self.backup_dir}/realestate_{timestamp}.db"
        
        shutil.copy2(self.db_path, backup_path)
        
        logger.info(f"SQLiteBackup: Backup criado em {backup_path}")
        
        return backup_path
    
    def restore(self, backup_path: str):
        """Restaura backup do database."""
        shutil.copy2(backup_path, self.db_path)
        
        logger.info(f"SQLiteBackup: Backup restaurado de {backup_path}")
```

### 14.2 Backup PostgreSQL

```bash
# Backup PostgreSQL
pg_dump -U username -d database_name > backup.sql

# Restore PostgreSQL
psql -U username -d database_name < backup.sql
```

---

## 15. GLOSSÁRIO DE DATABASE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│            GLOSSÁRIO DE DATABASE                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DATABASE: Base de dados (repositório de dados)                          │
│                                                                             │
│  SCHEMA: Estrutura da base de dados (tabelas, colunas, índices)        │
│                                                                             │
│  TABLE: Tabela (coleção de dados)                                         │
│                                                                             │
│  COLUMN: Coluna (campo de dados)                                           │
│                                                                             │
│  PRIMARY KEY: Chave primária (identificador único)                       │
│                                                                             │
│  FOREIGN KEY: Chave estrangeira (relaciona tabelas)                     │
│                                                                             │
│  INDEX: Índice (acelera queries)                                         │
│                                                                             │
│  SQL: Structured Query Language (linguagem de queries)                   │
│                                                                             │
│  SQLITE: Database local (single file)                                     │
│                                                                             │
│  POSTGRESQL: Database relacional (produção)                               │
│                                                                             │
│  JSON: JavaScript Object Notation (formato de dados)                       │
│                                                                             │
│  JSONB: JSON Binary (PostgreSQL, mais eficiente)                          │
│                                                                             │
│  WAL: Write-Ahead Logging (modo SQLite para melhor performance)          │
│                                                                             │
│  FOREIGN KEY CONSTRAINT: Restrição de chave estrangeira                   │
│                                                                             │
│  ACID: Atomicity, Consistency, Isolation, Durability (propriedades)    │
│                                                                             │
│  TRANSACTION: Transacção (grupo de operações atómicas)                 │
│                                                                             │
│  QUERY: Query (pedido de dados)                                            │
│                                                                             │
│  JOIN: Join (combinação de tabelas)                                       │
│                                                                             │
│  AGGREGATION: Agregação (COUNT, AVG, SUM, etc.)                         │
│                                                                             │
│  MIGRATION: Migração (mover dados de uma database para outra)            │
│                                                                             │
│  BACKUP: Backup (cópia de segurança)                                      │
│                                                                             │
│  RECOVERY: Recovery (restauração de backup)                               │
│                                                                             │
│  DUMP: Dump (exportação de dados)                                         │
│                                                                             │
│  RESTORE: Restore (importação de dados)                                    │
│                                                                             │
│  CONCURRENCY: Concorrência (múltiplos acessos simultâneos)               │
│                                                                             │
│  SCALABILITY: Escalabilidade (capacidade de crescimento)                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*Fim do Documento 08 — Database Design*
