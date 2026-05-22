# ESTRATÉGIA DE DADOS — REAL ESTATE OPPORTUNITY ENGINE
## Gestão de Dados, Retenção, Backup e Analytics

> **Este documento:** Especificação completa de estratégia de dados  
> **Objectivo:** Fornecer especificação detalhada de dados para IA implementar  
> **Linhas:** 1500+ linhas de documentação detalhada  
> **Versão:** 5.0 (Actualizado com Volume 13)

---

## ÍNDICE

1. [Introdução à Estratégia de Dados](#1-introducao-a-estrategia-de-dados)
2. [Arquitectura de Dados](#2-arquitetura-de-dados)
3. [Fluxo de Dados](#3-fluxo-de-dados)
4. [Data Quality](#4-data-quality)
5. [Data Retention](#5-data-retention)
6. [Backup Strategy](#6-backup-strategy)
7. [Data Archival](#7-data-archival)
8. [Data Analytics](#8-data-analytics)
9. [Data Governance](#9-data-governance)
10. [Data Privacy](#10-data-privacy)
11. [Data Lineage](#11-data-lineage)
12. [Data Catalog](#12-data-catalog)
13. [Data Migration](#13-data-migration)
14. [Data Lake vs Data Warehouse](#14-data-lake-vs-data-warehouse)
15. [Glossário de Dados](#15-glossário-de-dados)

---

## 1. INTRODUÇÃO À ESTRATÉGIA DE DADOS

### 1.1 Objectivo da Estratégia de Dados

**Estratégia de Dados** define como os dados são coletados, armazenados, processados, retidos e analisados ao longo do seu ciclo de vida.

**Objectivo:** Garantir que os dados são:
- De alta qualidade (exactos, completos, consistentes)
- Retidos apenas pelo tempo necessário (GDPR compliance)
- Backup e recovery confiáveis
- Analisáveis para insights de negócio
- Governados de forma compliant (GDPR)

---

## 2. ARQUITECTURA DE DADOS

### 2.1 Arquitectura de Alto Nível

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              ARQUITECTURA DE DADOS (MVP)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  RAW LAYER (BRUTA)                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - raw_listings table (dados brutos dos portais)                    │   │
│  │ - JSON raw_data (dados originais não processados)                   │   │
│  │ - Retenção: 7 dias                                                 │   │
│  │ - Propósito: Debugging, reprocessamento                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  CLEAN LAYER (LIMPA)                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - clean_listings table (dados normalizados)                       │   │
│  │ - Campos normalizados (preço, área, quartos, etc.)               │   │
│  │ - Retenção: 90 dias                                                │   │
│  │ - Propósito: Valuation, Scoring, Analytics                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  ENRICHED LAYER (ENRIQUECIDA)                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - clean_listings (com geocoding, INE data, POIs)                  │   │
│  │ - Campos enriquecidos (lat/lon, freguesia, preço_m2_ine, etc.)    │   │
│  │ - Retenção: 90 dias                                                │   │
│  │ - Propósito: Valuation, Scoring                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  VALUATION LAYER (VALUATION)                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - valuations table (valor justo, discount, confiança)            │   │
│  │ - 8-model ensemble (XGBoost, Hedonic, Neural Network, CatBoost, Random Forest, Linear, Comps, INE)              │   │
│  │ - Retenção: 90 dias                                                │   │
│  │ - Propósito: Scoring, Analytics                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  SCORING LAYER (SCORING)                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - scores table (score 0-10, classificacao, rationale)            │   │
│  │ - 5 factores + red flags                                          │   │
│  │ - Retenção: 90 dias                                                │   │
│  │ - Propósito: Notification, Analytics                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  NOTIFICATION LAYER (NOTIFICAÇÃO)                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - notifications table (notificações enviadas)                     │   │
│  │ - Histórico de notificações                                        │   │
│  │ - Retenção: 90 dias                                                │   │
│  │ - Propósito: Analytics, Auditing                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  ANALYTICS LAYER (ANALYTICS)                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - price_history table (histórico de preços)                        │   │
│  │ - Métricas agregadas (preço médio por freguesia, etc.)            │   │
│  │ - Retenção: 365 dias (1 ano)                                      │   │
│  │ - Propósito: Dashboard, Analytics                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. FLUXO DE DADOS

### 3.1 Fluxo End-to-End

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              FLUXO DE DADOS END-TO-END                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SCRAPING → RAW LAYER                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1. SpiderManager.run_all_spiders()                                │   │
│  │ 2. IdealistaSpiderNodriver, ImovirtualSpiderNodriver, etc.       │   │
│  │ 3. Parse listings de portais imobiliários                         │   │
│  │ 4. Inserir em raw_listings (JSON raw_data)                        │   │
│  │ 5. Retenção: 7 dias                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  ETL → CLEAN LAYER                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1. PipelineETL.run()                                              │   │
│  │ 2. Normalizer (parse_price, parse_area, parse_rooms)              │   │
│  │ 3. Deduplicator (fingerprint, is_duplicate)                       │   │
│  │ 4. Geocoder (Nominatim, GeocodeCache)                             │   │
│  │ 5. Enricher (INE data, POIs)                                      │   │
│  │ 6. Validator (validar campos, ranges)                             │   │
│  │ 7. Inserir em clean_listings                                      │   │
│  │ 8. Retenção: 90 dias                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  VALUATION → VALUATION LAYER                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1. ValuationEngine.valuate()                                     │   │
│  │ 2. HedonicModel.predict()                                         │   │
│  │ 3. CompsEngine.find_comparables()                                 │   │
│  │ 4. INEClient.get_freguesia_data()                                │   │
│  │ 5. XGBoostModel.predict() (opcional)                              │   │
│  │ 6. WeightedEnsemble.combine()                                     │   │
│  │ 7. Inserir em valuations                                           │   │
│  │ 8. Retenção: 90 dias                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  SCORING → SCORING LAYER                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1. ScoringEngine.score()                                          │   │
│  │ 2. ScoreDiscountCalculator.calculate()                             │   │
│  │ 3. ScoreLocationCalculator.calculate()                            │   │
│  │ 4. ScoreConditionCalculator.calculate()                           │   │
│  │ 5. ScoreLiquidityCalculator.calculate()                            │   │
│  │ 6. ScoreFreshnessCalculator.calculate()                             │   │
│  │ 7. RedFlagsDetector.detect()                                       │   │
│  │ 8. WeightedScoreCalculator.calculate()                             │   │
│  │ 9. RationaleGenerator.generate()                                   │   │
│  │ 10. Inserir em scores                                             │   │
│  │ 11. Retenção: 90 dias                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  NOTIFICATION → NOTIFICATION LAYER                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1. NotificationEngine.notify_top_opportunities()                 │   │
│  │ 2. OpportunitySelector.select()                                    │   │
│  │ 3. MessageFormatter.format_opportunity_message()                  │   │
│  │ 4. TelegramBot.send_message()                                     │   │
│  │ 5. Inserir em notifications                                       │   │
│  │ 6. Retenção: 90 dias                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  ANALYTICS → ANALYTICS LAYER                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1. Agregar price_history (diário)                                 │   │
│  │ 2. Calcular métricas (preço médio por freguesia, etc.)            │   │
│  │ 3. Inserir em price_history                                      │   │
│  │ 4. Retenção: 365 dias (1 ano)                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. DATA QUALITY

### 4.1 Dimensões de Data Quality

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              DIMENSÕES DE DATA QUALITY                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. ACCURACY (EXACTIDÃO)                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Preço: deve ser > 0 e razoável (não 0.01€ nem 100M€)            │   │
│  │ - Área: deve ser > 0 e razoável (não 1 m² nem 1000 m²)            │   │
│  │ - Quartos: deve ser ≥ 0 e razoável (não 100 quartos)              │   │
│  │ - Lat/Lon: deve estar dentro de Portugal                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  2. COMPLETENESS (COMPLETITUDE)                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Preço: obrigatório                                               │   │
│  │ - Área: obrigatório                                                │   │
│  │ - Quartos: opcional (mas desejável)                                │   │
│  │ - Morada: opcional (mas desejável)                                │   │
│  │ - Estado: opcional (mas desejável)                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  3. CONSISTENCY (CONSISTÊNCIA)                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Preço pedido vs preço por m² razoável                           │   │
│  │ - Quartos vs área razoável (ex: T3 não tem 10 m²)                  │   │
│  │ - Freguesia vs lat/lon consistente                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  4. TIMELINESS (TEMPORALIDADE)                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Scrape timestamp deve ser recente (últimas 24 horas)            │   │
│  │ - Listings antigos devem ser marcados (freshness score baixo)     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  5. VALIDITY (VALIDADE)                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Tipo de dados correcto (preço é float, quartos é int)            │   │
│  │ - Formato correcto (preço não tem "€", área não tem "m²")          │   │
│  │ - Ranges correctos (quartos ≥ 0, área > 0)                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  6. UNIQUENESS (UNICIDADE)                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Sem duplicados (fingerprint único)                              │   │
│  │ - source_id único por source_portal                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Implementação de Data Quality

```python
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class DataQualityChecker:
    """Verificador de qualidade de dados."""
    
    def __init__(self):
        self.quality_rules = {
            'accuracy': self._check_accuracy,
            'completeness': self._check_completeness,
            'consistency': self._check_consistency,
            'timeliness': self._check_timeliness,
            'validity': self._check_validity,
            'uniqueness': self._check_uniqueness
        }
    
    def check_listing(self, listing: Dict) -> Tuple[bool, List[str]]:
        """Verifica qualidade de listing."""
        errors = []
        
        for dimension, rule in self.quality_rules.items():
            is_valid, dimension_errors = rule(listing)
            if not is_valid:
                errors.extend(dimension_errors)
        
        return (len(errors) == 0, errors)
    
    def _check_accuracy(self, listing: Dict) -> Tuple[bool, List[str]]:
        """Verifica exactidão."""
        errors = []
        
        # Preço
        if 'preco_pedido' in listing:
            if listing['preco_pedido'] <= 0:
                errors.append(f"Preço deve ser > 0: {listing['preco_pedido']}")
            elif listing['preco_pedido'] > 10000000:  # 10M€
                errors.append(f"Preço suspeito > 10M€: {listing['preco_pedido']}")
        
        # Área
        if 'area_util_m2' in listing:
            if listing['area_util_m2'] <= 0:
                errors.append(f"Área deve ser > 0: {listing['area_util_m2']}")
            elif listing['area_util_m2'] > 1000:  # 1000 m²
                errors.append(f"Área suspeita > 1000 m²: {listing['area_util_m2']}")
        
        return (len(errors) == 0, errors)
    
    def _check_completeness(self, listing: Dict) -> Tuple[bool, List[str]]:
        """Verifica completude."""
        errors = []
        
        # Campos obrigatórios
        required_fields = ['preco_pedido', 'area_util_m2']
        for field in required_fields:
            if field not in listing or listing[field] is None:
                errors.append(f"Campo obrigatório ausente: {field}")
        
        return (len(errors) == 0, errors)
    
    def _check_consistency(self, listing: Dict) -> Tuple[bool, List[str]]:
        """Verifica consistência."""
        errors = []
        
        # Preço por m²
        if 'preco_pedido' in listing and 'area_util_m2' in listing:
            if listing['area_util_m2'] > 0:
                price_per_m2 = listing['preco_pedido'] / listing['area_util_m2']
                if price_per_m2 < 100:  # < 100€/m²
                    errors.append(f"Preço por m² suspeito < 100€: {price_per_m2}")
                elif price_per_m2 > 10000:  # > 10000€/m²
                    errors.append(f"Preço por m² suspeito > 10000€: {price_per_m2}")
        
        # Quartos vs Área
        if 'quartos' in listing and 'area_util_m2' in listing:
            if listing['quartos'] > 0 and listing['area_util_m2'] < (listing['quartos'] * 10):
                errors.append(f"Área insuficiente para {listing['quartos']} quartos")
        
        return (len(errors) == 0, errors)
    
    def _check_timeliness(self, listing: Dict) -> Tuple[bool, List[str]]:
        """Verifica temporalidade."""
        errors = []
        
        if 'scrape_timestamp' in listing:
            from datetime import datetime, timedelta
            scrape_time = datetime.fromisoformat(listing['scrape_timestamp'])
            now = datetime.now()
            
            if (now - scrape_time) > timedelta(hours=24):
                errors.append(f"Listing antigo (> 24 horas): {listing['scrape_timestamp']}")
        
        return (len(errors) == 0, errors)
    
    def _check_validity(self, listing: Dict) -> Tuple[bool, List[str]]:
        """Verifica validade."""
        errors = []
        
        # Tipo de dados
        if 'preco_pedido' in listing:
            if not isinstance(listing['preco_pedido'], (int, float)):
                errors.append(f"Preço deve ser numérico: {type(listing['preco_pedido'])}")
        
        if 'quartos' in listing:
            if not isinstance(listing['quartos'], int):
                errors.append(f"Quartos deve ser int: {type(listing['quartos'])}")
        
        return (len(errors) == 0, errors)
    
    def _check_uniqueness(self, listing: Dict) -> Tuple[bool, List[str]]:
        """Verifica unicidade."""
        errors = []
        
        # Esta verificação é feita pelo Deduplicator
        # Aqui apenas verificamos se há source_id e source_portal
        if 'source_id' not in listing or not listing['source_id']:
            errors.append("source_id ausente")
        
        if 'source_portal' not in listing or not listing['source_portal']:
            errors.append("source_portal ausente")
        
        return (len(errors) == 0, errors)
```

---

## 5. DATA RETENTION

### 5.1 Política de Retenção

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              POLÍTICA DE RETENÇÃO DE DADOS                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  RAW LAYER (RAW_LISTINGS)                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Retenção: 7 dias                                                   │   │
│  │ Razão: Dados brutos apenas para debug e reprocessamento           │   │
│  │ Política: DELETE FROM raw_listings WHERE scrape_timestamp < datetime('now', '-7 days')│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CLEAN LAYER (CLEAN_LISTINGS)                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Retenção: 90 dias                                                  │   │
│  │ Razão: Dados para valuation e scoring                               │   │
│  │ Política: DELETE FROM clean_listings WHERE scrape_timestamp < datetime('now', '-90 days')│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  VALUATION LAYER (VALUATIONS)                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Retenção: 90 dias                                                  │   │
│  │ Razão: Valuations para scoring e analytics                        │   │
│  │ Política: DELETE FROM valuations WHERE valuation_timestamp < datetime('now', '-90 days')│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SCORING LAYER (SCORES)                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Retenção: 90 dias                                                  │   │
│  │ Razão: Scores para notification e analytics                        │   │
│  │ Política: DELETE FROM scores WHERE score_timestamp < datetime('now', '-90 days')│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  NOTIFICATION LAYER (NOTIFICATIONS)                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Retenção: 90 dias                                                  │   │
│  │ Razão: Histórico de notificações para auditing                    │   │
│  │ Política: DELETE FROM notifications WHERE notification_timestamp < datetime('now', '-90 days')│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ANALYTICS LAYER (PRICE_HISTORY)                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Retenção: 365 dias (1 ano)                                        │   │
│  │ Razão: Histórico de preços para analytics de longo prazo          │   │
│  │ Política: DELETE FROM price_history WHERE date < date('now', '-365 days')│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  LOGS                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Retenção: 30 dias                                                  │   │
│  │ Razão: Logs para debugging e auditing                             │   │
│  │ Política: Loguru rotation automática (30 dias)                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Implementação de Data Retention

```python
from database.repository import DatabaseRepository
import logging

logger = logging.getLogger(__name__)

class DataRetentionManager:
    """Gestor de retenção de dados."""
    
    def __init__(self, database_repository: DatabaseRepository):
        self.db = database_repository
    
    async def cleanup_raw_listings(self):
        """Limpa raw_listings antigos (7 dias)."""
        logger.info("DataRetentionManager: Cleanup raw_listings (7 dias)")
        
        query = """
            DELETE FROM raw_listings 
            WHERE scrape_timestamp < datetime('now', '-7 days')
        """
        
        count = await self.db.execute(query)
        logger.info(f"DataRetentionManager: {count} raw_listings deletados")
    
    async def cleanup_clean_listings(self):
        """Limpa clean_listings antigos (90 dias)."""
        logger.info("DataRetentionManager: Cleanup clean_listings (90 dias)")
        
        query = """
            DELETE FROM clean_listings 
            WHERE scrape_timestamp < datetime('now', '-90 days')
        """
        
        count = await self.db.execute(query)
        logger.info(f"DataRetentionManager: {count} clean_listings deletados")
    
    async def cleanup_valuations(self):
        """Limpa valuations antigos (90 dias)."""
        logger.info("DataRetentionManager: Cleanup valuations (90 dias)")
        
        query = """
            DELETE FROM valuations 
            WHERE valuation_timestamp < datetime('now', '-90 days')
        """
        
        count = await self.db.execute(query)
        logger.info(f"DataRetentionManager: {count} valuations deletados")
    
    async def cleanup_scores(self):
        """Limpa scores antigos (90 dias)."""
        logger.info("DataRetentionManager: Cleanup scores (90 dias)")
        
        query = """
            DELETE FROM scores 
            WHERE score_timestamp < datetime('now', '-90 days')
        """
        
        count = await self.db.execute(query)
        logger.info(f"DataRetentionManager: {count} scores deletados")
    
    async def cleanup_notifications(self):
        """Limpa notifications antigas (90 dias)."""
        logger.info("DataRetentionManager: Cleanup notifications (90 dias)")
        
        query = """
            DELETE FROM notifications 
            WHERE notification_timestamp < datetime('now', '-90 days')
        """
        
        count = await self.db.execute(query)
        logger.info(f"DataRetentionManager: {count} notifications deletados")
    
    async def cleanup_price_history(self):
        """Limpa price_history antigo (365 dias)."""
        logger.info("DataRetentionManager: Cleanup price_history (365 dias)")
        
        query = """
            DELETE FROM price_history 
            WHERE date < date('now', '-365 days')
        """
        
        count = await self.db.execute(query)
        logger.info(f"DataRetentionManager: {count} price_history deletados")
    
    async def run_cleanup(self):
        """Executa cleanup completo."""
        logger.info("DataRetentionManager: Iniciando cleanup completo")
        
        await self.cleanup_raw_listings()
        await self.cleanup_clean_listings()
        await self.cleanup_valuations()
        await self.cleanup_scores()
        await self.cleanup_notifications()
        await self.cleanup_price_history()
        
        logger.info("DataRetentionManager: Cleanup completo")
```

---

## 6. BACKUP STRATEGY

### 6.1 Estratégia de Backup

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              ESTRATÉGIA DE BACKUP                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FASE 1: LOCAL (MVP)                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Backup diário: SQLite database (realestate.db)                     │   │
│  │ Backup diário: Scheduler database (scheduler.db)                   │   │
│  │ Backup semanal: Logs (30 dias)                                     │   │
│  │ Retenção: 30 dias                                                  │   │
│  │ Local: data/backups/                                               │   │
│  │ Automático: Task Scheduler (Windows)                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 2: VPS (PRODUÇÃO)                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Backup diário: PostgreSQL database (pg_dump)                       │   │
│  │ Backup diário: Scheduler database (SQLite)                         │   │
│  │ Backup semanal: Logs (30 dias)                                     │   │
│  │ Retenção: 30 dias                                                  │   │
│  │ Local: /var/backups/                                              │   │
│  │ Offsite: S3 / Azure Blob (opcional)                                │   │
│  │ Automático: Cron job                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 3: CLOUD-NATIVE                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Backup diário: PostgreSQL (RDS automated backups)                 │   │
│  │ Backup diário: Scheduler database (SQLite → S3)                     │   │
│  │ Backup semanal: Logs (Loki → S3)                                   │   │
│  │ Retenção: 30 dias                                                  │   │
│  │ Local: S3 / Azure Blob                                             │   │
│  │ Offsite: Multi-region (opcional)                                   │   │
│  │ Automático: RDS automated backups + Lambda function               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Implementação de Backup (Local)

```python
import shutil
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BackupManager:
    """Gestor de backup."""
    
    def __init__(self, db_path: str = "data/db/realestate.db"):
        self.db_path = Path(db_path)
        self.backup_dir = Path("data/backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    def backup_database(self) -> Path:
        """Backup da database."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_dir / f"realestate_{timestamp}.db"
        
        shutil.copy2(self.db_path, backup_path)
        logger.info(f"BackupManager: Backup criado em {backup_path}")
        
        return backup_path
    
    def cleanup_old_backups(self, retention_days: int = 30):
        """Limpa backups antigos."""
        cutoff_date = datetime.now().timestamp() - (retention_days * 24 * 60 * 60)
        
        for backup_file in self.backup_dir.glob("realestate_*.db"):
            if backup_file.stat().st_mtime < cutoff_date:
                backup_file.unlink()
                logger.info(f"BackupManager: Backup antigo removido: {backup_file}")
```

---

## 7. DATA ARCHIVAL

### 7.1 Estratégia de Archival

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              ESTRATÉGIA DE DATA ARCHIVAL                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DATA ARCHIVAL (ARQUIVAMENTO)                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Dados antigos (> 90 dias) são arquivados em vez de deletados       │   │
│  │ Archival: Compressão (gzip)                                         │   │
│  │ Local: data/archive/                                               │   │
│  │ Retenção: 1 ano                                                   │   │
│  │ Propósito: Analytics históricos, compliance                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PROCESSO DE ARCHIVAL:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1. Exportar dados antigos para CSV                                 │   │
│  │ 2. Comprimir CSV com gzip                                          │   │
│  │ 3. Guardar em data/archive/                                        │   │
│  │ 4. Deletar dados da database                                     │   │
│  │ 5. Retirar archival após 1 ano                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. DATA ANALYTICS

### 8.1 Métricas de Analytics

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              MÉTRICAS DE DATA ANALYTICS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MÉTRICAS DE MERCADO:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Preço médio por freguesia                                          │   │
│  │ - Preço médio por tipo (T1, T2, T3, T4, T5)                          │   │
│  │ - Preço médio por estado (Novo, Renovado, Usado)                    │   │
│  │ - Volume de listings por freguesia                                    │   │
│  │ - Tendência de preços (30 dias, 90 dias, 365 dias)                 │   │
│  │ - Discount médio por freguesia                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MÉTRICAS DE SCRAPING:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Listings por portal por dia                                       │   │
│  │ - Taxa de sucesso por portal                                         │   │
│  │ - Tempo de scraping por portal                                       │   │
│  │ - Taxa de erro por portal                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MÉTRICAS DE VALUATION:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - MAE (Mean Absolute Error)                                          │   │
│  │ - RMSE (Root Mean Square Error)                                     │   │
│  │ - Confiança média                                                    │   │
│  │ - Discount médio                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MÉTRICAS DE SCORING:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Distribuição de scores (0-10)                                     │   │
│  │ - % de Imperdíveis (score ≥ 8)                                       │   │
│  │ - % de Muito Bons (score 7-7.9)                                     │   │
│  │ - % de Bons (score 6-6.9)                                            │   │
│  │ - % de Médios (score 4-5.9)                                          │   │
│  │ - % de Fracos (score < 4)                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. DATA GOVERNANCE

### 9.1 Princípios de Data Governance

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              PRINCÍPIOS DE DATA GOVERNANCE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. DATA OWNERSHIP                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Proprietário dos dados: Utilizador (dado que sistema é local)    │   │
│  │ Responsável por: Acesso, retenção, backup, privacy               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  2. DATA STEWARDSHIP                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Data Steward: Desenvolvedor (gestão técnica)                      │   │
│  │ Responsável por: Data quality, integridade, consistência           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  3. DATA QUALITY                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Data Quality Checker: Verifica qualidade antes de inserir         │   │
│  │ Métricas: Accuracy, Completeness, Consistency, Timeliness        │   │
│  │ SLA: Data quality ≥ 95%                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  4. DATA PRIVACY                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ GDPR Compliance: Dados pessoais não são guardados intencionalmente│   │
│  │ Local-First: Dados ficam localmente no PC do utilizador            │   │
│  │ Right to be Forgotten: Implementado (DELETE endpoint)             │   │
│  │ Data Retention: 90 dias (configurável)                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  5. DATA SECURITY                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Encriptação: Database encriptado (Fernet)                           │   │
│  │ Secrets Management: .env (não no git)                              │   │
│  │ Access Control: Local deployment (acesso apenas do utilizador)    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  6. DATA LINEAGE                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Rastreio: Cada listing tem scrape_timestamp                         │   │
│  │ Audit trail: Cada alteração é logged                               │   │
│  │ Versioning: Database migrations versionadas                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. DATA PRIVACY

### 10.1 GDPR Compliance

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              GDPR COMPLIANCE                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DADOS PESSOAIS:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ O sistema NÃO guarda dados pessoais intencionalmente.               │   │
│  │ Apenas dados públicos dos portais imobiliários.                   │   │
│  │ Se dados pessoais estiverem presentes, são encriptados.            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DADOS NÃO PESSOAIS:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Preço, área, quartos                                               │   │
│  │ - Estado, ano construção, certificado energético                       │   │
│  │ - Lat/lon (coordenadas)                                              │   │
│  │ - Freguesia, concelho                                                │   │
│  │ - URLs dos listings                                                 │   │
│  │                                                                     │   │
│  │ Estes dados são públicos nos portais e não são dados pessoais.     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  RIGHT TO BE FORGOTTEN:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Utilizador pode pedir eliminação de dados                          │   │
│  │ Endpoint DELETE /listings/{id}                                      │   │
│  │ Confirmação de identidade (opcional para local deployment)          │   │
│  │ Eliminação permanente (hard delete)                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DATA RETENTION:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Dados guardados por 90 dias (configurável)                         │   │
│  │ Após 90 dias, dados são eliminados automaticamente                │   │
│  │ Logs guardados por 30 dias                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  LOCAL-FIRST APPROACH:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Dados ficam localmente no PC do utilizador                         │   │
│  │ Nada é enviado para cloud                                         │   │
│  │ Utilizador tem controlo total dos dados                              │   │
│  │ Compliance por design                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 11. DATA LINEAGE

### 11.1 Rastreio de Dados

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              DATA LINEAGE (RASTREIO DE DADOS)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  RAW LISTING → CLEAN LISTING                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ raw_listing.id → clean_listing.raw_id                               │   │
│  │ scrape_timestamp → scrape_timestamp                                 │   │
│  │ source_portal → source_portal                                       │   │
│  │ source_id → source_id                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CLEAN LISTING → VALUATION                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ clean_listing.id → valuation.listing_id                            │   │
│  │ valuation_timestamp → datetime.now()                                │   │
│  │ valuation_method → "hedonic+comps+ine"                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CLEAN LISTING + VALUATION → SCORING                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ clean_listing.id → score.listing_id                               │   │
│  │ valuation.id → score.valuation_id                                  │   │
│  │ score_timestamp → datetime.now()                                     │   │
│  │ score_method → "5_factors"                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SCORE → NOTIFICATION                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ score.id → notification.score_id                                    │   │
│  │ notification_timestamp → datetime.now()                            │   │
│  │ notification_method → "telegram"                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 12. DATA CATALOG

### 12.1 Catálogo de Dados

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              DATA CATALOG (CATÁLOGO DE DADOS)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TABELA: RAW_LISTINGS                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Descrição: Dados brutos dos portais imobiliários                  │   │
│  │ Colunas: id, source_portal, source_id, source_url, scrape_timestamp, raw_data│   │
│  │ Retenção: 7 dias                                                   │   │
│  │ Propósito: Debugging, reprocessamento                              │   │
│  │ Owner: Data Steward                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TABELA: CLEAN_LISTINGS                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Descrição: Dados normalizados                                      │   │
│  │ Colunas: id, titulo, preco_pedido, area_util_m2, quartos, etc.    │   │
│  │ Retenção: 90 dias                                                  │   │
│  │ Propósito: Valuation, Scoring, Analytics                          │   │
│  │ Owner: Data Steward                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TABELA: VALUATIONS                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Descrição: Valuations de listings                                  │   │
│  │ Colunas: id, listing_id, valor_justo, discount, confianca, etc.  │   │
│  │ Retenção: 90 dias                                                  │   │
│  │ Propósito: Scoring, Analytics                                      │   │
│  │ Owner: Data Steward                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TABELA: SCORES                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Descrição: Scores de listings (0-10)                               │   │
│  │ Colunas: id, listing_id, score_total, classificacao, rationale, etc.│   │
│  │ Retenção: 90 dias                                                  │   │
│  │ Propósito: Notification, Analytics                                │   │
│  │ Owner: Data Steward                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TABELA: NOTIFICATIONS                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Descrição: Histórico de notificações                              │   │
│  │ Colunas: id, score_id, chat_id, message, notification_timestamp, etc.│   │
│  │ Retenção: 90 dias                                                  │   │
│  │ Propósito: Analytics, Auditing                                    │   │
│  │ Owner: Data Steward                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 13. DATA MIGRATION

### 13.1 Estratégia de Migração

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              ESTRATÉGIA DE DATA MIGRAÇÃO                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MIGRAÇÃO SQLITE → POSTGRESQL                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1. Exportar SQLite para CSV                                        │   │
│  │ 2. Importar CSV para PostgreSQL                                   │   │
│  │ 3. Verificar dados migrados                                        │   │
│  │ 4. Testar queries em PostgreSQL                                    │   │
│  │ 5. Cutover (parar SQLite, iniciar PostgreSQL)                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MIGRAÇÃO POSTGRESQL → RDS (MANAGED SERVICE)                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1. Criar RDS instance                                             │   │
│  │ 2. Exportar PostgreSQL local para SQL dump                        │   │
│  │ 3. Importar SQL dump para RDS                                      │   │
│  │ 4. Verificar dados migrados                                        │   │
│  │ 5. Cutover (parar PostgreSQL local, iniciar RDS)                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 14. DATA LAKE VS DATA WAREHOUSE

### 14.1 Comparação

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              DATA LAKE VS DATA WAREHOUSE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DATA LAKE:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Armazena dados brutos (raw)                                        │   │
│  │ - Schema-on-read (flexível)                                        │   │
│  │ - Baixo custo (S3, Azure Blob)                                      │   │
│  │ - Propósito: Data science, machine learning                        │   │
│  │ - Não necessário para MVP (SQLite é suficiente)                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DATA WAREHOUSE:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Armazena dados processados (structured)                          │   │
│  │ - Schema-on-write (rígido)                                         │   │
│  │ - Alto custo (Redshift, Snowflake)                                 │   │
│  │ - Propósito: Business Intelligence, analytics                    │   │
│  │ - Não necessário para MVP (PostgreSQL é suficiente)              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DECISÃO:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ MVP: SQLite (data warehouse + data lake em um)                    │   │
│  │ Produção: PostgreSQL (data warehouse)                             │   │
│  │ Cloud-Native: PostgreSQL + S3 (data warehouse + data lake)        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 15. GLOSSÁRIO DE DADOS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│            GLOSSÁRIO DE DADOS                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DATA: Dados (informação armazenada)                                 │
│                                                                             │
│  DATA QUALITY: Qualidade de dados (exactidão, completude, etc.)    │
│                                                                             │
│  DATA RETENTION: Retenção de dados (tempo de guarda)                 │
│                                                                             │
│  DATA ARCHIVAL: Archival de dados (arquivamento de dados antigos)   │
│                                                                             │
│  BACKUP: Backup (cópia de segurança)                                    │
│                                                                             │
│  RESTORE: Restore (restauração de backup)                               │
│                                                                             │
│  DATA GOVERNANCE: Governança de dados (gestão de dados)             │
│                                                                             │
│  DATA OWNERSHIP: Propriedade de dados (dono dos dados)               │
│                                                                             │
│  DATA STEWARDSHIP: Stewardship de dados (gestor técnico)             │
│                                                                             │
│  DATA PRIVACY: Privacidade de dados (proteção de dados pessoais)   │
│                                                                             │
│  GDPR: General Data Protection Regulation (regulamento UE)           │
│                                                                             │
│  DATA LINEAGE: Linhagem de dados (rastreio de origem)                │
│                                                                             │
│  DATA CATALOG: Catálogo de dados (inventário de dados)               │
│                                                                             │
│  DATA MIGRATION: Migração de dados (mover de um sistema para outro)│   │
│                                                                             │
│  DATA LAKE: Data lake (armazenamento de dados brutos)                │
│                                                                             │
│  DATA WAREHOUSE: Data warehouse (armazenamento de dados processados) │   │
│                                                                             │
│  SCHEMA-ON-READ: Schema-on-read (definido ao ler)                   │
│                                                                             │
│  SCHEMA-ON-WRITE: Schema-on-write (definido ao escrever)             │
│                                                                             │
│  RAW DATA: Dados brutos (não processados)                             │
│                                                                             │
│  CLEAN DATA: Dados limpos (normalizados)                              │
│                                                                             │
│  ENRICHED DATA: Dados enriquecidos (com dados adicionais)          │
│                                                                             │
│  AGGREGATED DATA: Dados agregados (métricas, sumários)               │
│                                                                             │
│  TIME SERIES: Série temporal (dados ao longo do tempo)                │
│                                                                             │
│  ANOMALY DETECTION: Detecção de anomalias (outliers)                │
│                                                                             │
│  DATA PROFILING: Profiling de dados (análise de qualidade)          │
│                                                                             │
│  DATA VALIDATION: Validação de dados (verificação de qualidade)      │
│                                                                             │
│  DATA CLEANSING: Limpeza de dados (remoção de erros, duplicados)    │
│                                                                             │
│  DATA TRANSFORMATION: Transformação de dados (ETL)                   │
│                                                                             │
│  DATA INTEGRATION: Integração de dados (combinação de fontes)      │
│                                                                             │
│  DATA CONSISTENCY: Consistência de dados (uniformidade)              │
│                                                                             │
│  DATA ACCURACY: Exactidão de dados (correcção)                       │
│                                                                             │
│  DATA COMPLETENESS: Completude de dados (campos preenchidos)        │
│                                                                             │
│  DATA TIMELINESS: Temporalidade de dados (actualidade)                │
│                                                                             │
│  DATA VALIDITY: Validade de dados (formato, ranges)                  │
│                                                                             │
│  DATA UNIQUENESS: Unicidade de dados (sem duplicados)                │
│                                                                             │
│  METADATA: Metadados (dados sobre dados)                             │
│                                                                             │
│  MASTER DATA: Master data (dados mestres, golden record)             │
│                                                                             │
│  REFERENCE DATA: Reference data (dados de referência)                 │
│                                                                             │
│  TRANSACTIONAL DATA: Dados transaccionais (operações)                │
│                                                                             │
│  ANALYTICAL DATA: Dados analíticos (agregados, métricas)            │
│                                                                             │
│  HISTORICAL DATA: Dados históricos (arquivados)                      │
│                                                                             │
│  REAL-TIME DATA: Dados em tempo real (streaming)                     │
│                                                                             │
│  BATCH DATA: Dados em batch (processados em lotes)                    │
│                                                                             │
│  COLD DATA: Cold data (pouco acessados)                               │
│                                                                             │
│  HOT DATA: Hot data (frequentemente acessados)                        │
│                                                                             │
│  WARM DATA: Warm data (moderadamente acessados)                       │
│                                                                             │
│  DATA TIERING: Tiering de dados (hot, warm, cold)                   │
│                                                                             │
│  DATA LIFECYCLE: Ciclo de vida dos dados (criação → archival → delete)│   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*Fim do Documento 19 — Estratégia de Dados*
