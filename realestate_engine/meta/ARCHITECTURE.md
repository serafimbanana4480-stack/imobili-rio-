# Production-Ready Architecture (Phase 22)

## 1. Core Hardening
- **Config**: `Config` class with `is_production`, validation rules (JWT secret length, CORS no wildcard)
- **Security**: Security headers middleware, TrustedHost in production, CORS from env
- **Auth**: JWT with configurable secret, optional auth fallback controlled by `API_AUTH_REQUIRED`
- **Rate Limiting**: `slowapi` with configurable limits per endpoint category
- **Cache**: Redis with memory fallback, TTL, stats, `trimestre` typo fixed
- **Database**: SQLite WAL mode, PostgreSQL pool config (`pool_pre_ping`, `pool_size`, `max_overflow`)

## 2. Data Quality (5D)
- Completeness, Accuracy, Consistency, Freshness, Uniqueness
- Fixed field name mapping to ORM (`lat/lon`, `tem_ac`, `tipologia`)
- SQLite-backed cache for quality results

## 3. Meta Layer
- `TechAuditEngine`: read-only audit of stack versions, security posture, architecture completeness
- Generates JSON reports and Markdown summaries
- No automatic mutations — human-approved actions only

## 4. Explainable AI
- `/api/v1/explain/{listing_id}` endpoint returns top-5 SHAP features + location effect
- Depends on trained XGBoost model (graceful 503 if not ready)

## 5. Model Monitoring
- `ModelMonitor` with SQLite persistence for snapshots and drift alerts
- `detect_drift()` compares current stats vs baseline using configurable threshold
- Severity classification: critical (>50%), warning (>30%), info

## 6. Intelligent Alerting
- `IntelligentAlertEngine` with SQLite-backed rules + events
- Default rules: scraper block rate, DB latency, cache hit rate, model accuracy, listing quality
- Cooldown mechanism prevents alert storms

## 7. Feature Store
- `FeatureStore` with versioned `FeatureSet` persistence
- Registry tracks latest version per feature set
- Supports retrieval by exact version or latest

## 8. Cost Tracking
- `CostTracker` records source/event/cost per unit
- Aggregated summary by period with cost-per-lead metric

## 9. Testing
21 regression tests covering:
- Production config validation
- JWT roundtrip
- Memory cache fallback
- INE cache key correctness
- Security headers presence
- Data Quality scoring
- Meta Layer audit generation
- Drift detection + alert persistence
- Feature store versioning
- Intelligent alerting thresholds + cooldown
- Cost tracking aggregation

## 10. Next Steps (Future Phases)
- Integrate `ModelMonitor` into orchestrator periodic checks
- Wire `IntelligentAlertEngine` to `AlertManager` for Telegram notifications
- Connect `FeatureStore` to ETL pipeline for feature reuse
- Add cost-per-lead dashboard widget in Streamlit
- Auto-retrain trigger when drift alerts exceed threshold
