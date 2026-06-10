# ETL PIPELINE — REAL ESTATE OPPORTUNITY ENGINE
## Pipeline de Dados: Extract, Transform, Load

> **Este documento:** Especificação completa do pipeline ETL  
> **Objectivo:** Fornecer especificação detalhada de ETL para IA implementar  
> **Linhas:** 1500+ linhas de documentação detalhada  
> **Versão:** 5.0 (Actualizado com Volume 13)

---

## ÍNDICE

1. [Introdução ao ETL](#1-introdução-ao-etl)
2. [Arquitectura do Pipeline](#2-arquitectura-do-pipeline)
3. [Componentes do ETL](#3-componentes-do-etl)
4. [Normalizer](#4-normalizer)
5. [Deduplicator](#5-deduplicator)
6. [Geocoder](#6-geocoder)
7. [Enricher](#7-enricher)
8. [Validator](#8-validator)
9. [Fluxo de Dados ETL](#9-fluxo-de-dados-etl)
10. [Performance ETL](#10-performance-etl)
11. [Error Handling ETL](#11-error-handling-etl)
12. [Cache ETL](#12-cache-etl)
13. [Batch Processing](#13-batch-processing)
14. [Monitoring ETL](#14-monitoring-etl)
15. [Glossário de ETL](#15-glossário-de-etl)

---

## 1. INTRODUÇÃO AO ETL

### 1.1 O Que é ETL?

**ETL** significa **Extract, Transform, Load**:
- **Extract:** Extrair dados de fontes externas (portais imobiliários)
- **Transform:** Transformar dados brutos em formato normalizado
- **Load:** Carregar dados transformados em database

No contexto do Real Estate Opportunity Engine:
- **Extract:** Scraping de 17 portais imobiliários (Nodriver)
- **Transform:** Normalização, deduplicação, geocodificação, enrichment, validação
- **Load:** Inserção em database (SQLite/PostgreSQL)

### 1.2 Porquê ETL?

**Problema sem ETL:**
- Dados brutos inconsistentes entre portais
- Duplicações (mesmo imóvel em múltiplos portais)
- Dados incompletos ou incorrectos
- Impossível usar dados directamente para valuation/scoring

**Solução com ETL:**
- Dados normalizados (formato canónico)
- Sem duplicações (cada imóvel único)
- Dados enriquecidos (INE, POIs)
- Dados validados (integridade garantida)
- Prontos para valuation/scoring

---

## 2. ARQUITECTURA DO PIPELINE

### 2.1 Pipeline ETL

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              PIPELINE ETL — VISÃO GERAL                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  RAW LISTINGS (raw_listings table)                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Dados brutos de scraping                                         │   │
│  │ - Formato JSON (variável por portal)                               │   │
│  │ - 50+ campos por listing                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  NORMALIZER                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Normaliza campos (preço, área, quartos)                         │   │
│  │ - Converte tipos (string → float, int)                             │   │
│  │ - Preenche valores em falta                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  DEDUPLICATOR                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Detecta duplicados (mesmo imóvel em múltiplos portais)          │   │
│  │ - Gera fingerprint (hash de campos únicos)                          │   │
│  │ - Mantém listing mais recente                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  GEOCODER                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Geocodifica morada → lat/lon                                      │   │
│  │ - Extrai freguesia, concelho                                         │   │
│  │ - Cache de geocodificações (Redis/local)                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  ENRICHER                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Enrich com dados INE (preço médio freguesia)                    │   │
│  │ - Enrich com POIs (escolas, metro, comércio)                        │   │
│  │ - Calcula preço por m²                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  VALIDATOR                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Valida integridade dos dados                                    │   │
│  │ - Remove listings inválidos                                       │   │
│  │ - Marca listings para review manual                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  CLEAN LISTINGS (clean_listings table)                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Dados normalizados e enriquecidos                                │   │
│  │ - Formato canónico (mesmo para todos os portais)                     │   │
│  │ - 60+ campos por listing                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 PipelineETL Class

```python
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class PipelineETL:
    """
    Pipeline ETL completo.
    
    Ordem:
    1. Normalizer
    2. Deduplicator
    3. Geocoder
    4. Enricher
    5. Validator
    """
    
    def __init__(
        self,
        normalizer: INormalizer,
        deduplicator: IDeduplicator,
        geocoder: IGeocoder,
        enricher: IEnricher,
        validator: IValidator,
        database_repository: IDatabaseRepository
    ):
        self.normalizer = normalizer
        self.deduplicator = deduplicator
        self.geocoder = geocoder
        self.enricher = enricher
        self.validator = validator
        self.database_repository = database_repository
    
    async def run(self) -> int:
        """Executa pipeline ETL completo."""
        logger.info("PipelineETL: Iniciando pipeline")
        
        # Step 1: Extract (já feito pelo scraping)
        raw_listings = await self.database_repository.get_raw_listings()
        logger.info(f"PipelineETL: {len(raw_listings)} raw listings")
        
        # Step 2: Transform
        clean_listings = []
        for raw_listing in raw_listings:
            try:
                # Normalizer
                normalized = self.normalizer.normalize(raw_listing)
                
                # Deduplicator
                if self.deduplicator.is_duplicate(normalized):
                    logger.debug(f"PipelineETL: Listing duplicado, ignorando")
                    continue
                
                # Geocoder
                geocoded = await self.geocoder.geocode(normalized)
                
                # Enricher
                enriched = await self.enricher.enrich(geocoded)
                
                # Validator
                is_valid, errors = self.validator.validate(enriched)
                if not is_valid:
                    logger.warning(f"PipelineETL: Listing inválido: {errors}")
                    continue
                
                clean_listings.append(enriched)
            
            except Exception as e:
                logger.error(f"PipelineETL: Erro ao processar listing: {e}")
                continue
        
        logger.info(f"PipelineETL: {len(clean_listings)} clean listings")
        
        # Step 3: Load
        await self.database_repository.insert_clean_listings(clean_listings)
        
        logger.info("PipelineETL: Pipeline completo")
        return len(clean_listings)
```

---

## 3. COMPONENTES DO ETL

### 3.1 Interfaces dos Componentes

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple

class INormalizer(ABC):
    @abstractmethod
    def normalize(self, raw_listing: Dict) -> Dict:
        """Normaliza um raw listing."""
        pass

class IDeduplicator(ABC):
    @abstractmethod
    def is_duplicate(self, listing: Dict) -> bool:
        """Verifica se listing é duplicado."""
        pass

class IGeocoder(ABC):
    @abstractmethod
    async def geocode(self, listing: Dict) -> Dict:
        """Geocodifica listing."""
        pass

class IEnricher(ABC):
    @abstractmethod
    async def enrich(self, listing: Dict) -> Dict:
        """Enrich listing com dados externos."""
        pass

class IValidator(ABC):
    @abstractmethod
    def validate(self, listing: Dict) -> Tuple[bool, List[str]]:
        """Valida listing."""
        pass
```

---

## 4. NORMALIZER

### 4.1 Responsabilidade

Normalizar dados brutos de scraping para formato canónico:
- Converter tipos (string → float, int)
- Normalizar campos (preço, área, quartos)
- Preencher valores em falta
- Padronizar formato de datas

### 4.2 Implementação

```python
import re
from datetime import datetime
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class Normalizer(INormalizer):
    """Normaliza raw listings para formato canónico."""
    
    def __init__(self):
        self.field_mappings = {
            # Mapeamento de campos (portal → canónico)
            'idealista': {
                'price': 'preco_pedido',
                'size': 'area_util_m2',
                'rooms': 'quartos',
            },
            'imovirtual': {
                'price': 'preco_pedido',
                'area': 'area_util_m2',
                'rooms': 'quartos',
            },
            # ... mais portais
        }
    
    def normalize(self, raw_listing: Dict) -> Dict:
        """Normaliza um raw listing."""
        normalized = {}
        
        # Identificar portal
        source_portal = raw_listing.get('source_portal', '')
        
        # Mapear campos
        field_mapping = self.field_mappings.get(source_portal, {})
        for raw_field, canonical_field in field_mapping.items():
            if raw_field in raw_listing:
                normalized[canonical_field] = raw_listing[raw_field]
        
        # Normalizar preço
        if 'preco_pedido' in normalized:
            normalized['preco_pedido'] = self._parse_price(normalized['preco_pedido'])
        
        # Normalizar área
        if 'area_util_m2' in normalized:
            normalized['area_util_m2'] = self._parse_area(normalized['area_util_m2'])
        
        # Normalizar quartos
        if 'quartos' in normalized:
            normalized['quartos'] = self._parse_rooms(normalized['quartos'])
        
        # Normalizar data
        if 'scrape_timestamp' in normalized:
            normalized['scrape_timestamp'] = self._parse_date(normalized['scrape_timestamp'])
        
        # Preencher valores em falta
        normalized = self._fill_missing_values(normalized)
        
        return normalized
    
    def _parse_price(self, price: Any) -> float:
        """Parse preço para float."""
        if isinstance(price, (int, float)):
            return float(price)
        
        if isinstance(price, str):
            # Remover símbolos e espaços
            price = price.replace("€", "").replace(".", "").replace(" ", "").strip()
            try:
                return float(price)
            except ValueError:
                return 0.0
        
        return 0.0
    
    def _parse_area(self, area: Any) -> float:
        """Parse área para float."""
        if isinstance(area, (int, float)):
            return float(area)
        
        if isinstance(area, str):
            # Extrair número antes de "m²"
            match = re.search(r"([\d.,]+)", area.replace(".", "").replace(",", "."))
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    return 0.0
        
        return 0.0
    
    def _parse_rooms(self, rooms: Any) -> int:
        """Parse quartos para int."""
        if isinstance(rooms, int):
            return rooms
        
        if isinstance(rooms, str):
            match = re.search(r"(\d+)", rooms)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    return 0
        
        return 0
    
    def _parse_date(self, date_str: Any) -> str:
        """Parse data para ISO format."""
        if isinstance(date_str, str):
            try:
                # Tentar parsear data
                dt = datetime.fromisoformat(date_str)
                return dt.isoformat()
            except ValueError:
                # Se falhar, retornar data actual
                return datetime.now().isoformat()
        
        if isinstance(date_str, datetime):
            return date_str.isoformat()
        
        return datetime.now().isoformat()
    
    def _fill_missing_values(self, listing: Dict) -> Dict:
        """Preenche valores em falta com defaults."""
        defaults = {
            'casas_banho': 0,
            'estado': 'Desconhecido',
            'ano_construcao': None,
            'cert_energetico': None,
            'fotos_urls': [],
            'num_fotos': 0,
            'agencia': '',
            'descricao': '',
        }
        
        for field, default_value in defaults.items():
            if field not in listing or listing[field] is None:
                listing[field] = default_value
        
        return listing
```

---

## 5. DEDUPLICATOR

### 5.1 Responsabilidade

Detectar duplicados (mesmo imóvel em múltiplos portais):
- Gerar fingerprint (hash de campos únicos)
- Comparar fingerprints
- Manter listing mais recente (baseado em scrape_timestamp)

### 5.2 Implementação

```python
import hashlib
from typing import Dict, Set
import logging

logger = logging.getLogger(__name__)

class Deduplicator(IDeduplicator):
    """Detecta duplicados usando fingerprinting."""
    
    def __init__(self):
        self.seen_fingerprints: Set[str] = set()
        self.fingerprint_metadata: Dict[str, Dict] = {}
    
    def is_duplicate(self, listing: Dict) -> bool:
        """Verifica se listing é duplicado."""
        fingerprint = self._generate_fingerprint(listing)
        
        if fingerprint in self.seen_fingerprints:
            # Verificar se listing actual é mais recente
            existing = self.fingerprint_metadata[fingerprint]
            current_timestamp = listing.get('scrape_timestamp', '')
            
            if current_timestamp > existing['scrape_timestamp']:
                # Listing actual é mais recente, actualizar
                logger.debug(f"Deduplicator: Listing mais recente, actualizando")
                self.fingerprint_metadata[fingerprint] = {
                    'scrape_timestamp': current_timestamp,
                    'listing_id': listing.get('id', '')
                }
                return False  # Não é duplicado (é mais recente)
            
            return True  # É duplicado (mais antigo)
        
        # Primeira vez visto
        self.seen_fingerprints.add(fingerprint)
        self.fingerprint_metadata[fingerprint] = {
            'scrape_timestamp': listing.get('scrape_timestamp', ''),
            'listing_id': listing.get('id', '')
        }
        
        return False
    
    def _generate_fingerprint(self, listing: Dict) -> str:
        """
        Gera fingerprint do listing.
        
        Campos usados para fingerprint:
        - morada_raw
        - area_util_m2
        - quartos
        - preco_pedido
        """
        key = (
            f"{listing.get('morada_raw', '')}_"
            f"{listing.get('area_util_m2', 0)}_"
            f"{listing.get('quartos', 0)}_"
            f"{listing.get('preco_pedido', 0)}"
        )
        
        return hashlib.sha256(key.encode()).hexdigest()[:32]
    
    def reset(self):
        """Reseta fingerprints (útil para testes)."""
        self.seen_fingerprints.clear()
        self.fingerprint_metadata.clear()
        logger.info("Deduplicator: Fingerprints reset")
```

---

## 6. GEOCODER

### 6.1 Responsabilidade

Geocodificar morada → lat/lon + freguesia:
- Usar Nominatim (OpenStreetMap) - gratuito
- Cache de geocodificações (local)
- Fallback: usar freguesia do portal se geocodificação falhar

### 6.2 Implementação

```python
import aiohttp
from typing import Dict, Tuple, Optional
import logging
import asyncio

logger = logging.getLogger(__name__)

class Geocoder(IGeocoder):
    """Geocodifica moradas usando Nominatim."""
    
    def __init__(self):
        self.cache: Dict[str, Tuple[float, float, str]] = {}
        self.nominatim_url = "https://nominatim.openstreetmap.org/search"
    
    async def geocode(self, listing: Dict) -> Dict:
        """Geocodifica listing."""
        morada = listing.get('morada_raw', '')
        
        if not morada:
            logger.warning("Geocoder: Morada vazia, usando defaults")
            return self._add_geocoding_defaults(listing)
        
        # Verificar cache
        if morada in self.cache:
            lat, lon, freguesia = self.cache[morada]
            listing['lat'] = lat
            listing['lon'] = lon
            listing['freguesia'] = freguesia
            return listing
        
        # Geocodificar com Nominatim
        try:
            lat, lon, freguesia = await self._geocode_nominatim(morada)
            
            # Guardar no cache
            self.cache[morada] = (lat, lon, freguesia)
            
            # Adicionar ao listing
            listing['lat'] = lat
            listing['lon'] = lon
            listing['freguesia'] = freguesia
            
            logger.debug(f"Geocoder: Geocodificado {morada} → ({lat}, {lon})")
            
        except Exception as e:
            logger.error(f"Geocoder: Erro ao geocodificar {morada}: {e}")
            # Usar defaults se geocodificação falhar
            listing = self._add_geocoding_defaults(listing)
        
        return listing
    
    async def _geocode_nominatim(self, morada: str) -> Tuple[float, float, str]:
        """Geocodifica usando Nominatim."""
        async with aiohttp.ClientSession() as session:
            params = {
                'q': f"{morada}, Portugal",
                'format': 'json',
                'countrycodes': 'pt',
                'limit': 1
            }
            
            async with session.get(self.nominatim_url, params=params) as response:
                data = await response.json()
                
                if not data:
                    return (0.0, 0.0, '')
                
                result = data[0]
                lat = float(result.get('lat', 0.0))
                lon = float(result.get('lon', 0.0))
                
                # Extrair freguesia
                address = result.get('address', {})
                freguesia = self._extract_freguesia(address)
                
                return (lat, lon, freguesia)
    
    def _extract_freguesia(self, address: Dict) -> str:
        """Extrai freguesia do address."""
        # Tenta extrair freguesia do address
        freguesia = address.get('suburb', '')
        
        if not freguesia:
            freguesia = address.get('city_district', '')
        
        return freguesia
    
    def _add_geocoding_defaults(self, listing: Dict) -> Dict:
        """Adiciona defaults se geocodificação falhar."""
        listing['lat'] = 0.0
        listing['lon'] = 0.0
        listing['freguesia'] = listing.get('freguesia', '')  # Usa freguesia do portal
        return listing
```

---

## 7. ENRICHER

### 7.1 Responsabilidade

Enrich listings com dados externos:
- Dados INE (preço médio por m² da freguesia)
- POIs (escolas, metro, comércio)
- Cálculo de preço por m²

### 7.2 Implementação

```python
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class Enricher(IEnricher):
    """Enrich listings com dados externos."""
    
    def __init__(self, ine_client=None, poi_client=None):
        self.ine_client = ine_client
        self.poi_client = poi_client
    
    async def enrich(self, listing: Dict) -> Dict:
        """Enrich listing com dados externos."""
        enriched = listing.copy()
        
        # Calcular preço por m²
        enriched['preco_por_m2'] = self._calculate_price_per_m2(listing)
        
        # Enrich com dados INE
        if self.ine_client:
            try:
                ine_data = await self.ine_client.get_freguesia_data(
                    listing.get('freguesia', '')
                )
                enriched.update(ine_data)
            except Exception as e:
                logger.error(f"Enricher: Erro ao obter dados INE: {e}")
        
        # Enrich com POIs
        if self.poi_client and listing.get('lat', 0) != 0:
            try:
                pois = await self.poi_client.get_nearby_pois(
                    listing['lat'],
                    listing['lon']
                )
                enriched.update(pois)
            except Exception as e:
                logger.error(f"Enricher: Erro ao obter POIs: {e}")
        
        return enriched
    
    def _calculate_price_per_m2(self, listing: Dict) -> float:
        """Calcula preço por m²."""
        preco = listing.get('preco_pedido', 0)
        area = listing.get('area_util_m2', 0)
        
        if area > 0:
            return preco / area
        
        return 0.0
```

---

## 8. VALIDATOR

### 8.1 Responsabilidade

Validar integridade dos dados:
- Verificar campos obrigatórios
- Verificar ranges válidos
- Marcar listings inválidos
- Marcar listings para review manual

### 8.2 Implementação

```python
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class Validator(IValidator):
    """Valida integridade dos dados."""
    
    REQUIRED_FIELDS = [
        'id', 'source_portal', 'source_id', 'source_url',
        'scrape_timestamp', 'preco_pedido', 'area_util_m2', 'quartos'
    ]
    
    def validate(self, listing: Dict) -> Tuple[bool, List[str]]:
        """Valida listing."""
        errors = []
        
        # Verificar campos obrigatórios
        for field in self.REQUIRED_FIELDS:
            if field not in listing or listing[field] is None:
                errors.append(f"Campo obrigatório ausente: {field}")
        
        # Verificar preço
        preco = listing.get('preco_pedido', 0)
        if preco <= 0:
            errors.append("Preço deve ser > 0")
        elif preco > 10000000:  # 10 milhões
            errors.append("Preço suspeito (> 10M€)")
        
        # Verificar área
        area = listing.get('area_util_m2', 0)
        if area <= 0:
            errors.append("Área deve ser > 0")
        elif area > 1000:  # 1000 m²
            errors.append("Área suspeita (> 1000 m²)")
        
        # Verificar quartos
        quartos = listing.get('quartos', 0)
        if quartos < 0:
            errors.append("Quartos deve ser ≥ 0")
        elif quartos > 20:  # 20 quartos
            errors.append("Quartos suspeito (> 20)")
        
        # Verificar lat/lon
        lat = listing.get('lat', 0)
        lon = listing.get('lon', 0)
        if not (-90 <= lat <= 90):
            errors.append("Lat deve estar entre -90 e 90")
        if not (-180 <= lon <= 180):
            errors.append("Lon deve estar entre -180 e 180")
        
        return (len(errors) == 0, errors)
```

---

## 9. FLUXO DE DADOS ETL

### 9.1 Fluxo Completo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              FLUXO DE DADOS ETL DETALHADO                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. EXTRACT (já feito pelo scraping)                                    │
│     ┌───────────────────────────────────────────────────────────────────┐  │
│     │ SELECT * FROM raw_listings                                       │  │
│     │ WHERE created_at > (NOW() - INTERVAL '30 minutes')               │  │
│     │                                                                   │  │
│     │ Resultado: 5000-8000 raw listings                                │  │
│     └───────────────────────────────────────────────────────────────────┘  │
│                              │                                            │   │
│                              ▼                                            │   │
│  2. NORMALIZER                                                             │
│     ┌───────────────────────────────────────────────────────────────────┐  │
│     │ Para cada raw listing:                                          │  │
│     │   - Mapear campos (portal → canónico)                            │  │
│     │   - Parse preço (string → float)                                  │  │
│     │   - Parse área (string → float)                                   │  │
│     │   - Parse quartos (string → int)                                  │  │
│     │   - Parse data (string → ISO format)                              │  │
│     │   - Preencher valores em falta                                    │  │
│     │                                                                   │  │
│     │ Resultado: 5000-8000 normalized listings                         │  │
│     └───────────────────────────────────────────────────────────────────┘  │
│                              │                                            │   │
│                              ▼                                            │   │
│  3. DEDUPLICATOR                                                           │
│     ┌───────────────────────────────────────────────────────────────────┐  │
│     │ Para cada normalized listing:                                    │  │
│     │   - Gerar fingerprint (hash de morada + área + quartos + preço)  │  │
│     │   - Verificar se fingerprint já visto                             │  │
│     │   - Se sim → ignorar (duplicado)                                │  │
│     │   - Se não → manter                                              │  │
│     │   - Se mais recente → actualizar                                  │  │
│     │                                                                   │  │
│     │ Resultado: 4000-6000 unique listings (remove 20-30% duplicados)   │  │
│     └───────────────────────────────────────────────────────────────────┘  │
│                              │                                            │   │
│                              ▼                                            │   │
│  4. GEOCODER                                                               │
│     ┌───────────────────────────────────────────────────────────────────┐  │
│     │ Para cada unique listing:                                        │  │
│     │   - Verificar cache de geocodificação                             │  │
│     │   - Se no cache → geocodificar com Nominatim                      │  │
│     │   - Extrair lat, lon, freguesia                                   │  │
│     │   - Guardar no cache                                              │  │
│     │   - Se falhar → usar freguesia do portal                          │  │
│     │                                                                   │  │
│     │ Resultado: 4000-6000 geocoded listings (95% sucesso, 5% fallback)   │  │
│     └───────────────────────────────────────────────────────────────────┘  │
│                              │                                            │   │
│                              ▼                                            │   │
│  5. ENRICHER                                                               │
│     ┌───────────────────────────────────────────────────────────────────┐  │
│     │ Para cada geocoded listing:                                      │  │
│     │   - Calcular preço por m²                                         │  │
│     │   - Enrich com dados INE (preço médio freguesia)                  │  │
│     │   - Enrich com POIs (distância metro, escolas, comércio)         │  │
│     │                                                                   │  │
│     │ Resultado: 4000-6000 enriched listings (90% sucesso, 10% sem dados)│  │
│     └───────────────────────────────────────────────────────────────────┘  │
│                              │                                            │   │
│                              ▼                                            │   │
│  6. VALIDATOR                                                              │
│     ┌───────────────────────────────────────────────────────────────────┐  │
│     │ Para cada enriched listing:                                      │  │
│     │   - Verificar campos obrigatórios                                │  │
│     │   - Verificar ranges válidos                                    │  │
│     │   - Se inválido → marcar para review manual                      │  │
│     │   - Se válido → manter                                           │  │
│     │                                                                   │  │
│     │ Resultado: 3800-5700 valid listings (remove 5% inválidos)         │  │
│     └───────────────────────────────────────────────────────────────────┘  │
│                              │                                            │   │
│                              ▼                                            │   │
│  7. LOAD                                                                    │
│     ┌───────────────────────────────────────────────────────────────────┐  │
│     │ INSERT INTO clean_listings (3800-5700 listings)                │  │
│     │                                                                   │  │
│     │ Resultado: 3800-5700 clean listings na database                  │  │
│     └───────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  TOTAL: 5000-8000 raw listings → 3800-5700 clean listings (76-71%)        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. PERFORMANCE ETL

### 10.1 Métricas de Performance

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              MÉTRICAS DE PERFORMANCE ETL                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  NORMALIZER:                                                               │
│  - Tempo por listing: < 0.001 segundos                                    │
│  - 1000 listings: < 1 segundo                                             │
│  - 5000 listings: < 5 segundos                                            │
│                                                                             │
│  DEDUPLICATOR:                                                             │
│  - Tempo por listing: < 0.0005 segundos                                   │
│  - 1000 listings: < 0.5 segundos                                         │
│  - 5000 listings: < 2.5 segundos                                          │
│                                                                             │
│  GEOCODER:                                                                │
│  - Tempo por listing (cache hit): < 0.0001 segundos                      │
│  - Tempo por listing (cache miss): 1-2 segundos                            │
│  - 1000 listings (80% cache hit): < 0.5 segundos                         │
│  - 5000 listings (80% cache hit): < 2.5 segundos                         │
│                                                                             │
│  ENRICHER:                                                                │
│  - Tempo por listing (INE + POIs): 0.5-1 segundos                         │
│  - 1000 listings: 500-1000 segundos (8-17 minutos)                       │
│  - 5000 listings: 2500-5000 segundos (42-83 minutos)                     │
│                                                                             │
│  VALIDATOR:                                                               │
│  - Tempo por listing: < 0.001 segundos                                    │
│  - 1000 listings: < 1 segundo                                             │
│  - 5000 listings: < 5 segundos                                            │
│                                                                             │
│  TOTAL ETL:                                                                │
│  - 1000 listings: < 2 minutos (sem cache), < 1 minuto (com cache)        │
│  - 5000 listings: < 10 minutos (sem cache), < 5 minutos (com cache)      │
│                                                                             │
│  OPTIMIZAÇÃO:                                                            │
│  - Batch geocoding (10 requests em paralelo)                              │
│  - Cache de geocodificações (80% hit rate)                                │
│  - Lazy loading de dados externos (INE, POIs)                            │
│  - Resultado: 50% redução de tempo                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 11. ERROR HANDLING ETL

### 11.1 Estratégias de Error Handling

```python
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class ETLErrorHandler:
    """Gestão de erros no pipeline ETL."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def handle_error(self, listing: Dict, component: str, error: Exception):
        """Regista erro de ETL."""
        error_entry = {
            'listing_id': listing.get('id', ''),
            'component': component,
            'error': str(error),
            'timestamp': datetime.now().isoformat()
        }
        self.errors.append(error_entry)
        
        logger.error(
            f"ETLErrorHandler: Erro em {component} para listing {listing.get('id', '')}: {error}"
        )
    
    def handle_warning(self, listing: Dict, component: str, warning: str):
        """Regista warning de ETL."""
        warning_entry = {
            'listing_id': listing.get('id', ''),
            'component': component,
            'warning': warning,
            'timestamp': datetime.now().isoformat()
        }
        self.warnings.append(warning_entry)
        
        logger.warning(
            f"ETLErrorHandler: Warning em {component} para listing {listing.get('id', '')}: {warning}"
        )
    
    def get_error_rate(self) -> float:
        """Calcula taxa de erro."""
        total = len(self.errors) + len(self.warnings)
        if total == 0:
            return 0.0
        return (len(self.errors) / total) * 100
    
    def get_summary(self) -> Dict:
        """Retorna resumo de erros."""
        return {
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'error_rate': self.get_error_rate(),
            'errors_by_component': self._get_errors_by_component()
        }
    
    def _get_errors_by_component(self) -> Dict[str, int]:
        """Retorna erros por componente."""
        component_errors = {}
        for error in self.errors:
            component = error['component']
            component_errors[component] = component_errors.get(component, 0) + 1
        return component_errors
```

---

## 12. CACHE ETL

### 12.1 Cache de Geocodificações

```python
import json
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class GeocodeCache:
    """Cache de geocodificações."""
    
    def __init__(self, cache_file: str = 'data/cache/geocode_cache.json'):
        self.cache_file = cache_file
        self.cache: Dict[str, Tuple[float, float, str]] = {}
        self._load_cache()
    
    def _load_cache(self):
        """Carrega cache do ficheiro."""
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
                self.cache = {
                    k: (v[0], v[1], v[2])
                    for k, v in data.items()
                }
            logger.info(f"GeocodeCache: Cache carregado com {len(self.cache)} entradas")
        except FileNotFoundError:
            logger.info("GeocodeCache: Cache não encontrado, iniciando vazio")
        except Exception as e:
            logger.error(f"GeocodeCache: Erro ao carregar cache: {e}")
    
    def _save_cache(self):
        """Guarda cache no ficheiro."""
        try:
            data = {
                k: [v[0], v[1], v[2]]
                for k, v in self.cache.items()
            }
            with open(self.cache_file, 'w') as f:
                json.dump(data, f)
            logger.info(f"GeocodeCache: Cache guardado com {len(self.cache)} entradas")
        except Exception as e:
            logger.error(f"GeocodeCache: Erro ao guardar cache: {e}")
    
    def get(self, morada: str) -> Optional[Tuple[float, float, str]]:
        """Retorna geocodificação do cache."""
        return self.cache.get(morada)
    
    def set(self, morada: str, lat: float, lon: float, freguesia: str):
        """Guarda geocodificação no cache."""
        self.cache[morada] = (lat, lon, freguesia)
        self._save_cache()
    
    def clear(self):
        """Limpa cache."""
        self.cache.clear()
        self._save_cache()
        logger.info("GeocodeCache: Cache limpo")
```

---

## 13. BATCH PROCESSING

### 13.1 Batch Processing

```python
import asyncio
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class BatchProcessor:
    """Processamento em batch para performance."""
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
    
    async def process_batch(
        self,
        items: List[Dict],
        process_func,
        max_concurrent: int = 10
    ) -> List[Dict]:
        """
        Processa items em batch.
        
        Args:
            items: Lista de items a processar
            process_func: Função async para processar cada item
            max_concurrent: Número máximo de tarefas em paralelo
        """
        results = []
        
        # Dividir em batches
        batches = [
            items[i:i + self.batch_size]
            for i in range(0, len(items), self.batch_size)
        ]
        
        for batch in batches:
            # Processar batch em paralelo
            tasks = [process_func(item) for item in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filtrar erros
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"BatchProcessor: Erro ao processar item: {result}")
                else:
                    results.append(result)
        
        return results
```

---

## 14. MONITORING ETL

### 14.1 Métricas ETL

```python
from datetime import datetime
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class ETLMetrics:
    """Métricas do pipeline ETL."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.raw_count = 0
        self.normalized_count = 0
        self.duplicate_count = 0
        self.geocoded_count = 0
        self.enriched_count = 0
        self.valid_count = 0
        self.invalid_count = 0
    
    def start(self):
        """Inicia medição."""
        self.start_time = datetime.now()
    
    def end(self):
        """Termina medição."""
        self.end_time = datetime.now()
    
    def get_duration(self) -> float:
        """Retorna duração em segundos."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    def get_throughput(self) -> float:
        """Retorna throughput (listings/segundo)."""
        duration = self.get_duration()
        if duration > 0:
            return self.valid_count / duration
        return 0.0
    
    def get_summary(self) -> Dict:
        """Retorna resumo de métricas."""
        return {
            'duration_seconds': self.get_duration(),
            'raw_count': self.raw_count,
            'normalized_count': self.normalized_count,
            'duplicate_count': self.duplicate_count,
            'geocoded_count': self.geocoded_count,
            'enriched_count': self.enriched_count,
            'valid_count': self.valid_count,
            'invalid_count': self.invalid_count,
            'throughput_listings_per_second': self.get_throughput(),
            'duplicate_rate': (self.duplicate_count / self.raw_count * 100) if self.raw_count > 0 else 0,
            'invalid_rate': (self.invalid_count / self.normalized_count * 100) if self.normalized_count > 0 else 0
        }
```

---

## 15. LAZY IMPORTS & ENRICH_SKIP_HEAVY (ONDA 1)

### 15.1 Lazy Imports no Pipeline ETL

**Problema:**
- O pipeline ETL usa torch, transformers e opencv para enriquecimento pesado (CV/NLP)
- Essas dependências são pesadas (torch: 2GB+, transformers: 500MB+, opencv: 100MB+)
- Carregar essas bibliotecas no startup do sistema aumenta tempo de boot significativamente
- Utilizadores que não precisam de CV/NLP não devem pagar esse custo

**Solução:**
- Imports lazy: carregar torch/transformers/opencv apenas quando necessário
- Variável `ENRICH_SKIP_HEAVY`: desabilitar enriquecimento pesado se desejado
- Extras opcionais no requirements.txt para slim install

### 15.2 Implementação Lazy Imports

```python
# realestate_engine/etl/enricher.py
from typing import Optional

class Enricher:
    def __init__(self):
        self._cv_analyzer = None
        self._nlp_analyzer = None
        
    @property
    def cv_analyzer(self):
        """Lazy load CV analyzer (opencv)."""
        if self._cv_analyzer is None and not os.getenv("ENRICH_SKIP_HEAVY"):
            from realestate_engine.cv.image_quality import ImageQualityAnalyzer
            self._cv_analyzer = ImageQualityAnalyzer()
        return self._cv_analyzer
    
    @property
    def nlp_analyzer(self):
        """Lazy load NLP analyzer (transformers)."""
        if self._nlp_analyzer is None and not os.getenv("ENRICH_SKIP_HEAVY"):
            from realestate_engine.nlp.text_similarity import TextSimilarityAnalyzer
            self._nlp_analyzer = TextSimilarityAnalyzer()
        return self._nlp_analyzer
    
    async def enrich(self, listing: dict) -> dict:
        """Enrich listing com dados externos."""
        # Enrichment básico (sempre executado)
        listing = await self._enrich_ine_data(listing)
        listing = await self._enrich_pois(listing)
        
        # Enrichment pesado (opcional)
        if not os.getenv("ENRICH_SKIP_HEAVY"):
            if self.cv_analyzer:
                listing = await self._enrich_image_quality(listing)
            if self.nlp_analyzer:
                listing = await self._enrich_text_similarity(listing)
        
        return listing
```

### 15.3 Variável ENRICH_SKIP_HEAVY

**Configuração:**
```env
# .env
ENRICH_SKIP_HEAVY=false  # true para desabilitar CV/NLP
```

**Impacto:**
- `ENRICH_SKIP_HEAVY=false` (default): CV/NLP activos, enriquecimento completo
- `ENRICH_SKIP_HEAVY=true`: CV/NLP desactivados, apenas enriquecimento básico (INE, POIs)

**Quando usar `ENRICH_SKIP_HEAVY=true`:**
- Sistema com recursos limitados (CPU, RAM)
- Utilizador não precisa de análise de imagens/texto
- Ambiente de desenvolvimento/teste
- Deploy sem GPU (torch CPU-bound é lento)

### 15.4 Extras Opcionais no requirements.txt

```txt
# requirements.txt

# Core dependencies (sempre instaladas)
pandas>=2.2.0
numpy>=1.26.0
sqlalchemy>=2.0.25
apscheduler>=3.10.4
loguru>=0.7.2
fastapi>=0.109.0
streamlit>=1.31.0
python-telegram-bot>=20.7

# Heavy dependencies (opcionais)
[heavy]
torch>=2.1.0
transformers>=4.36.0
opencv-python>=4.9.0
pillow>=10.2.0

# Slim install (sem heavy deps)
# pip install -r requirements.txt
# Full install (com heavy deps)
# pip install -r requirements.txt[heavy]
```

### 15.5 Benefícios

**Performance:**
- Startup time reduzido em 30-60 segundos (sem torch/transformers)
- Memória reduzida em 2-3GB (sem torch/transformers/opencv)
- Sistema mais responsivo para utilizadores que não precisam de CV/NLP

**Flexibilidade:**
- Utilizador pode escolher entre slim install e full install
- Variável `ENRICH_SKIP_HEAVY` permite desabilitar enriquecimento pesado em runtime
- Facilita desenvolvimento e testes

---

## 16. GLOSSÁRIO DE ETL

```
┌─────────────────────────────────────────────────────────────────────────────┐
│            GLOSSÁRIO DE ETL                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ETL: Extract, Transform, Load (pipeline de dados)                       │
│                                                                             │
│  EXTRACT: Extracção de dados de fontes externas                          │
│                                                                             │
│  TRANSFORM: Transformação de dados brutos em formato normalizado         │
│                                                                             │
│  LOAD: Carregamento de dados transformados em database                    │
│                                                                             │
│  NORMALIZER: Componente que normaliza dados (tipos, formatos)           │
│                                                                             │
│  DEDUPLICATOR: Componente que detecta duplicados                        │
│                                                                             │
│  FINGERPRINT: Hash único para identificar duplicados                       │
│                                                                             │
│  GEOCODER: Componente que geocodifica moradas → lat/lon                   │
│                                                                             │
│  NOMINATIM: Serviço de geocodificação gratuito (OpenStreetMap)         │
│                                                                             │
│  ENRICHER: Componente que enrich dados com dados externos                  │
│                                                                             │
│  INE: Instituto Nacional de Estatística (Portugal)                         │
│                                                                             │
│  POI: Point of Interest (ponto de interesse)                              │
│                                                                             │
│  VALIDATOR: Componente que valida integridade dos dados                   │
│                                                                             │
│  CACHE: Armazenamento temporário de dados para performance                │
│                                                                             │
│  BATCH PROCESSING: Processamento em lotes para performance                │
│                                                                             │
│  ERROR HANDLING: Gestão de erros no pipeline                             │
│                                                                             │
│  METRICS: Métricas de performance e qualidade                             │
│                                                                             │
│  THROUGHPUT: Volume de dados processados por unidade de tempo             │
│                                                                             │
│  DUPLICATE RATE: Percentagem de duplicados detectados                       │
│                                                                             │
│  INVALID RATE: Percentagem de listings inválidos                         │
│                                                                             │
│  SUCCESS RATE: Percentagem de listings processados com sucesso            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*Fim do Documento 05 — ETL Pipeline*
