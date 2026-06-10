# ARQUITECTURA DO SISTEMA — REAL ESTATE OPPORTUNITY ENGINE
## Detalhamento Completo de Componentes, Fluxos e Integrações

> **Este documento:** Arquitectura detalhada do sistema Real Estate Opportunity Engine  
> **Objectivo:** Fornecer especificação completa da arquitectura para IA implementar  
> **Linhas:** 1500+ linhas de documentação detalhada  
> **Versão:** 5.0 (Actualizado com Volume 13 e Nodriver 2026)

---

## ÍNDICE

1. [Visão Geral da Arquitectura](#1-visão-geral-da-arquitectura)
2. [Princípios de Design](#2-princípios-de-design)
3. [Camadas do Sistema](#3-camadas-do-sistema)
4. [Componentes Detalhados](#4-componentes-detalhados)
5. [Fluxo de Dados](#5-fluxo-de-dados)
6. [Integração entre Componentes](#6-integração-entre-componentes)
7. [Arquitectura de Banco de Dados](#7-arquitectura-de-banco-de-dados)
8. [Arquitectura de Scheduler](#8-arquitectura-de-scheduler)
9. [Arquitectura de Monitorização](#9-arquitectura-de-monitorização)
10. [Diagramas de Sequência](#10-diagramas-de-sequência)
11. [Padrões de Design](#11-padrões-de-design)
12. [Considerações de Performance](#12-considerações-de-performance)
13. [Considerações de Segurança](#13-considerações-de-segurança)
14. [Roadmap de Escalabilidade](#14-roadmap-de-escalabilidade)
15. [Glossário de Arquitectura](#15-glossário-de-arquitectura)

---

## 1. VISÃO GERAL DA ARQUITECTURA

### 1.1 Arquitectura de Alto Nível

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              ARQUITECTURA DE ALTO NÍVEL (LOCAL-FIRST)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         SCRAPING LAYER                                │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │ Nodriver Spiders (8 portais cobertos por 12 spiders)        │  │   │
│  │  │ - Nacionais: Idealista, Imovirtual, Casa Sapo, OLX           │  │   │
│  │  │ - Regionais: ERA, REMAX, Century21, Supercasa                │  │   │
│  │  │ - Nodriver + warm-up + proxies                                │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  │                              │                                        │   │
│  │                              ▼                                        │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │ Raw Listings (JSON)                                           │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                          ETL LAYER                                   │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │ Normalizer → Deduplicator → Geocoder → Enricher → Validator   │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  │                              │                                        │   │
│  │                              ▼                                        │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │ Clean Listings (SQLite/PostgreSQL)                             │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        VALUATION LAYER                               │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │ 8 Modelos ML Ensemble: XGBoost, Hedonic, Neural Network,      │  │   │
│  │  │ CatBoost, RF, Linear, Comps, INE → Meta-Learning Ensemble    │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  │                              │                                        │   │
│  │                              ▼                                        │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │ Valuations (SQLite/PostgreSQL)                                 │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         SCORING LAYER                                │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │ Discount (30%) + Location (25%) + Condition (15%) +           │  │   │
│  │  │ Liquidity (15%) + Freshness (15%) → Total Score (0-10)        │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  │                              │                                        │   │
│  │                              ▼                                        │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │ Scores (SQLite/PostgreSQL)                                     │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      NOTIFICATION LAYER                              │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │ Opportunity Selector → Telegram Bot → Notification History      │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       DASHBOARD LAYER                                │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │ Streamlit Dashboard (Overview, Search, Config, etc.)            │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      ORCHESTRATION LAYER                             │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │ APScheduler (Jobs agendados)                                    │  │   │
│  │  │ - Scraping job (cada 30 minutos)                               │  │   │
│  │  │ - ETL job (cada 32 minutos)                                    │  │   │
│  │  │ - Valuation job (cada 35 minutos)                              │  │   │
│  │  │ - Scoring job (cada 38 minutos)                                │  │   │
│  │  │ - Notification job (cada 60 minutos)                           │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      MONITORING LAYER                                │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │ Loguru (logging) + Health Checks + Metrics                     │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      DATABASE LAYER                                  │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │ SQLite (MVP) / PostgreSQL (Produção)                           │  │   │
│  │  │ Tables: raw_listings, clean_listings, valuations, scores,     │  │   │
│  │  │         price_history, notifications, config                   │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Paradigma Arquitectural

**Paradigma:** Event-Driven Architecture (EDA) com Batch Processing

**Justificativa:**
- Scraping é por natureza event-driven (novo listing publicado)
- ETL, Valuation e Scoring são batch processing (processam lotes)
- Dashboard é on-demand (utilizador solicita dados)
- Notification é event-driven (score ≥ 8)

**Padrões:**
- **Producer-Consumer:** Spiders produzem dados, ETL consome
- **Pipeline:** ETL → Valuation → Scoring (pipeline sequencial)
- **Observer:** Scheduler observa tempo e dispara jobs
- **Repository:** Database como repositório central

---

## 2. PRINCÍPIOS DE DESIGN

### 2.1 Princípios Core

**Princípio 1: Local-First**
- Dados nunca saem do PC
- GDPR compliance por design
- Custo zero de infraestrutura
- Privacidade total

**Princípio 2: Modularidade**
- Cada camada independente
- Fácil testar e manter
- Fácil substituir componentes
- Baixo acoplamento

**Princípio 3: Escalabilidade**
- Arquitectura desenhada para escalar
- Fase 1 (MVP) → Fase 4 (Cloud-native)
- Sem rewrites major
- Horizontal scaling possível

**Princípio 4: Observabilidade**
- Logging estruturado
- Health checks
- Métricas e alertas
- Tracing (quando escalado)

**Princípio 5: Simplicidade**
- KISS (Keep It Simple, Stupid)
- Ferramentas maduras e estáveis
- Sem over-engineering
- MVP primeiro, optimização depois

### 2.2 Princípios SOLID

**S - Single Responsibility:**
- Cada classe/módulo tem uma única responsabilidade
- Ex: Normalizer só normaliza, Geocoder só geocodifica

**O - Open/Closed:**
- Aberto para extensão, fechado para modificação
- Ex: Adicionar novo spider não modifica SpiderManager

**L - Liskov Substitution:**
- Subclasses podem substituir superclasses
- Ex: IdealistaSpider pode substituir BaseSpider

**I - Interface Segregation:**
- Interfaces pequenas e específicas
- Ex: IScrapable, IETL, IValuation, IScorable

**D - Dependency Inversion:**
- Depender de abstracções, não de implementações
- Ex: Depender de IDatabase, não de SQLite/PostgreSQL

---

## 3. CAMADAS DO SISTEMA

### 3.1 Layer 1: Scraping

**Responsabilidade:** Extrair dados de 8 portais imobiliários (Nacionais + Regionais) com 12 spiders

**Componentes:**
- Nodriver Spiders (8 portais cobertos por 12 spiders)
- ProxyManager (residential proxies opcional)
- StealthManager (Nodriver CDP directo)
- RateLimiter (rate limiting por portal)
- CircuitBreaker (pausa se falhas consecutivas)

**Input:**
- URLs dos portais (start_urls)
- Configurações (user-agent, viewport, proxy)

**Output:**
- Raw Listings (JSON)
- Inseridos em raw_listings table

**Performance:**
- Taxa de sucesso: 60-70% (com Nodriver)
- Tempo scraping: < 15 minutos para todos os portais
- Volume: 5000-8000 listings/dia (Portugal)

### 3.2 Layer 2: ETL

**Responsabilidade:** Transformar dados brutos em dados normalizados

**Componentes:**
- Normalizer (normaliza campos)
- Deduplicator (detecta duplicados)
- Geocoder (geocodifica morada → lat/lon)
- Enricher (enrich com dados INE e POIs)
- Validator (valida integridade)

**Input:**
- Raw Listings (raw_listings table)

**Output:**
- Clean Listings (clean_listings table)

**Performance:**
- Tempo ETL: < 5 minutos para 1000 listings
- Taxa de erro: < 5%

### 3.3 Layer 3: Valuation

**Responsabilidade:** Calcular valor justo estimado para cada listing

**Componentes:**
- 8 Modelos ML Ensemble: XGBoost, Hedonic, Neural Network, CatBoost, RF, Linear, Comps, INE
- Meta-Learning (optimização dinâmica de pesos)
- Weighted Ensemble (combina 8 modelos)
- Target R² > 0.85

**Input:**
- Clean Listings (clean_listings table)

**Output:**
- Valuations (valuations table)
- Valor justo estimado (8 modelos)
- Intervalo de confiança
- Discount (%)
- Confiança (%)
- Meta-features (pesos dinâmicos)

**Performance:**
- Tempo valuation: < 1 segundo por listing
- Precisão: MAE < 10% do valor de mercado
- Confiança: 70-85%
- Target R² > 0.85

### 3.4 Layer 4: Scoring

**Responsabilidade:** Calcular score (0-10) para cada listing

**Componentes:**
- Score Discount Calculator (30% peso)
- Score Location Calculator (25% peso)
- Score Condition Calculator (15% peso)
- Score Liquidity Calculator (15% peso)
- Score Freshness Calculator (15% peso)
- Red Flags Detector
- Weighted Score Calculator
- Rationale Generator

**Input:**
- Clean Listings + Valuations

**Output:**
- Scores (scores table)
- Score total (0-10)
- Score por factor
- Classificação (Imperdível, Bom, Aceitável, Não recomendado)
- Rationale
- Red flags

**Performance:**
- Tempo scoring: < 0.5 segundos por listing
- Taxa de erro: < 2%

### 3.5 Layer 5: Notification

**Responsabilidade:** Notificar utilizador de top 3-5 listings/dia

**Componentes:**
- Opportunity Selector (selecciona top listings)
- Telegram Bot (envia notificações)
- Message Formatter (formata mensagem detalhada)
- Notification History (rastreia notificações)

**Input:**
- Scores (scores table)
- Filtros do utilizador

**Output:**
- Notificações Telegram
- Notification History

**Performance:**
- Tempo notificação: < 10 segundos
- Taxa de falsos positivos: < 10%

### 3.6 Layer 6: Dashboard

**Responsabilidade:** Interface visual para explorar dados

**Componentes:**
- Streamlit Dashboard (UI)
- Páginas: Overview, Search, Config, Market Analysis, Telegram, System
- Filtros avançados
- Gráficos interactivos

**Input:**
- Database queries (todas as tables)

**Output:**
- UI interactiva (http://localhost:8501)

**Performance:**
- Tempo carregamento página: < 2 segundos
- Tempo query: < 1 segundo

---

## 4. COMPONENTES DETALHADOS

### 4.1 Componente: SpiderManager

**Responsabilidade:** Orquestrar execução de spiders

**Interface:**
```python
class ISpiderManager(ABC):
    @abstractmethod
    async def run_all_spiders(self) -> List[Dict]:
        """Executa todos os spiders e retorna raw listings."""
        pass
    
    @abstractmethod
    async def run_spider(self, spider_name: str) -> List[Dict]:
        """Executa um spider específico."""
        pass
    
    @abstractmethod
    def get_spider_status(self, spider_name: str) -> Dict:
        """Retorna status de um spider."""
        pass
```

**Implementação:**
```python
class SpiderManager(ISpiderManager):
    def __init__(self, proxy_manager=None, stealth_manager=None):
        self.proxy_manager = proxy_manager
        self.stealth_manager = stealth_manager
        self.spiders = {
            # Nacionais (Tier 1)
            'idealista': IdealistaSpiderNodriver,
            'imovirtual': ImovirtualSpiderNodriver,
            'casa_sapo': CasaSapoSpiderNodriver,
            'olx': OLXSpiderNodriver,
            # Bancários (Tier 2)
            'bpi': BPISpiderNodriver,
            'caixa': CaixaSpiderNodriver,
            'santander': SantanderSpiderNodriver,
            'millennium': MillenniumSpiderNodriver,
            # Regionais (Tier 3)
            'era': ERASpider,
            'century21': Century21SpiderNodriver,
            'supercasa': SuperCasaSpider,
            'remax': REMAXSpiderNodriver,
            # Mais regionais...
        }
        self.status = {name: 'idle' for name in self.spiders.keys()}
    
    async def run_all_spiders(self) -> List[Dict]:
        """Executa todos os spiders em paralelo."""
        tasks = [
            self.run_spider(name) 
            for name in self.spiders.keys()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_listings = []
        for result in results:
            if isinstance(result, list):
                all_listings.extend(result)
        
        return all_listings
```

**Dependências:**
- ProxyManager (opcional)
- StealthManager
- Spiders (17 implementações: Nacionais + Bancários + Regionais)

### 4.2 Componente: Normalizer

**Responsabilidade:** Normalizar campos dos raw listings

**Interface:**
```python
class INormalizer(ABC):
    @abstractmethod
    def normalize(self, raw_listing: Dict) -> Dict:
        """Normaliza um raw listing."""
        pass
    
    @abstractmethod
    def normalize_batch(self, raw_listings: List[Dict]) -> List[Dict]:
        """Normaliza um batch de raw listings."""
        pass
```

**Regras de Normalização:**
- **Preço:** Converter string "250.000€" → float 250000.0
- **Área:** Converter string "85 m²" → float 85.0
- **Quartos:** Converter string "3" → int 3
- **Morada:** Normalizar formato (rua, número, freguesia)
- **Data:** Converter string para datetime ISO format

**Exemplo:**
```python
class Normalizer(INormalizer):
    def normalize(self, raw_listing: Dict) -> Dict:
        normalized = {}
        
        # Normalizar preço
        normalized['preco_pedido'] = self._parse_price(
            raw_listing.get('price', '')
        )
        
        # Normalizar área
        normalized['area_util_m2'] = self._parse_area(
            raw_listing.get('area', '')
        )
        
        # Normalizar quartos
        normalized['quartos'] = self._parse_rooms(
            raw_listing.get('rooms', '')
        )
        
        # ... mais normalizações
        
        return normalized
```

### 4.3 Componente: Deduplicator

**Responsabilidade:** Detectar duplicados (mesmo imóvel em múltiplos portais)

**Estratégia:**
- Gerar fingerprint (hash de campos únicos)
- Campos únicos: morada_raw, area_util_m2, quartos, preco_pedido
- Se fingerprint igual → duplicado
- Manter listing mais recente (baseado em scrape_timestamp)

**Implementação:**
```python
class Deduplicator:
    def __init__(self):
        self.seen_fingerprints = set()
    
    def is_duplicate(self, listing: Dict) -> bool:
        """Verifica se listing é duplicado."""
        fingerprint = self._generate_fingerprint(listing)
        
        if fingerprint in self.seen_fingerprints:
            return True
        
        self.seen_fingerprints.add(fingerprint)
        return False
    
    def _generate_fingerprint(self, listing: Dict) -> str:
        """Gera fingerprint do listing."""
        key = f"{listing['morada_raw']}_{listing['area_util_m2']}" \
              f"_{listing['quartos']}_{listing['preco_pedido']}"
        return hashlib.sha256(key.encode()).hexdigest()[:32]
```

### 4.4 Componente: Geocoder

**Responsabilidade:** Geocodificar morada → lat/lon + freguesia

**Estratégia:**
- Usar Nominatim (OpenStreetMap) - gratuito
- Cache de geocodificações (local)
- Taxa de sucesso: 90-95%
- Fallback: usar freguesia do portal se geocodificação falhar

**Implementação:**
```python
class Geocoder:
    def __init__(self):
        self.cache = {}  # {morada: (lat, lon, freguesia)}
    
    async def geocode(self, morada: str) -> Tuple[float, float, str]:
        """Geocodifica morada."""
        # Verificar cache
        if morada in self.cache:
            return self.cache[morada]
        
        # Geocodificar com Nominatim
        async with aiohttp.ClientSession() as session:
            url = f"https://nominatim.openstreetmap.org/search"
            params = {'q': morada, 'format': 'json', 'countrycodes': 'pt'}
            
            async with session.get(url, params=params) as response:
                data = await response.json()
                
                if not data:
                    return (0.0, 0.0, '')
                
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                freguesia = self._extract_freguesia(data[0])
                
                # Guardar no cache
                self.cache[morada] = (lat, lon, freguesia)
                
                return (lat, lon, freguesia)
```

### 4.5 Componente: Enricher

**Responsabilidade:** Enrich listings com dados externos (INE, POIs)

**Dados INE:**
- Preço médio por m² da freguesia
- Tendências de preços (mensal, trimestral)
- Volume de transações

**Dados POIs:**
- Distância a metro
- Distância a escolas
- Distância a comércio
- Distância a hospitais

**Implementação:**
```python
class Enricher:
    def __init__(self, ine_client=None, poi_client=None):
        self.ine_client = ine_client
        self.poi_client = poi_client
    
    async def enrich(self, listing: Dict) -> Dict:
        """Enrich listing com dados externos."""
        enriched = listing.copy()
        
        # Enrich com dados INE
        if self.ine_client:
            ine_data = await self.ine_client.get_freguesia_data(
                listing['freguesia']
            )
            enriched.update(ine_data)
        
        # Enrich com POIs
        if self.poi_client:
            pois = await self.poi_client.get_nearby_pois(
                listing['lat'], listing['lon']
            )
            enriched.update(pois)
        
        # Calcular preço por m²
        enriched['preco_por_m2'] = (
            listing['preco_pedido'] / listing['area_util_m2']
            if listing['area_util_m2'] > 0 else 0
        )
        
        return enriched
```

### 4.6 Componente: Validator

**Responsabilidade:** Validar integridade dos dados

**Regras de Validação:**
- Preço > 0
- Área > 0
- Quartos ≥ 0
- Lat/lon válidos (-90 a 90, -180 a 180)
- Todos os campos obrigatórios presentes

**Implementação:**
```python
class Validator:
    REQUIRED_FIELDS = [
        'preco_pedido', 'area_util_m2', 'quartos', 
        'morada_raw', 'freguesia'
    ]
    
    def validate(self, listing: Dict) -> Tuple[bool, List[str]]:
        """Valida listing."""
        errors = []
        
        # Verificar campos obrigatórios
        for field in self.REQUIRED_FIELDS:
            if field not in listing or listing[field] is None:
                errors.append(f"Campo obrigatório ausente: {field}")
        
        # Verificar preço
        if listing.get('preco_pedido', 0) <= 0:
            errors.append("Preço deve ser > 0")
        
        # Verificar área
        if listing.get('area_util_m2', 0) <= 0:
            errors.append("Área deve ser > 0")
        
        # Verificar quartos
        if listing.get('quartos', 0) < 0:
            errors.append("Quartos deve ser ≥ 0")
        
        # Verificar lat/lon
        lat = listing.get('lat', 0)
        lon = listing.get('lon', 0)
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            errors.append("Lat/Lon inválidos")
        
        return (len(errors) == 0, errors)
```

---

## 5. FLUXO DE DADOS

### 5.1 Fluxo End-to-End

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              FLUXO DE DADOS END-TO-END                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. SCRAPING (cada 30 minutos)                                            │
│     ┌───────────────────────────────────────────────────────────────────┐  │
│     │ Scheduler dispara scraping job                                   │  │
│     │ SpiderManager.run_all_spiders()                                 │  │
│     │   └─> IdealistaSpiderNodriver.run()                             │  │
│     │   └─> ImovirtualSpiderNodriver.run()                            │  │
│     │   └─> ... (6 mais spiders)                                      │  │
│     │ Raw listings → raw_listings table                               │  │
│     └───────────────────────────────────────────────────────────────────┘  │
│                              │                                            │   │
│                              ▼                                            │   │
│  2. ETL (cada 32 minutos)                                                  │
│     ┌───────────────────────────────────────────────────────────────────┐  │
│     │ Scheduler dispara ETL job                                       │  │
│     │ PipelineETL.run()                                                │  │
│     │   └─> Normalizer.normalize_batch()                              │  │
│     │   └─> Deduplicator.filter_duplicates()                          │  │
│     │   └─> Geocoder.geocode_batch()                                  │  │
│     │   └─> Enricher.enrich_batch()                                   │  │
│     │   └─> Validator.validate_batch()                                │  │
│     │ Clean listings → clean_listings table                            │  │
│     └───────────────────────────────────────────────────────────────────┘  │
│                              │                                            │   │
│                              ▼                                            │   │
│  3. VALUATION (cada 35 minutos)                                            │
│     ┌───────────────────────────────────────────────────────────────────┐  │
│     │ Scheduler dispara valuation job                                  │  │
│     │ ValuationEngine.valuate_batch()                                 │  │
│     │   └─> HedonicModel.predict_batch()                              │  │
│     │   └─> CompsEngine.find_comparables_batch()                      │  │
│     │   └─> INEMacroData.add_context_batch()                          │  │
│     │   └─> XGBoostModel.predict_batch() (opcional)                   │  │
│     │   └─> WeightedEnsemble.combine_batch()                          │  │
│     │ Valuations → valuations table                                    │  │
│     └───────────────────────────────────────────────────────────────────┘  │
│                              │                                            │   │
│                              ▼                                            │   │
│  4. SCORING (cada 38 minutos)                                             │
│     ┌───────────────────────────────────────────────────────────────────┐  │
│     │ Scheduler dispara scoring job                                    │  │
│     │ ScoringEngine.score_batch()                                     │  │
│     │   └─> ScoreDiscountCalculator.calculate_batch()                 │  │
│     │   └─> ScoreLocationCalculator.calculate_batch()                  │  │
│     │   └─> ScoreConditionCalculator.calculate_batch()                 │  │
│     │   └─> ScoreLiquidityCalculator.calculate_batch()                 │  │
│     │   └─> ScoreFreshnessCalculator.calculate_batch()                  │  │
│     │   └─> RedFlagsDetector.detect_batch()                            │  │
│     │   └─> WeightedScoreCalculator.calculate_batch()                  │  │
│     │   └─> RationaleGenerator.generate_batch()                         │  │
│     │ Scores → scores table                                            │  │
│     └───────────────────────────────────────────────────────────────────┘  │
│                              │                                            │   │
│                              ▼                                            │   │
│  5. NOTIFICATION (cada 60 minutos)                                       │
│     ┌───────────────────────────────────────────────────────────────────┐  │
│     │ Scheduler dispara notification job                               │  │
│     │ NotificationEngine.notify()                                      │  │
│     │   └─> OpportunitySelector.select_top_listings()                  │  │
│     │   └─> TelegramBot.send_notifications()                          │  │
│     │   └─> NotificationHistory.save()                                │  │
│     │ Telegram notifications enviadas                                   │  │
│     └───────────────────────────────────────────────────────────────────┘  │
│                              │                                            │   │
│                              ▼                                            │   │
│  6. DASHBOARD (on-demand)                                                  │
│     ┌───────────────────────────────────────────────────────────────────┐  │
│     │ Utilizador acessa http://localhost:8501                         │  │
│     │ Streamlit Dashboard carrega dados                                │  │
│     │   └─> Queries a database (todas as tables)                      │  │
│     │   └─> Visualizações interactivas                                │  │
│     │ UI exibida ao utilizador                                         │  │
│     └───────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Diagrama de Sequência (Scraping → ETL)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│            DIAGRAMA DE SEQUÊNCIA: SCRAPING → ETL                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Scheduler                SpiderManager            Spider                Database │
│    │                         │                     │                        │   │
│    │ trigger job            │                     │                        │   │
│    ├──────────────────────>│                     │                        │   │
│    │                         │                     │                        │   │
│    │                         run_all_spiders()    │                        │   │
│    │                         ├────────────────────>│                        │   │
│    │                         │                     │                        │   │
│    │                         │                navigate()                   │   │
│    │                         │                     │                        │   │
│    │                         │                extract_listings()          │   │
│    │                         │                     │                        │   │
│    │                         │<────────────────────┤ raw_listings            │   │
│    │                         │                     │                        │   │
│    │                         │                     │                        │   │
│    │                         │                close()                      │   │
│    │                         │<────────────────────┤                        │   │
│    │                         │                     │                        │   │
│    │<────────────────────────┤ results             │                        │   │
│    │                         │                     │                        │   │
│    │                         │                     │                        │   │
│    │ trigger ETL job         │                     │                        │   │
│    ├──────────────────────>│                     │                        │   │
│    │                         │                     │                        │   │
│    │                         PipelineETL.run()    │                        │   │
│    │                         ├────────────────────>│                        │   │
│    │                         │                     │                        │   │
│    │                         │                SELECT * FROM raw_listings   │   │
│    │                         │<────────────────────┤                        │   │
│    │                         │                     │                        │   │
│    │                         │                normalize_batch()            │   │
│    │                         │                     │                        │   │
│    │                         │                deduplicate_batch()          │   │
│    │                         │                     │                        │   │
│    │                         │                geocode_batch()              │   │
│    │                         │                     │                        │   │
│    │                         │                enrich_batch()               │   │
│    │                         │                     │                        │   │
│    │                         │                validate_batch()              │   │
│    │                         │                     │                        │   │
│    │                         │                INSERT INTO clean_listings   │   │
│    │                         ├────────────────────>│                        │   │
│    │                         │                     │                        │   │
│    │<────────────────────────┤ done                │                        │   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. INTEGRAÇÃO ENTRE COMPONENTES

### 6.1 Contratos de Interface

**IScrapable:**
```python
class IScrapable(ABC):
    @abstractmethod
    async def run(self, max_pages: int = 5) -> List[Dict]:
        """Executa scraping e retorna raw listings."""
        pass
```

**IETL:**
```python
class IETL(ABC):
    @abstractmethod
    async def run(self) -> int:
        """Executa ETL e retorna número de clean listings."""
        pass
```

**IValuation:**
```python
class IValuation(ABC):
    @abstractmethod
    async def valuate(self, listing: Dict) -> Dict:
        """Calcula valor justo estimado."""
        pass
```

**IScorable:**
```python
class IScorable(ABC):
    @abstractmethod
    async def score(self, listing: Dict, valuation: Dict) -> Dict:
        """Calcula score (0-10)."""
        pass
```

**INotifiable:**
```python
class INotifiable(ABC):
    @abstractmethod
    async def notify(self, listings: List[Dict]) -> int:
        """Envia notificações e retorna número enviado."""
        pass
```

### 6.2 Injeção de Dependências

**Exemplo: ValuationEngine**
```python
class ValuationEngine(IValuation):
    def __init__(
        self,
        hedonic_model: IHedonicModel,
        comps_engine: ICompsEngine,
        ine_client: IINEClient,
        xgboost_model: Optional[IXGBoostModel] = None
    ):
        self.hedonic_model = hedonic_model
        self.comps_engine = comps_engine
        self.ine_client = ine_client
        self.xgboost_model = xgboost_model
        self.ensemble = WeightedEnsemble()
    
    async def valuate(self, listing: Dict) -> Dict:
        """Calcula valor justo usando ensemble."""
        # 1. Hedonic
        hedonic_value = self.hedonic_model.predict(listing)
        
        # 2. Comps
        comps_value = self.comps_engine.find_comparables_value(listing)
        
        # 3. INE
        ine_value = self.ine_client.get_freguesia_avg_price(
            listing['freguesia']
        ) * listing['area_util_m2']
        
        # 4. XGBoost (opcional)
        xgboost_value = 0
        if self.xgboost_model:
            xgboost_value = self.xgboost_model.predict(listing)
        
        # 5. Ensemble
        final_value = self.ensemble.combine({
            'hedonic': hedonic_value,
            'comps': comps_value,
            'ine': ine_value,
            'xgboost': xgboost_value
        })
        
        return {
            'valor_justo': final_value,
            'hedonic_value': hedonic_value,
            'comps_value': comps_value,
            'ine_value': ine_value,
            'xgboost_value': xgboost_value,
            'discount': (listing['preco_pedido'] - final_value) / final_value * 100
        }
```

---

## 7. ARQUITECTURA DE BANCO DE DADOS

### 7.1 Schema SQLite (MVP)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              SCHEMA SQLITE (MVP)                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TABLE raw_listings:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ id TEXT PRIMARY KEY,                                                   │   │
│  │ source_portal TEXT NOT NULL,                                          │   │
│  │ source_id TEXT NOT NULL,                                              │   │
│  │ source_url TEXT NOT NULL,                                             │   │
│  │ scrape_timestamp TEXT NOT NULL,                                       │   │
│  │ raw_data JSON NOT NULL,                                                │   │
│  │ created_at TEXT NOT NULL                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TABLE clean_listings:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ id TEXT PRIMARY KEY,                                                   │   │
│  │ source_portal TEXT NOT NULL,                                          │   │
│  │ source_id TEXT NOT NULL,                                              │   │
│  │ source_url TEXT NOT NULL,                                             │   │
│  │ scrape_timestamp TEXT NOT NULL,                                       │   │
│  │ titulo TEXT,                                                           │   │
│  │ descricao TEXT,                                                         │   │
│  │ preco_pedido REAL NOT NULL,                                            │   │
│  │ area_util_m2 REAL NOT NULL,                                           │   │
│  │ quartos INTEGER NOT NULL,                                             │   │
│  │ casas_banho INTEGER,                                                   │   │
│  │ morada_raw TEXT,                                                       │   │
│  │ freguesia TEXT,                                                        │   │
│  │ concelho TEXT,                                                         │   │
│  │ lat REAL,                                                               │   │
│  │ lon REAL,                                                               │   │
│  │ estado TEXT,                                                            │   │
│  │ ano_construcao INTEGER,                                                │   │
│  │ cert_energetico TEXT,                                                  │   │
│  │ fotos_urls JSON,                                                       │   │
│  │ num_fotos INTEGER,                                                      │   │
│  │ agencia TEXT,                                                           │   │
│  │ preco_por_m2 REAL,                                                     │   │
│  │ ine_preco_medio_m2 REAL,                                               │   │
│  │ ine_tendencia_mensal REAL,                                            │   │
│  │ dist_metro_m REAL,                                                     │   │
│  │ dist_escola_m REAL,                                                    │   │
│  │ dist_comercio_m REAL,                                                  │   │
│  │ created_at TEXT NOT NULL,                                              │   │
│  │ updated_at TEXT NOT NULL                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TABLE valuations:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ id TEXT PRIMARY KEY,                                                   │   │
│  │ listing_id TEXT NOT NULL,                                             │   │
│  │ valor_justo REAL NOT NULL,                                            │   │
│  │ hedonic_value REAL,                                                    │   │
│  │ comps_value REAL,                                                      │   │
│  │ ine_value REAL,                                                         │   │
│  │ xgboost_value REAL,                                                    │   │
│  │ ci_lower REAL,                                                         │   │
│  │ ci_upper REAL,                                                         │   │
│  │ discount REAL NOT NULL,                                                │   │
│  │ confianca REAL NOT NULL,                                               │   │
│  │ created_at TEXT NOT NULL                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TABLE scores:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ id TEXT PRIMARY KEY,                                                   │   │
│  │ listing_id TEXT NOT NULL,                                             │   │
│  │ score_total REAL NOT NULL,                                             │   │
│  │ score_discount REAL NOT NULL,                                          │   │
│  │ score_location REAL NOT NULL,                                         │   │
│  │ score_condition REAL NOT NULL,                                        │   │
│  │ score_liquidity REAL NOT NULL,                                         │   │
│  │ score_freshness REAL NOT NULL,                                        │   │
│  │ classificacao TEXT NOT NULL,                                          │   │
│  │ rationale TEXT,                                                         │   │
│  │ red_flags JSON,                                                        │   │
│  │ created_at TEXT NOT NULL                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TABLE notifications:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ id TEXT PRIMARY KEY,                                                   │   │
│  │ listing_id TEXT NOT NULL,                                             │   │
│  │ telegram_chat_id TEXT NOT NULL,                                        │   │
│  │ telegram_message_id TEXT,                                              │   │
│  │ message TEXT NOT NULL,                                                 │   │
│  │ sent_at TEXT NOT NULL,                                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TABLE config:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ key TEXT PRIMARY KEY,                                                  │   │
│  │ value JSON NOT NULL,                                                   │   │
│  │ updated_at TEXT NOT NULL                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Índices

```sql
-- Índices para performance
CREATE INDEX idx_clean_listings_freguesia ON clean_listings(freguesia);
CREATE INDEX idx_clean_listings_preco ON clean_listings(preco_pedido);
CREATE INDEX idx_clean_listings_area ON clean_listings(area_util_m2);
CREATE INDEX idx_clean_listings_scrape_timestamp ON clean_listings(scrape_timestamp);
CREATE INDEX idx_valuations_listing_id ON valuations(listing_id);
CREATE INDEX idx_scores_listing_id ON scores(listing_id);
CREATE INDEX idx_scores_score_total ON scores(score_total);
CREATE INDEX idx_notifications_listing_id ON notifications(listing_id);
```

---

## 8. ARQUITECTURA DE SCHEDULER

### 8.1 APScheduler Configuration

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

# Configuração do scheduler
scheduler = AsyncIOScheduler(
    jobstores={
        'default': SQLAlchemyJobStore(url='sqlite:///data/db/scheduler.db')
    },
    executors={
        'default': AsyncIOExecutor()
    },
    job_defaults={
        'coalesce': True,
        'max_instances': 1,
        'misfire_grace_time': 300
    }
)
```

### 8.2 Jobs Agendados

```python
# Job 1: Scraping (cada 30 minutos)
scheduler.add_job(
    func=scraping_job,
    trigger='interval',
    minutes=30,
    id='scraping_job',
    name='Scraping Job'
)

# Job 2: ETL (cada 32 minutos)
scheduler.add_job(
    func=etl_job,
    trigger='interval',
    minutes=32,
    id='etl_job',
    name='ETL Job'
)

# Job 3: Valuation (cada 35 minutos)
scheduler.add_job(
    func=valuation_job,
    trigger='interval',
    minutes=35,
    id='valuation_job',
    name='Valuation Job'
)

# Job 4: Scoring (cada 38 minutos)
scheduler.add_job(
    func=scoring_job,
    trigger='interval',
    minutes=38,
    id='scoring_job',
    name='Scoring Job'
)

# Job 5: Notification (cada 60 minutos)
scheduler.add_job(
    func=notification_job,
    trigger='interval',
    minutes=60,
    id='notification_job',
    name='Notification Job'
)
```

---

## 9. ARQUITECTURA DE MONITORIZAÇÃO

### 9.1 Logging com Loguru

```python
from loguru import logger

# Configuração Loguru
logger.remove()  # Remove handler default
logger.add(
    "logs/app_{time}.log",
    rotation="1 day",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
)
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
```

### 9.2 Health Checks

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    checks = {
        'database': check_database(),
        'scheduler': check_scheduler(),
        'spiders': check_spiders()
    }
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            'status': 'healthy' if all_healthy else 'unhealthy',
            'checks': checks
        }
    )
```

---

## 10. DIAGRAMAS DE SEQUÊNCIA

### 10.1 Diagrama de Sequência (Valuation → Scoring)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│         DIAGRAMA DE SEQUÊNCIA: VALUATION → SCORING                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Scheduler              ValuationEngine         ScoringEngine          Database │
│    │                         │                     │                        │   │
│    │ trigger valuation job  │                     │                        │   │
│    ├──────────────────────>│                     │                        │   │
│    │                         │                     │                        │   │
│    │                         SELECT * FROM clean_listings                   │   │
│    │                         ├────────────────────>│                        │   │
│    │                         │<────────────────────┤ listings                │   │
│    │                         │                     │                        │   │
│    │                         valuate_batch()      │                        │   │
│    │                         │                     │                        │   │
│    │                         │  HedonicModel.predict()                     │   │
│    │                         │  CompsEngine.find_comparables()             │   │
│    │                         │  INEMacroData.add_context()                 │   │
│    │                         │  WeightedEnsemble.combine()                 │   │
│    │                         │                     │                        │   │
│    │                         INSERT INTO valuations                         │   │
│    │                         ├────────────────────>│                        │   │
│    │                         │                     │                        │   │
│    │<────────────────────────┤ done                │                        │   │
│    │                         │                     │                        │   │
│    │ trigger scoring job     │                     │                        │   │
│    ├──────────────────────>│                     │                        │   │
│    │                         │                     │                        │   │
│    │                         SELECT * FROM clean_listings                  │   │
│    │                         JOIN valuations                                │   │
│    │                         ├────────────────────>│                        │   │
│    │                         │<────────────────────┤ listings + valuations   │   │
│    │                         │                     │                        │   │
│    │                         score_batch()       │                        │   │
│    │                         │                     │                        │   │
│    │                         │  ScoreDiscountCalculator()                │   │
│    │                         │  ScoreLocationCalculator()                 │   │
│    │                         │  ScoreConditionCalculator()                │   │
│    │                         │  ScoreLiquidityCalculator()                │   │
│    │                         │  ScoreFreshnessCalculator()                 │   │
│    │                         │  WeightedScoreCalculator()                   │   │
│    │                         │  RationaleGenerator()                      │   │
│    │                         │                     │                        │   │
│    │                         INSERT INTO scores                             │   │
│    │                         ├────────────────────>│                        │   │
│    │                         │                     │                        │   │
│    │<────────────────────────┤ done                │                        │   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 11. PADRÕES DE DESIGN

### 11.1 Padrões Utilizados

**1. Repository Pattern**
- Abstracção sobre database
- Interface: IDatabaseRepository
- Implementações: SQLiteRepository, PostgreSQLRepository

**2. Factory Pattern**
- Criação de spiders
- Interface: ISpiderFactory
- Implementação: NodriverSpiderFactory

**3. Strategy Pattern**
- Diferentes estratégias de scraping
- Interface: IScrapingStrategy
- Implementações: NodriverStrategy, CurlCffiStrategy

**4. Observer Pattern**
- Scheduler observa tempo e dispara jobs
- Interface: IJobObserver
- Implementação: APSchedulerJobObserver

**5. Pipeline Pattern**
- ETL pipeline sequencial
- Interface: IPipeline
- Implementação: PipelineETL

**6. Builder Pattern**
- Construção de mensagens Telegram
- Interface: IMessageBuilder
- Implementação: TelegramMessageBuilder

---

## 12. CONSIDERAÇÕES DE PERFORMANCE

### 12.1 Optimizações

**Database:**
- SQLite WAL mode (Write-Ahead Logging)
- Índices em campos frequentemente queryados
- Batch inserts em vez de inserts individuais
- Connection pooling

**Scraping:**
- Async/await para scraping paralelo
- Rate limiting para evitar bloqueios
- Circuit breakers para pausar em falhas
- Warm-up navigation para Nodriver

**ETL:**
- Batch processing em vez de row-by-row
- Cache de geocodificações
- Lazy loading de dados externos (INE, POIs)

**Valuation:**
- Modelos carregados em memória
- Batch predictions em vez de single predictions
- Cache de comparáveis (Comps Engine)

**Scoring:**
- Cálculos vectorizados com NumPy
- Cache de scores por freguesia
- Lazy evaluation de red flags

---

## 13. CONSIDERAÇÕES DE SEGURANÇA

### 13.1 Security Measures

**GDPR Compliance:**
- Dados locais (nunca saem do PC)
- Encriptação de secrets (Telegram tokens)
- Logging sem dados pessoais
- Right to be forgotten (delete endpoint)

**Rate Limiting:**
- Rate limiting por portal
- Respect robots.txt
- User-agent rotation
- Backoff em falhas

**Input Validation:**
- Validação de todos os inputs
- Sanitização de strings
- SQL injection prevention (SQLAlchemy ORM)
- XSS prevention (escaping em dashboard)

**Secrets Management:**
- Environment variables (.env)
- Encriptação de tokens (Fernet)
- Não hardcode secrets no código
- .env no .gitignore

---

## 14. ROADMAP DE ESCALABILIDADE

### 14.1 Fases de Escalabilidade

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              ROADMAP DE ESCALABILIDADE (4 FASES)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FASE 1: OPTIMIZAÇÃO (Custo: €0/mês)                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ SQLite WAL mode                                                      │   │
│  │ Rate limiting global                                                  │   │
│  │ Logging estruturado                                                  │   │
│  │ Health checks                                                         │   │
│  │ Capacidade: 1000 listings/dia                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 2: MULTI-INSTANCE (Custo: ~€110/mês)                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Migrar para PostgreSQL                                               │   │
│  │ Adicionar Redis para cache                                            │   │
│  │ Implementar Celery + RabbitMQ                                        │   │
│  │ Docker containerization                                               │   │
│  │ Deploy em 2 VPS                                                       │   │
│  │ Capacidade: 5000 listings/dia                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 3: MICROSERVICES (Custo: ~€500/mês)                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Separar em microservices                                            │   │
│  │ Implementar Kubernetes                                               │   │
│  │ Distributed tracing (OpenTelemetry)                                  │   │
│  │ Circuit breakers (Istio/Linkerd)                                     │   │
│  │ Capacidade: 20000 listings/dia                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 4: CLOUD-NATIVE (Custo: ~€700-900/mês)                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Migrar para managed services                                        │   │
│  │ AWS RDS / Azure Database / Cloud SQL                                  │   │
│  │ AWS SQS / Azure Service Bus / Google Pub/Sub                        │   │
│  │ AWS ElastiCache / Azure Cache / Memorystore                           │   │
│  │ Serverless para peak loads (AWS Lambda)                              │   │
│  │ Capacidade: 100000+ listings/dia                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 15. GLOSSÁRIO DE ARQUITECTURA

```
┌─────────────────────────────────────────────────────────────────────────────┐
│            GLOSSÁRIO DE ARQUITECTURA                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LOCAL-FIRST: Arquitectura onde dados ficam localmente (no PC)          │
│                                                                             │
│  EVENT-DRIVEN ARCHITECTURE (EDA): Arquitectura baseada em eventos         │
│                                                                             │
│  BATCH PROCESSING: Processamento em lotes (não streaming)                 │
│                                                                             │
│  PRODUCER-CONSUMER: Padrão onde produtor gera dados, consumidor processa │
│                                                                             │
│  PIPELINE: Sequência de transformações de dados                           │
│                                                                             │
│  OBSERVER: Padrão onde observador reage a mudanças de estado            │
│                                                                             │
│  REPOSITORY: Padrão de abstracção sobre database                          │
│                                                                             │
│  FACTORY: Padrão de criação de objectos                                  │
│                                                                             │
│  STRATEGY: Padrão para encapsular algoritmos intercambiáveis            │
│                                                                             │
│  BUILDER: Padrão para construção complexa de objectos                     │
│                                                                             │
│  INJECTION OF DEPENDENCIES: Padrão para injectar dependências           │
│                                                                             │
│  SOLID: Princípios de design (Single Responsibility, Open/Closed, etc.) │
│                                                                             │
│  KISS: Keep It Simple, Stupid (princípio de simplicidade)                │
│                                                                             │
│  DRY: Don't Repeat Yourself (princípio de não repetição)                  │
│                                                                             │
│  WAL: Write-Ahead Logging (modo SQLite para melhor performance)          │
│                                                                             │
│  CIRCUIT BREAKER: Padrão para pausar em falhas consecutivas             │
│                                                                             │
│  RATE LIMITING: Limitação de taxa de requests                             │
│                                                                             │
│  HEALTH CHECK: Verificação de saúde do sistema                           │
│                                                                             │
│  OBSERVABILITY: Capacidade de observar estado interno do sistema         │
│                                                                             │
│  TRACING: Rastreio de requisições através de componentes                 │
│                                                                             │
│  MICROSERVICES: Arquitectura de serviços pequenos e independentes         │
│                                                                             │
│  KUBERNETES: Orquestrador de containers                                  │
│                                                                             │
│  CELERY: Distributed task queue                                          │
│                                                                             │
│  RABBITMQ: Message broker                                                  │
│                                                                             │
│  REDIS: Cache e message broker                                             │
│                                                                             │
│  SERVERLESS: Computação sem servidor (AWS Lambda, etc.)                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*Fim do Documento 03 — Arquitectura do Sistema*
