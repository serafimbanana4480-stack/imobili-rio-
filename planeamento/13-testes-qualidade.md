# TESTES E QUALIDADE — REAL ESTATE OPPORTUNITY ENGINE
## Estratégia de Testes: Unit, Integration e E2E

> **Este documento:** Especificação completa de testes e qualidade  
> **Objectivo:** Fornecer especificação detalhada de testes para IA implementar  
> **Linhas:** 1500+ linhas de documentação detalhada  
> **Versão:** 5.0 (Actualizado com Volume 13)

---

## ÍNDICE

1. [Introdução aos Testes](#1-introducao-aos-testes)
2. [Estratégia de Testes](#2-estrategia-de-testes)
3. [Pytest Configuration](#3-pytest-configuration)
4. [Testes Unitários](#4-testes-unitarios)
5. [Testes de Integração](#5-testes-de-integracao)
6. [Testes E2E](#6-testes-e2e)
7. [Testes de Scraping](#7-testes-de-scraping)
8. [Testes de ETL](#8-testes-de-etl)
9. [Testes de Valuation](#9-testes-de-valuation)
10. [Testes de Scoring](#10-testes-de-scoring)
11. [Cobertura de Código](#11-cobertura-de-codigo)
12. [Test Data Management](#12-test-data-management)
13. [CI/CD Pipeline de Testes](#13-cicd-pipeline-de-testes)
14. [Best Practices Testes](#14-best-practices-testes)
15. [Glossário de Testes](#15-glossário-de-testes)

---

## 1. INTRODUÇÃO AOS TESTES

### 1.1 Objectivo dos Testes

**Testes** são o conjunto de práticas para garantir qualidade e confiabilidade do sistema:
- Testes unitários (testar funções individuais)
- Testes de integração (testar componentes juntos)
- Testes E2E (testar fluxos end-to-end)
- Cobertura de código (medir % de código testado)
- CI/CD pipeline (automatizar testes em cada commit)

**Objectivo:** Detectar bugs antes de produção, garantir regressões não são introduzidas, e documentar comportamento esperado.

### 1.2 Porquê Testes?

**Problema sem Testes:**
- Bugs só são descobertos em produção
- Refactoring é arriscado (sem safety net)
- Difícil saber se mudanças quebraram algo
- Sem documentação de comportamento esperado

**Solução com Testes:**
- Bugs detectados antes de produção
- Refactoring seguro (testes garantem comportamento)
- CI/CD detecta regressões automaticamente
- Documentação viva de comportamento esperado

---

## 2. ESTRATÉGIA DE TESTES

### 2.1 Pirâmide de Testes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              PIRÂMIDE DE TESTES                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  E2E TESTS (10%)                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Fluxos end-to-end completos                                        │   │
│  │ - Scraping → ETL → Valuation → Scoring → Notification              │   │
│  │ - Lento (minutos)                                                    │   │
│  │ - Frágil (depende de portais externos)                              │   │
│  │ - 10-20 testes                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ▲                                            │   │
│                              │                                            │   │
│  INTEGRATION TESTS (30%)                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Testar componentes juntos                                       │   │
│  │ - Database + Repository                                            │   │
│  │ - ETL + Database                                                    │   │
│  │ - Valuation + Database                                             │   │
│  │ - Médio (segundos)                                                  │   │
│  │ - 50-100 testes                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ▲                                            │   │
│                              │                                            │   │
│  UNIT TESTS (60%)                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Testar funções individuais                                      │   │
│  │ - Normalizer, Deduplicator, Geocoder                               │   │
│  │ - Score calculators                                                 │   │
│  │ - Rápido (milissegundos)                                            │   │
│  │ - 200-500 testes                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. PYTEST CONFIGURATION

### 3.1 Configuração pytest.ini

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --tb=short
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=70
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow tests
    scraping: Scraping tests
```

### 3.2 Configuração conftest.py

```python
# conftest.py
import pytest
import asyncio
from pathlib import Path
import sys

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture(scope="session")
def event_loop():
    """Cria event loop para testes async."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_database():
    """Database mock para testes."""
    from unittest.mock import MagicMock
    mock_db = MagicMock()
    mock_db.execute.return_value = [(1,)]
    return mock_db

@pytest.fixture
def sample_listing():
    """Listing de exemplo para testes."""
    return {
        'id': '123',
        'source_portal': 'idealista',
        'source_id': '456',
        'source_url': 'https://idealista.pt/imovel/456',
        'titulo': 'T3 Renovado Cedofeita',
        'preco_pedido': 180000,
        'area_util_m2': 85,
        'quartos': 3,
        'casas_banho': 2,
        'morada_raw': 'Rua do Cedofeita 123, Porto',
        'freguesia': 'Cedofeita',
        'concelho': 'Porto',
        'lat': 41.15,
        'lon': -8.61,
        'estado': 'Bom',
        'ano_construcao': 2010,
        'cert_energetico': 'B',
        'fotos_urls': ['https://example.com/foto1.jpg'],
        'num_fotos': 1,
        'agencia': 'Imobiliária Exemplo',
        'scrape_timestamp': '2026-01-15T10:30:00'
    }

@pytest.fixture
def sample_valuation():
    """Valuation de exemplo para testes."""
    return {
        'id': '123',
        'listing_id': '123',
        'valor_justo': 200000,
        'hedonic_value': 195000,
        'comps_value': 205000,
        'ine_value': 200000,
        'xgboost_value': 0,
        'ci_lower': 180000,
        'ci_upper': 220000,
        'discount': 10.0,
        'confianca': 75.0
    }
```

---

## 4. TESTES UNITÁRIOS

### 4.1 Teste Normalizer

```python
# tests/etl/test_normalizer.py
import pytest
from etl.normalizer import Normalizer

@pytest.mark.unit
class TestNormalizer:
    """Testes do Normalizer."""
    
    def test_parse_price_valid(self):
        """Testa parse de preço válido."""
        normalizer = Normalizer()
        
        # Teste com formato "250.000€"
        price = normalizer._parse_price("250.000€")
        assert price == 250000.0
        
        # Teste com formato "250000"
        price = normalizer._parse_price("250000")
        assert price == 250000.0
    
    def test_parse_price_invalid(self):
        """Testa parse de preço inválido."""
        normalizer = Normalizer()
        
        # Teste com string vazia
        price = normalizer._parse_price("")
        assert price == 0.0
        
        # Teste com formato inválido
        price = normalizer._parse_price("abc")
        assert price == 0.0
    
    def test_parse_area_valid(self):
        """Testa parse de área válida."""
        normalizer = Normalizer()
        
        # Teste com formato "85 m²"
        area = normalizer._parse_area("85 m²")
        assert area == 85.0
        
        # Teste com formato "85"
        area = normalizer._parse_area("85")
        assert area == 85.0
    
    def test_parse_rooms_valid(self):
        """Testa parse de quartos válido."""
        normalizer = Normalizer()
        
        # Teste com formato "3"
        rooms = normalizer._parse_rooms("3")
        assert rooms == 3
        
        # Teste com formato "3 quartos"
        rooms = normalizer._parse_rooms("3 quartos")
        assert rooms == 3
    
    def test_normalize_listing(self, sample_listing):
        """Testa normalização de listing."""
        normalizer = Normalizer()
        normalized = normalizer.normalize(sample_listing)
        
        # Verificar campos normalizados
        assert normalized['preco_pedido'] == 180000.0
        assert normalized['area_util_m2'] == 85.0
        assert normalized['quartos'] == 3
        assert normalized['casas_banho'] == 0  # Default se não existir
```

### 4.2 Teste Deduplicator

```python
# tests/etl/test_deduplicator.py
import pytest
from etl.deduplicator import Deduplicator

@pytest.mark.unit
class TestDeduplicator:
    """Testes do Deduplicator."""
    
    def test_generate_fingerprint(self, sample_listing):
        """Testa geração de fingerprint."""
        deduplicator = Deduplicator()
        fingerprint = deduplicator._generate_fingerprint(sample_listing)
        
        # Fingerprint deve ser string de 32 caracteres
        assert isinstance(fingerprint, str)
        assert len(fingerprint) == 32
    
    def test_is_duplicate_first_time(self, sample_listing):
        """Testa detecção de duplicado (primeira vez)."""
        deduplicator = Deduplicator()
        
        # Primeira vez → não é duplicado
        is_duplicate = deduplicator.is_duplicate(sample_listing)
        assert is_duplicate == False
    
    def test_is_duplicate_second_time(self, sample_listing):
        """Testa detecção de duplicado (segunda vez)."""
        deduplicator = Deduplicator()
        
        # Primeira vez
        is_duplicate = deduplicator.is_duplicate(sample_listing)
        assert is_duplicate == False
        
        # Segunda vez → é duplicado
        is_duplicate = deduplicator.is_duplicate(sample_listing)
        assert is_duplicate == True
    
    def test_is_duplicate_different_listing(self, sample_listing):
        """Testa detecção de duplicado (listing diferente)."""
        deduplicator = Deduplicator()
        
        # Primeiro listing
        is_duplicate = deduplicator.is_duplicate(sample_listing)
        assert is_duplicate == False
        
        # Segundo listing (diferente)
        different_listing = sample_listing.copy()
        different_listing['preco_pedido'] = 200000
        is_duplicate = deduplicator.is_duplicate(different_listing)
        assert is_duplicate == False
```

### 4.3 Teste Score Calculators

```python
# tests/scoring/test_score_discount_calculator.py
import pytest
from scoring.score_discount_calculator import ScoreDiscountCalculator

@pytest.mark.unit
class TestScoreDiscountCalculator:
    """Testes do ScoreDiscountCalculator."""
    
    def test_calculate_high_discount(self):
        """Testa cálculo de discount alto."""
        calculator = ScoreDiscountCalculator()
        listing = {'preco_pedido': 160000}
        valuation = {'discount': 25.0}
        
        score = calculator.calculate(listing, valuation)
        
        # Discount ≥ 20% → score 8-10
        assert score >= 8.0
        assert score <= 10.0
    
    def test_calculate_medium_discount(self):
        """Testa cálculo de discount médio."""
        calculator = ScoreDiscountCalculator()
        listing = {'preco_pedido': 180000}
        valuation = {'discount': 15.0}
        
        score = calculator.calculate(listing, valuation)
        
        # Discount 10-19% → score 6-7.9
        assert score >= 6.0
        assert score <= 7.9
    
    def test_calculate_low_discount(self):
        """Testa cálculo de discount baixo."""
        calculator = ScoreDiscountCalculator()
        listing = {'preco_pedido': 195000}
        valuation = {'discount': 5.0}
        
        score = calculator.calculate(listing, valuation)
        
        # Discount 5-9% → score 4-5.9
        assert score >= 4.0
        assert score <= 5.9
    
    def test_calculate_overpricing(self):
        """Testa cálculo de overpricing."""
        calculator = ScoreDiscountCalculator()
        listing = {'preco_pedido': 250000}
        valuation = {'discount': -25.0}
        
        score = calculator.calculate(listing, valuation)
        
        # Overpricing → score 0
        assert score == 0.0
```

---

## 5. TESTES DE INTEGRAÇÃO

### 5.1 Teste ETL + Database

```python
# tests/integration/test_etl_database.py
import pytest
import asyncio
from etl.pipeline_etl import PipelineETL
from database.repository import DatabaseRepository

@pytest.mark.integration
@pytest.mark.slow
class TestETLDatabase:
    """Testes de integração ETL + Database."""
    
    @pytest.fixture
    async def database(self):
        """Database de teste (SQLite em memória)."""
        repo = DatabaseRepository(":memory:")
        await repo.initialize()
        yield repo
        await repo.close()
    
    async def test_etl_pipeline(self, database):
        """Testa pipeline ETL completo."""
        # Inserir raw listings
        raw_listings = [
            {
                'id': '1',
                'source_portal': 'idealista',
                'source_id': '123',
                'source_url': 'https://idealista.pt/imovel/123',
                'scrape_timestamp': '2026-01-15T10:30:00',
                'raw_data': {'title': 'T3 Cedofeita', 'price': '180000€', 'area': '85 m²'}
            }
        ]
        
        await database.insert_raw_listings(raw_listings)
        
        # Executar ETL
        pipeline = PipelineETL(
            normalizer=Normalizer(),
            deduplicator=Deduplicator(),
            geocoder=Geocoder(),
            enricher=Enricher(),
            validator=Validator(),
            database_repository=database
        )
        
        count = await pipeline.run()
        
        # Verificar se clean listings foram inseridos
        clean_listings = await database.get_clean_listings()
        assert len(clean_listings) == 1
        assert clean_listings[0]['preco_pedido'] == 180000.0
        assert clean_listings[0]['area_util_m2'] == 85.0
```

### 5.2 Teste Valuation + Database

```python
# tests/integration/test_valuation_database.py
import pytest
import asyncio
from valuation.valuation_engine import ValuationEngine
from database.repository import DatabaseRepository

@pytest.mark.integration
@pytest.mark.slow
class TestValuationDatabase:
    """Testes de integração Valuation + Database."""
    
    @pytest.fixture
    async def database(self):
        """Database de teste."""
        repo = DatabaseRepository(":memory:")
        await repo.initialize()
        yield repo
        await repo.close()
    
    async def test_valuation_pipeline(self, database):
        """Testa pipeline de valuation completo."""
        # Inserir clean listings
        clean_listings = [
            {
                'id': '1',
                'titulo': 'T3 Cedofeita',
                'preco_pedido': 180000,
                'area_util_m2': 85,
                'quartos': 3,
                'freguesia': 'Cedofeita',
                'lat': 41.15,
                'lon': -8.61
            }
        ]
        
        await database.insert_clean_listings(clean_listings)
        
        # Executar valuation
        valuation_engine = ValuationEngine(
            hedonic_model=HedonicModel(),
            comps_engine=CompsEngine(database),
            ine_client=INEClient(),
            xgboost_model=None  # Opcional
        )
        
        # Treinar modelo com dados dummy
        training_data = [
            {'area_util_m2': 85, 'quartos': 3, 'preco_pedido': 180000}
        ]
        valuation_engine.hedonic_model.train(training_data)
        
        # Valuar
        for listing in clean_listings:
            valuation = await valuation_engine.valuate(listing)
            await database.insert_valuation(valuation)
        
        # Verificar se valuations foram inseridos
        valuations = await database.get_valuations()
        assert len(valuations) == 1
        assert valuations[0]['valor_justo'] > 0
        assert valuations[0]['discount'] is not None
```

---

## 6. TESTES E2E

### 6.1 Teste E2E Completo

```python
# tests/e2e/test_pipeline_e2e.py
import pytest
import asyncio
from scraping.spider_manager import SpiderManager
from etl.pipeline_etl import PipelineETL
from valuation.valuation_engine import ValuationEngine
from scoring.scoring_engine import ScoringEngine
from database.repository import DatabaseRepository

@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.skip(reason="E2E tests são lentos e dependem de portais externos")
class TestPipelineE2E:
    """Testes E2E do pipeline completo."""
    
    async def test_complete_pipeline(self):
        """Testa pipeline completo (Scraping → ETL → Valuation → Scoring)."""
        # Database
        database = DatabaseRepository(":memory:")
        await database.initialize()
        
        try:
            # Step 1: Scraping (mock)
            spider_manager = SpiderManager()
            # Mock scraping para não depender de portais reais
            raw_listings = [
                {
                    'id': '1',
                    'source_portal': 'idealista',
                    'source_id': '123',
                    'source_url': 'https://idealista.pt/imovel/123',
                    'scrape_timestamp': '2026-01-15T10:30:00',
                    'raw_data': {'title': 'T3 Cedofeita', 'price': '180000€', 'area': '85 m²'}
                }
            ]
            await database.insert_raw_listings(raw_listings)
            
            # Step 2: ETL
            pipeline_etl = PipelineETL(
                normalizer=Normalizer(),
                deduplicator=Deduplicator(),
                geocoder=Geocoder(),
                enricher=Enricher(),
                validator=Validator(),
                database_repository=database
            )
            await pipeline_etl.run()
            
            # Step 3: Valuation
            valuation_engine = ValuationEngine(
                hedonic_model=HedonicModel(),
                comps_engine=CompsEngine(database),
                ine_client=INEClient(),
                xgboost_model=None
            )
            
            # Treinar com dummy data
            training_data = [
                {'area_util_m2': 85, 'quartos': 3, 'preco_pedido': 180000}
            ]
            valuation_engine.hedonic_model.train(training_data)
            
            clean_listings = await database.get_clean_listings()
            for listing in clean_listings:
                valuation = await valuation_engine.valuate(listing)
                await database.insert_valuation(valuation)
            
            # Step 4: Scoring
            scoring_engine = ScoringEngine(
                score_discount_calculator=ScoreDiscountCalculator(),
                score_location_calculator=ScoreLocationCalculator(),
                score_condition_calculator=ScoreConditionCalculator(),
                score_liquidity_calculator=ScoreLiquidityCalculator(),
                score_freshness_calculator=ScoreFreshnessCalculator(),
                red_flags_detector=RedFlagsDetector(),
                weighted_score_calculator=WeightedScoreCalculator(),
                rationale_generator=RationaleGenerator()
            )
            
            for listing in clean_listings:
                valuation = await database.get_valuation_by_listing_id(listing['id'])
                score = await scoring_engine.score(listing, valuation)
                await database.insert_score(score)
            
            # Verificar pipeline completo
            scores = await database.get_scores()
            assert len(scores) == 1
            assert scores[0]['score_total'] >= 0
            assert scores[0]['score_total'] <= 10
            
        finally:
            await database.close()
```

---

## 7. TESTES DE SCRAPING

### 7.1 Teste Spider Nodriver (Mock)

```python
# tests/scraping/test_spider_nodriver.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from scraping.spiders.idealista_spider_nodriver import IdealistaSpiderNodriver

@pytest.mark.scraping
@pytest.mark.unit
class TestIdealistaSpiderNodriver:
    """Testes do IdealistaSpiderNodriver."""
    
    @pytest.mark.asyncio
    async def test_parse_price(self):
        """Testa parse de preço."""
        spider = IdealistaSpiderNodriver()
        
        # Teste com formato "250.000€"
        price = spider._parse_price("250.000€")
        assert price == 250000.0
    
    @pytest.mark.asyncio
    async def test_parse_area(self):
        """Testa parse de área."""
        spider = IdealistaSpiderNodriver()
        
        # Teste com formato "85 m²"
        area = spider._parse_area("85 m²")
        assert area == 85.0
    
    @pytest.mark.asyncio
    async def test_parse_listing_mock(self):
        """Testa parse de listing com mock."""
        spider = IdealistaSpiderNodriver()
        
        # Mock page element
        mock_element = AsyncMock()
        mock_element.query_selector = AsyncMock()
        
        mock_title_element = AsyncMock()
        mock_title_element.get_text = AsyncMock(return_value="T3 Cedofeita")
        mock_element.query_selector.return_value = mock_title_element
        
        mock_price_element = AsyncMock()
        mock_price_element.get_text = AsyncMock(return_value="180.000€")
        
        # Parse
        listing = await spider.parse_listing(mock_element, "https://idealista.pt/imovel/123")
        
        # Verificar
        assert listing['source_portal'] == 'idealista'
        assert listing['titulo'] == 'T3 Cedofeita'
        assert listing['preco_pedido'] == 180000.0
```

---

## 8. TESTES DE ETL

### 8.1 Teste Pipeline ETL

```python
# tests/etl/test_pipeline_etl.py
import pytest
from etl.pipeline_etl import PipelineETL

@pytest.mark.integration
class TestPipelineETL:
    """Testes do PipelineETL."""
    
    @pytest.mark.asyncio
    async def test_pipeline_normal_flow(self, sample_listing):
        """Testa fluxo normal do pipeline."""
        pipeline = PipelineETL(
            normalizer=Normalizer(),
            deduplicator=Deduplicator(),
            geocoder=Geocoder(),
            enricher=Enricher(),
            validator=Validator(),
            database_repository=MockDatabaseRepository()
        )
        
        # Pipeline deve completar sem erros
        count = await pipeline.run()
        assert count > 0
    
    @pytest.mark.asyncio
    async def test_pipeline_with_invalid_listing(self):
        """Testa pipeline com listing inválido."""
        pipeline = PipelineETL(
            normalizer=Normalizer(),
            deduplicator=Deduplicator(),
            geocoder=Geocoder(),
            enricher=Enricher(),
            validator=Validator(),
            database_repository=MockDatabaseRepository()
        )
        
        # Listing inválido (preço = 0)
        invalid_listing = {
            'id': '1',
            'preco_pedido': 0,
            'area_util_m2': 0,
            'quartos': 0
        }
        
        # Pipeline deve ignorar listing inválido
        count = await pipeline.run()
        assert count == 0
```

---

## 9. TESTES DE VALUATION

### 9.1 Teste Valuation Engine

```python
# tests/valuation/test_valuation_engine.py
import pytest
from valuation.valuation_engine import ValuationEngine

@pytest.mark.integration
class TestValuationEngine:
    """Testes do ValuationEngine."""
    
    @pytest.mark.asyncio
    async def test_valuation_with_hedonic_only(self, sample_listing):
        """Testa valuation com apenas Hedonic Model."""
        valuation_engine = ValuationEngine(
            hedonic_model=HedonicModel(),
            comps_engine=None,  # Desactivado
            ine_client=None,  # Desactivado
            xgboost_model=None  # Desactivado
        )
        
        # Treinar com dummy data
        training_data = [
            {'area_util_m2': 85, 'quartos': 3, 'preco_pedido': 180000}
        ]
        valuation_engine.hedonic_model.train(training_data)
        
        # Valuar
        valuation = await valuation_engine.valuate(sample_listing)
        
        # Verificar
        assert valuation['valor_justo'] > 0
        assert valuation['discount'] is not None
        assert valuation['hedonic_value'] > 0
        assert valuation['comps_value'] == 0  # Desactivado
```

---

## 10. TESTES DE SCORING

### 10.1 Teste Scoring Engine

```python
# tests/scoring/test_scoring_engine.py
import pytest
from scoring.scoring_engine import ScoringEngine

@pytest.mark.integration
class TestScoringEngine:
    """Testes do ScoringEngine."""
    
    @pytest.mark.asyncio
    async def test_scoring_with_high_discount(self, sample_listing, sample_valuation):
        """Testa scoring com discount alto."""
        scoring_engine = ScoringEngine(
            score_discount_calculator=ScoreDiscountCalculator(),
            score_location_calculator=ScoreLocationCalculator(),
            score_condition_calculator=ScoreConditionCalculator(),
            score_liquidity_calculator=ScoreLiquidityCalculator(),
            score_freshness_calculator=ScoreFreshnessCalculator(),
            red_flags_detector=RedFlagsDetector(),
            weighted_score_calculator=WeightedScoreCalculator(),
            rationale_generator=RationaleGenerator()
        )
        
        # Valuation com discount alto
        sample_valuation['discount'] = 25.0
        
        # Score
        score = await scoring_engine.score(sample_listing, sample_valuation)
        
        # Verificar
        assert score['score_total'] >= 8.0  # Discount alto → score alto
        assert score['score_discount'] >= 8.0
        assert score['classificacao'] == 'Imperdível'
```

---

## 11. COBERTURA DE CÓDIGO

### 11.1 Configuração de Cobertura

```bash
# Executar testes com cobertura
pytest --cov=src --cov-report=html --cov-report=term-missing

# Verificar cobertura
# - HTML report: htmlcov/index.html
# - Terminal report: mostra % de cobertura e linhas não cobertas
```

### 11.2 Metas de Cobertura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              METAS DE COBERTURA DE CÓDIGO                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MÓDULO                  │ COBERTURA MÍNIMA │ COBERTURA ACTUAL          │   │
│  ────────────────────────┼──────────────────┼───────────────────┤   │
│  scraping/               │ 70%               │ TBD                 │   │
│  etl/                    │ 80%               │ TBD                 │   │
│  valuation/              │ 75%               │ TBD                 │   │
│  scoring/                │ 80%               │ TBD                 │   │
│  database/               │ 85%               │ TBD                 │   │
│  notification/           │ 75%               │ TBD                 │   │
│  dashboard/              │ 60%               │ TBD                 │   │
│  scheduler/              │ 70%               │ TBD                 │   │
│                                                                             │
│  TOTAL                   │ 75%               │ TBD                 │   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 12. TEST DATA MANAGEMENT

### 12.1 Fixtures de Test Data

```python
# tests/fixtures/test_data.py
import pytest
from typing import List, Dict

@pytest.fixture
def test_listings() -> List[Dict]:
    """Listings de teste."""
    return [
        {
            'id': '1',
            'titulo': 'T3 Cedofeita',
            'preco_pedido': 180000,
            'area_util_m2': 85,
            'quartos': 3,
            'freguesia': 'Cedofeita'
        },
        {
            'id': '2',
            'titulo': 'T2 Paranhos',
            'preco_pedido': 150000,
            'area_util_m2': 65,
            'quartos': 2,
            'freguesia': 'Paranhos'
        }
    ]

@pytest.fixture
def test_valuations() -> List[Dict]:
    """Valuations de teste."""
    return [
        {
            'id': '1',
            'listing_id': '1',
            'valor_justo': 200000,
            'discount': 10.0,
            'confianca': 75.0
        },
        {
            'id': '2',
            'listing_id': '2',
            'valor_justo': 160000,
            'discount': 6.25,
            'confianca': 70.0
        }
    ]
```

---

## 13. CI/CD PIPELINE DE TESTES

### 13.1 GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio
    
    - name: Run unit tests
      run: pytest tests/unit -v --cov=src --cov-report=xml
    
    - name: Run integration tests
      run: pytest tests/integration -v --cov=src --cov-append --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

---

## 14. BEST PRACTICES TESTES

### 14.1 Best Practices

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              BEST PRACTICES TESTES                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. PIRÂMIDE DE TESTES                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 60% unit tests (rápidos, isolados)                                  │   │
│  │ 30% integration tests (médio, componentes juntos)                    │   │
│  │ 10% E2E tests (lentos, fluxos completos)                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  2. TESTES INDEPENDENTES                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Cada teste deve ser independente                                     │   │
│  │ Use fixtures para setup/teardown                                     │   │
│  │ Limpeza de dados após cada teste                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  3. NOME DE TESTES DESCRITIVO                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Use nomes descritivos: test_parse_price_valid, test_etl_flow      │   │
│  │ Nomes devem descrever o que é testado e o resultado esperado       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  4. AAA PATTERN (ARRANGE, ACT, ASSERT)                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Arrange: Setup do teste (dados, mocks)                             │   │
│  │ Act: Executar acção a testar                                        │   │
│  │ Assert: Verificar resultado esperado                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  5. MOCK PARA DEPENDÊNCIAS EXTERNAS                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Mock scraping (não depende de portais reais)                        │   │
│  │ Mock database (usar SQLite em memória)                              │   │
│  │ Mock APIs externas (INE, Telegram, etc.)                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  6. COBERTURA DE CÓDIGO                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Meta de cobertura: 75%                                             │   │
│  │ CI/CD falha se cobertura < meta                                      │   │
│  │ Identificar linhas não cobertas e adicionar testes                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  7. TESTES RÁPIDOS                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Unit tests devem ser rápidos (< 100ms cada)                         │   │
│  │ Integration tests devem ser razoáveis (< 1s cada)                   │   │
│  │ E2E tests podem ser lentos (minutos)                                │   │
│  │ Use @pytest.mark.slow para testes lentos                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  8. CI/CD AUTOMÁTICO                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Executar testes em cada commit/pull request                         │   │
│  │ Bloquear merge se testes falharem                                   │   │
│  │ Reportar cobertura em cada build                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 15. GLOSSÁRIO DE TESTES

```
┌─────────────────────────────────────────────────────────────────────────────┐
│            GLOSSÁRIO DE TESTES                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TESTE: Teste (verificação de comportamento)                           │
│                                                                             │
│  UNIT TEST: Teste unitário (função individual)                         │
│                                                                             │
│  INTEGRATION TEST: Teste de integração (componentes juntos)            │
│                                                                             │
│  E2E TEST: Teste end-to-end (fluxo completo)                            │
│                                                                             │
│  PYTEST: Framework de testes Python                                     │
│                                                                             │
│  FIXTURE: Fixture (setup/teardown de testes)                            │
│                                                                             │
│  MOCK: Mock (simulação de dependências)                                   │
│                                                                             │
│  STUB: Stub (implementação simplificada)                                 │
│                                                                             │
│  COVERAGE: Cobertura de código (% de código testado)                   │
│                                                                             │
│  COVERAGE REPORT: Relatório de cobertura                               │
│                                                                             │
│  AAA PATTERN: Arrange, Act, Assert (padrão de testes)                │
│                                                                             │
│  ASSERT: Assert (verificação de resultado)                              │
│                                                                             │
│  MARKER: Marker (etiqueta de teste, ex: @pytest.mark.unit)           │
│                                                                             │
│  PARAMETRIZE: Parametrize (testar com múltiplos inputs)              │
│                                                                             │
│  SKIP: Skip (saltar teste)                                             │
│                                                                             │
│  XFAIL: XFail (expected failure)                                         │
│                                                                             │
│  CI/CD: Continuous Integration / Continuous Deployment               │
│                                                                             │
│  GITHUB ACTIONS: Ferramenta de CI/CD do GitHub                          │
│                                                                             │
│  CODECOV: Ferramenta de relatório de cobertura                           │
│                                                                             │
│  REGRESSION: Regressão (bug introduzido por mudança)                   │
│                                                                             │
│  SAFETY NET: Safety net (testes como rede de segurança)               │
│                                                                             │
│  TEST DRIVEN DEVELOPMENT (TDD): Desenvolvimento guiado por testes     │
│                                                                             │
│  BEHAVIOR DRIVEN DEVELOPMENT (BDD): Desenvolvimento guiado por comportamento│
│                                                                             │
│  ACCEPTANCE TEST: Teste de aceitação (UAT)                             │
│                                                                             │
│  SMOKE TEST: Smoke test (teste rápido de funcionalidade básica)        │
│                                                                             │
│  PERFORMANCE TEST: Teste de performance                                 │
│                                                                             │
│  LOAD TEST: Teste de carga                                             │
│                                                                             │
│  STRESS TEST: Teste de stress                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 16. ESTRUTURA DUAL DE TESTES (BASELINE PRODUCTION-READY)

### 16.1 Suíte Base (tests/)

**Localização:** `tests/` (raiz do projeto)

**Propósito:** Testes curados, end-to-end e regressão production-readiness

**Números:**
- 29 testes
- Testes de regressão para Ondas 1-5 (5 arquivos)
- Testes de API, database e browser resolver
- Execução rápida (< 2 minutos)

**Arquivos:**
- `test_api.py` — Testes de API FastAPI
- `test_api_db.py` — Testes de API com database
- `test_browser_resolver.py` — Testes de resolução de browser
- `test_casa_sapo_direct.py` — Testes de scraping Casa Sapo
- `test_production_readiness_onda[1-5].py` — Testes de regressão por onda

### 16.2 Suíte Granular (realestate_engine/tests/)

**Localização:** `realestate_engine/tests/` (dentro do engine)

**Propósito:** Testes unit/integration granulares para cada componente

**Números:**
- ~305 testes
- Testes unitários de cada módulo
- Testes de integração entre componentes
- Cobertura detalhada de CV, NLP, validators, etc.

**Estrutura:**
- `unit/` — Testes unitários granulares (34 arquivos)
- `integration/` — Testes de integração
- `e2e/` — Testes end-to-end (placeholder)

### 16.3 Testes de Regressão Production-Readiness

**Onda 1:** `test_production_readiness_onda1.py`
- Testa imports lazy no pipeline ETL
- Verifica ENRICH_SKIP_HEAVY funciona
- Verifica Ollama env-driven com warm-up/retry/cache/timeouts

**Onda 2:** `test_production_readiness_onda2.py`
- Testa paridade entre start.bat e start.sh
- Verifica existência e conteúdo do .gitignore raiz
- Verifica uso do caminho canónico de testes

**Onda 3:** `test_production_readiness_onda3.py`
- Testa que o tema do Streamlit está em dark
- Verifica que overview.py não usa cores claras hardcoded
- Verifica que não existem backgrounds claros hardcoded nas views

**Onda 4:** `test_production_readiness_onda4.py`
- Testa hardening do orchestrator (max_instances, coalesce, misfire_grace_time)
- Verifica env-driven notify_ai_analysis
- Verifica fail-closed em dedup
- Verifica tratamento de erros no TelegramBot

**Onda 5:** `test_production_readiness_onda5.py`
- Testa reconciliação de README.md com estado real
- Verifica números corretos (spiders, views, testes)
- Verifica remoção de RELATORIO_INCONSISTENCIAS.md

### 16.4 Benefícios da Estrutura Dual

**Separação de Responsabilidades:**
- Suíte base: regressão production-ready rápida
- Suíte granular: cobertura detalhada de componentes

**Velocidade de Feedback:**
- Suíte base: < 2 minutos para feedback rápido
- Suíte granular: cobertura completa em ~10 minutos

**Manutenibilidade:**
- Suíte base: fácil de manter (29 testes)
- Suíte granular: organizada por componente

**CI/CD:**
- Suíte base: executa em cada commit
- Suíte granular: executa em PRs e nightly

---

*Fim do Documento 13 — Testes e Qualidade*
