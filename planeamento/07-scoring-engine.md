# SCORING ENGINE — REAL ESTATE OPPORTUNITY ENGINE
## Motor de Scoring: 5 Factores, Red Flags e Classificação

> **Este documento:** Especificação completa do motor de scoring  
> **Objectivo:** Fornecer especificação detalhada de scoring para IA implementar  
> **Linhas:** 1500+ linhas de documentação detalhada  
> **Versão:** 5.0 (Actualizado com Volume 13)

---

## ÍNDICE

1. [Introdução ao Scoring Engine](#1-introducao-ao-scoring-engine)
2. [Arquitectura de Scoring](#2-arquitetura-de-scoring)
3. [Factor 1: Score Discount](#3-factor-1-score-discount)
4. [Factor 2: Score Location](#4-factor-2-score-location)
5. [Factor 3: Score Condition](#5-factor-3-score-condition)
6. [Factor 4: Score Liquidity](#6-factor-4-score-liquidity)
7. [Factor 5: Score Freshness](#7-factor-5-score-freshness)
8. [Red Flags Detector](#8-red-flags-detector)
9. [Weighted Score Calculator](#9-weighted-score-calculator)
10. [Rationale Generator](#10-rationale-generator)
11. [Classificação](#11-classificacao)
12. [Performance Scoring](#12-performance-scoring)
13. [Thresholds de Scoring](#13-thresholds-de-scoring)
14. [A/B Testing de Scoring](#14-ab-testing-de-scoring)
15. [Glossário de Scoring](#15-glossario-de-scoring)

---

## 1. INTRODUÇÃO AO SCORING ENGINE

### 1.1 O Que é Scoring Engine?

**Scoring Engine** é o motor que calcula um **score de 0-10** para cada imóvel, baseado em 5 factores principais. O score indica o quão "imperdível" é o imóvel como oportunidade de investimento.

**Objectivo:** Priorizar listings para o utilizador, destacando os melhores oportunidades (score 8-10 = "Imperdível").

### 1.2 Porquê Scoring Engine?

**Problema sem Scoring Engine:**
- 5000-8000 listings/dia → impossível analisar todos
- Sem priorização → utilizador perde tempo em listings irrelevantes
- Sem contexto → não sabe porquê um listing é bom/ruim

**Solução com Scoring Engine:**
- Score 0-10 para cada listing
- Top 3-5 listings/dia notificados (score ≥ 8)
- Rationale explicando porquê score é X
- Red flags automáticos (overpricing, localização má, etc.)

---

## 2. ARQUITECTURA DE SCORING

### 2.1 Arquitectura de 5 Factores

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              ARQUITECTURA DE SCORING (5 FACTORES)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FACTOR 1: SCORE DISCOUNT (30% peso)                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Calcula score de discount (0-10)                                     │   │
│  │ Discount ≥ 20% = score 8-10                                         │   │
│  │ Discount 10-19% = score 6-7.9                                       │   │
│  │ Discount 5-9% = score 4-5.9                                         │   │
│  │ Discount < 5% = score 0-3.9                                         │   │
│  │ Overpricing = score 0                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  FACTOR 2: SCORE LOCATION (25% peso)                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Calcula score de localização (0-10)                                 │   │
│  │ Fatores: freguesia, distância metro, POIs, segurança                 │   │
│  │ Freguesias alta procura = score 8-10                                │   │
│  │ Freguesias média procura = score 6-7.9                              │   │
│  │ Freguesias baixa procura = score 4-5.9                              │   │
│  │ Freguesias muito baixa procura = score 0-3.9                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  FACTOR 3: SCORE CONDITION (15% peso)                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Calcula score de estado (0-10)                                      │   │
│  │ Fatores: estado conservação, ano construção, cert. energ.          │   │
│  │ Novo/Renovado = score 8-10                                           │   │
│  │ Bom = score 6-7.9                                                    │   │
│  │ Aceitável = score 4-5.9                                              │   │
│  │ Ruim = score 0-3.9                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  FACTOR 4: SCORE LIQUIDITY (15% peso)                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Calcula score de liquidez (0-10)                                   │   │
│  │ Fatores: tempo médio venda, volume transações, taxa vendidos        │   │
│  │ Tempo < 60 dias, volume alto = score 8-10                            │   │
│  │ Tempo 60-90 dias, volume médio = score 6-7.9                         │   │
│  │ Tempo 90-120 dias, volume baixo = score 4-5.9                        │   │
│  │ Tempo > 120 dias, volume muito baixo = score 0-3.9                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  FACTOR 5: SCORE FRESHNESS (15% peso)                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Calcula score de frescura (0-10)                                    │   │
│  │ Fatores: dias no mercado, primeira vez visto                       │   │
│  │ ≤ 7 dias = score 8-10                                               │   │
│  │ 8-14 dias = score 6-7.9                                             │   │
│  │ 15-30 dias = score 4-5.9                                            │   │
│  │ > 30 dias = score 0-3.9                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  RED FLAGS DETECTOR                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Detecta red flags (overpricing, localização má, estado ruim, etc.) │   │
│  │ Se red flag maior = score 0                                          │   │
│  │ Se 2+ red flags menores = score reduzido                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  WEIGHTED SCORE CALCULATOR                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Combina 5 factores:                                                 │   │
│  │ - Discount (30%)                                                      │   │
│  │ - Location (25%)                                                     │   │
│  │ - Condition (15%)                                                    │   │
│  │ - Liquidity (15%)                                                    │   │
│  │ - Freshness (15%)                                                    │   │
│  │ Calcula score total (0-10)                                           │   │
│  │ Ajusta por red flags                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  RATIONALE GENERATOR                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Gera explicação do score (rationale)                                 │   │
│  │ Exemplo: "Discount 25% em Cedofeita com metro próximo,              │   │
│  │          imóvel renovado em 2022, excelente liquidez"               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  CLASSIFICAÇÃO                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Imperdível (8.0-10.0)                                               │   │
│  │ Bom (6.0-7.9)                                                         │   │
│  │ Aceitável (4.0-5.9)                                                   │   │
│  │ Não recomendado (0.0-3.9)                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. FACTOR 1: SCORE DISCOUNT

### 3.1 Definição de Discount

**Discount** é a diferença percentual entre o valor justo estimado e o preço pedido:

```
Discount (%) = (Valor Justo - Preço Pedido) / Valor Justo × 100
```

**Exemplos:**
- Valor justo = 200.000€, Preço pedido = 160.000€ → Discount = 20%
- Valor justo = 300.000€, Preço pedido = 210.000€ → Discount = 30%
- Valor justo = 200.000€, Preço pedido = 250.000€ → Overpricing = -25%

### 3.2 Implementação Score Discount

```python
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class ScoreDiscountCalculator:
    """Calcula score de discount."""
    
    def calculate(self, listing: Dict, valuation: Dict) -> float:
        """Calcula score de discount (0-10)."""
        discount = valuation.get('discount', 0)
        
        # Overpricing (negative discount)
        if discount < 0:
            logger.info(f"ScoreDiscount: Overpricing de {discount:.1f}% → score 0")
            return 0.0
        
        # Discount ≥ 20% (excelente)
        if discount >= 20:
            score = 8.0 + min(discount - 20, 30) / 30 * 2.0  # 8-10
            logger.info(f"ScoreDiscount: Discount de {discount:.1f}% → score {score:.1f}")
            return min(score, 10.0)
        
        # Discount 10-19% (bom)
        if discount >= 10:
            score = 6.0 + (discount - 10) / 10 * 1.9  # 6-7.9
            logger.info(f"ScoreDiscount: Discount de {discount:.1f}% → score {score:.1f}")
            return score
        
        # Discount 5-9% (aceitável)
        if discount >= 5:
            score = 4.0 + (discount - 5) / 5 * 1.9  # 4-5.9
            logger.info(f"ScoreDiscount: Discount de {discount:.1f}% → score {score:.1f}")
            return score
        
        # Discount < 5% (ruim)
        score = discount / 5 * 3.9  # 0-3.9
        logger.info(f"ScoreDiscount: Discount de {discount:.1f}% → score {score:.1f}")
        return score
```

---

## 4. FACTOR 2: SCORE LOCATION

### 4.1 Definição de Score Location

**Score Location** avalia a qualidade da localização baseado em:
- Freguesia (alta/média/baixa procura)
- Distância ao metro
- Proximidade a POIs (escolas, comércio)
- Segurança (taxa de criminalidade)

### 4.2 Pontuação de Freguesias

```python
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class ScoreLocationCalculator:
    """Calcula score de localização."""
    
    def __init__(self):
        self.freguesia_scores = {
            # Alta procura (8-10)
            'cedofeita': 9.0,
            'baixa': 9.0,
            'miragaia': 8.5,
            'sé': 8.5,
            'vitória': 8.0,
            
            # Média-alta procura (6-7.9)
            'paranhos': 7.5,
            'bonfim': 7.5,
            'santo ildefonso': 7.0,
            'massarelos': 7.0,
            'lordelo do ouro': 7.0,
            
            # Média procura (4-5.9)
            'aldoar': 5.5,
            'campanhã': 5.0,
            'ramalde': 5.0,
            'nevogilde': 5.0,
            'foz do douro': 5.0,
            
            # Média-baixa procura (0-3.9)
            'lordelo': 3.5,
            'campo grande': 3.0,
            'parada de tode': 3.0,
            'areosa': 2.5,
            'custóias': 2.0,
        }
    
    def calculate(self, listing: Dict) -> float:
        """Calcula score de localização (0-10)."""
        freguesia = listing.get('freguesia', '').lower()
        
        # Pontuação base da freguesia
        base_score = self.freguesia_scores.get(freguesia, 3.0)
        
        # Ajuste por distância ao metro
        dist_metro = listing.get('dist_metro_m', 9999)
        if dist_metro <= 500:
            metro_adjustment = 1.0
        elif dist_metro <= 1000:
            metro_adjustment = 0.5
        elif dist_metro <= 1500:
            metro_adjustment = 0.0
        else:
            metro_adjustment = -0.5
        
        # Ajuste por POIs
        dist_escola = listing.get('dist_escola_m', 9999)
        dist_comercio = listing.get('dist_comercio_m', 9999)
        
        if dist_escola <= 500 and dist_comercio <= 500:
            poi_adjustment = 0.5
        elif dist_escola <= 1000 and dist_comercio <= 1000:
            poi_adjustment = 0.0
        else:
            poi_adjustment = -0.5
        
        # Score final
        final_score = base_score + metro_adjustment + poi_adjustment
        final_score = max(0.0, min(final_score, 10.0))  # Clamp entre 0-10
        
        logger.info(
            f"ScoreLocation: Freguesia {freguesia} → base {base_score:.1f}, "
            f"metro {metro_adjustment:+.1f}, POIs {poi_adjustment:+.1f} → final {final_score:.1f}"
        )
        
        return final_score
```

---

## 5. FACTOR 3: SCORE CONDITION

### 5.1 Definição de Score Condition

**Score Condition** avalia o estado do imóvel baseado em:
- Estado de conservação
- Ano de construção
- Certificado energético

### 5.2 Implementação Score Condition

```python
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class ScoreConditionCalculator:
    """Calcula score de estado."""
    
    def __init__(self):
        self.estado_scores = {
            'novo': 10.0,
            'muito bom': 9.0,
            'bom': 7.5,
            'aceitável': 5.0,
            'ruim': 2.0,
            'mau': 1.0,
            'precisa de obras': 0.5,
        }
        
        self.cert_energetico_scores = {
            'a': 10.0,
            'b': 8.0,
            'c': 6.0,
            'd': 4.0,
            'e': 2.0,
            'f': 1.0,
            'g': 0.0,
        }
    
    def calculate(self, listing: Dict) -> float:
        """Calcula score de estado (0-10)."""
        estado = listing.get('estado', '').lower()
        ano_construcao = listing.get('ano_construcao', 0)
        cert_energetico = listing.get('cert_energetico', '').upper()
        
        # Pontuação do estado
        estado_score = self.estado_scores.get(estado, 3.0)
        
        # Ajuste por ano de construção
        if ano_construcao >= 2020:
            ano_adjustment = 1.0
        elif ano_construcao >= 2010:
            ano_adjustment = 0.5
        elif ano_construcao >= 2000:
            ano_adjustment = 0.0
        elif ano_construcao >= 1990:
            ano_adjustment = -0.5
        else:
            ano_adjustment = -1.0
        
        # Ajuste por certificado energético
        cert_score = self.cert_energetico_scores.get(cert_energetico, 0.0)
        cert_adjustment = (cert_score - 5.0) / 10.0  # Normalizar para -0.5 a +0.5
        
        # Score final
        final_score = estado_score + ano_adjustment + cert_adjustment
        final_score = max(0.0, min(final_score, 10.0))  # Clamp entre 0-10
        
        logger.info(
            f"ScoreCondition: Estado {estado} → {estado_score:.1f}, "
            f"ano {ano_construcao} → {ano_adjustment:+.1f}, "
            f"cert {cert_energetico} → {cert_adjustment:+.1f} → final {final_score:.1f}"
        )
        
        return final_score
```

---

## 6. FACTOR 4: SCORE LIQUIDITY

### 6.1 Definição de Score Liquidity

**Score Liquidity** avalia a facilidade de vender o imóvel baseado em:
- Tempo médio de venda na freguesia
- Volume de transações na freguesia
- Taxa de listings vendidos

### 6.2 Implementação Score Liquidity

```python
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class ScoreLiquidityCalculator:
    """Calcula score de liquidez."""
    
    def calculate(self, listing: Dict) -> float:
        """Calcula score de liquidez (0-10)."""
        # Dados de liquidez (simulados - em produção viriam do INE)
        tempo_medio_venda = listing.get('ine_tempo_medio_venda', 90)  # dias
        volume_transacoes = listing.get('ine_volume_transacoes', 10)  # listings/mês
        taxa_vendidos = listing.get('ine_taxa_vendidos', 0.7)  # 0-1
        
        # Pontuação por tempo médio de venda
        if tempo_medio_venda <= 60:
            tempo_score = 10.0
        elif tempo_medio_venda <= 90:
            tempo_score = 8.0
        elif tempo_medio_venda <= 120:
            tempo_score = 5.0
        else:
            tempo_score = 2.0
        
        # Pontuação por volume de transações
        if volume_transacoes >= 20:
            volume_score = 10.0
        elif volume_transacoes >= 10:
            volume_score = 7.5
        elif volume_transacoes >= 5:
            volume_score = 5.0
        else:
            volume_score = 2.0
        
        # Pontuação por taxa de vendidos
        taxa_score = taxa_vendidos * 10.0  # 0-10
        
        # Score final (média ponderada)
        final_score = (tempo_score * 0.4 + volume_score * 0.3 + taxa_score * 0.3)
        final_score = max(0.0, min(final_score, 10.0))  # Clamp entre 0-10
        
        logger.info(
            f"ScoreLiquidity: Tempo {tempo_medio_venda}d → {tempo_score:.1f}, "
            f"volume {volume_transacoes} → {volume_score:.1f}, "
            f"taxa {taxa_vendidos:.2f} → {taxa_score:.1f} → final {final_score:.1f}"
        )
        
        return final_score
```

---

## 7. FACTOR 5: SCORE FRESHNESS

### 7.1 Definição de Score Freshness

**Score Freshness** avalia o quão recente é o listing no mercado:
- Dias no mercado
- Primeira vez visto
- Não é relançamento (re-listing)

### 7.2 Implementação Score Freshness

```python
from typing import Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ScoreFreshnessCalculator:
    """Calcula score de frescura."""
    
    def calculate(self, listing: Dict) -> float:
        """Calcula score de frescura (0-10)."""
        # Calcular dias no mercado
        scrape_timestamp = listing.get('scrape_timestamp', '')
        
        if not scrape_timestamp:
            logger.warning("ScoreFreshness: Sem scrape_timestamp → score 5.0 (default)")
            return 5.0
        
        try:
            scrape_date = datetime.fromisoformat(scrape_timestamp)
            days_on_market = (datetime.now() - scrape_date).days
        except ValueError:
            logger.warning(f"ScoreFreshness: scrape_timestamp inválido → score 5.0 (default)")
            return 5.0
        
        # Pontuação por dias no mercado
        if days_on_market <= 7:
            score = 10.0
        elif days_on_market <= 14:
            score = 8.0
        elif days_on_market <= 30:
            score = 5.0
        elif days_on_market <= 60:
            score = 3.0
        else:
            score = 1.0
        
        logger.info(
            f"ScoreFreshness: Dias no mercado {days_on_market} → score {score:.1f}"
        )
        
        return score
```

---

## 8. RED FLAGS DETECTOR

### 8.1 Definição de Red Flags

**Red Flags** são sinais de aviso que excluem um imóvel da classificação "Imperdível":
- Overpricing (preço > 120% valor justo)
- Localização má (score ≤ 4/10)
- Estado ruim (score ≤ 4/10)
- Liquidez baixa (score ≤ 4/10)
- Antigo (> 90 dias no mercado)
- Dados incompletos

### 8.2 Implementação Red Flags Detector

```python
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class RedFlagsDetector:
    """Detecta red flags em listings."""
    
    def detect(self, listing: Dict, valuation: Dict, scores: Dict) -> List[Dict]:
        """Detecta red flags."""
        red_flags = []
        
        # Red Flag 1: Overpricing
        discount = valuation.get('discount', 0)
        if discount < -20:  # > 20% overpricing
            red_flags.append({
                'type': 'overpricing',
                'severity': 'major',
                'description': f'Overpricing de {abs(discount):.1f}% (preço > 120% valor justo)'
            })
            logger.warning(f"RedFlags: Overpricing detectado ({discount:.1f}%)")
        
        # Red Flag 2: Localização má
        location_score = scores.get('score_location', 0)
        if location_score <= 4.0:
            red_flags.append({
                'type': 'location',
                'severity': 'major' if location_score <= 3.0 else 'minor',
                'description': f'Localização má (score {location_score:.1f}/10)'
            })
            logger.warning(f"RedFlags: Localização má (score {location_score:.1f}/10)")
        
        # Red Flag 3: Estado ruim
        condition_score = scores.get('score_condition', 0)
        if condition_score <= 4.0:
            red_flags.append({
                'type': 'condition',
                'severity': 'major' if condition_score <= 3.0 else 'minor',
                'description': f'Estado ruim (score {condition_score:.1f}/10)'
            })
            logger.warning(f"RedFlags: Estado ruim (score {condition_score:.1f}/10)")
        
        # Red Flag 4: Liquidez baixa
        liquidity_score = scores.get('score_liquidity', 0)
        if liquidity_score <= 4.0:
            red_flags.append({
                'type': 'liquidity',
                'severity': 'major' if liquidity_score <= 3.0 else 'minor',
                'description': f'Liquidez baixa (score {liquidity_score:.1f}/10)'
            })
            logger.warning(f"RedFlags: Liquidez baixa (score {liquidity_score:.1f}/10)")
        
        # Red Flag 5: Antigo
        freshness_score = scores.get('score_freshness', 0)
        if freshness_score <= 3.0:  # > 60 dias
            red_flags.append({
                'type': 'freshness',
                'severity': 'major',
                'description': f'Antigo no mercado (score {freshness_score:.1f}/10)'
            })
            logger.warning(f"RedFlags: Antigo no mercado (score {freshness_score:.1f}/10)")
        
        # Red Flag 6: Dados incompletos
        required_fields = ['titulo', 'descricao', 'fotos_urls']
        missing_fields = [field for field in required_fields if not listing.get(field)]
        if len(missing_fields) >= 2:
            red_flags.append({
                'type': 'incomplete_data',
                'severity': 'major',
                'description': f'Dados incompletos: {", ".join(missing_fields)}'
            })
            logger.warning(f"RedFlags: Dados incompletos: {missing_fields}")
        
        return red_flags
```

---

## 9. WEIGHTED SCORE CALCULATOR

### 9.1 Definição de Weighted Score

**Weighted Score** combina os 5 factores usando pesos ponderados:
- Discount: 30%
- Location: 25%
- Condition: 15%
- Liquidity: 15%
- Freshness: 15%

### 9.2 Implementação Weighted Score Calculator

```python
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class WeightedScoreCalculator:
    """Calcula score total usando pesos ponderados."""
    
    def __init__(self):
        self.weights = {
            'discount': 0.30,
            'location': 0.25,
            'condition': 0.15,
            'liquidity': 0.15,
            'freshness': 0.15
        }
    
    def calculate(self, scores: Dict, red_flags: List[Dict]) -> Dict:
        """Calcula score total (0-10)."""
        # Calcular score ponderado
        score_total = (
            scores['score_discount'] * self.weights['discount'] +
            scores['score_location'] * self.weights['location'] +
            scores['score_condition'] * self.weights['condition'] +
            scores['score_liquidity'] * self.weights['liquidity'] +
            scores['score_freshness'] * self.weights['freshness']
        )
        
        # Ajustar por red flags
        major_red_flags = [rf for rf in red_flags if rf['severity'] == 'major']
        minor_red_flags = [rf for rf in red_flags if rf['severity'] == 'minor']
        
        if major_red_flags:
            # Se houver red flag maior, score = 0
            score_total = 0.0
            logger.warning(f"WeightedScore: Red flag maior detectada → score 0")
        elif len(minor_red_flags) >= 2:
            # Se houver 2+ red flags menores, reduzir score
            score_total = score_total * 0.5
            logger.warning(f"WeightedScore: {len(minor_red_flags)} red flags menores → score reduzido 50%")
        elif len(minor_red_flags) == 1:
            # Se houver 1 red flag menor, reduzir score 25%
            score_total = score_total * 0.75
            logger.warning(f"WeightedScore: 1 red flag menor → score reduzido 25%")
        
        # Clamp entre 0-10
        score_total = max(0.0, min(score_total, 10.0))
        
        logger.info(
            f"WeightedScore: Score total = {score_total:.1f} "
            f"(discount {scores['score_discount']:.1f}, "
            f"location {scores['score_location']:.1f}, "
            f"condition {scores['score_condition']:.1f}, "
            f"liquidity {scores['score_liquidity']:.1f}, "
            f"freshness {scores['score_freshness']:.1f})"
        )
        
        return {
            'score_total': score_total,
            'red_flags': red_flags
        }
```

---

## 10. RATIONALE GENERATOR

### 10.1 Definição de Rationale

**Rationale** é uma explicação em linguagem natural do score, explicando porquê o score é X.

### 10.2 Implementação Rationale Generator

```python
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class RationaleGenerator:
    """Gera explicação do score."""
    
    def generate(self, listing: Dict, valuation: Dict, scores: Dict, red_flags: List[Dict]) -> str:
        """Gera rationale."""
        discount = valuation.get('discount', 0)
        freguesia = listing.get('freguesia', '')
        estado = listing.get('estado', '')
        
        # Partes do rationale
        parts = []
        
        # Parte 1: Discount
        if discount >= 20:
            parts.append(f"Discount excelente de {discount:.1f}%")
        elif discount >= 10:
            parts.append(f"Discount bom de {discount:.1f}%")
        elif discount >= 5:
            parts.append(f"Discount aceitável de {discount:.1f}%")
        elif discount > 0:
            parts.append(f"Discount pequeno de {discount:.1f}%")
        elif discount < -10:
            parts.append(f"Overpricing de {abs(discount):.1f}%")
        
        # Parte 2: Localização
        if scores['score_location'] >= 8:
            parts.append(f"localização excelente em {freguesia}")
        elif scores['score_location'] >= 6:
            parts.append(f"localização boa em {freguesia}")
        elif scores['score_location'] >= 4:
            parts.append(f"localização aceitável em {freguesia}")
        else:
            parts.append(f"localização fraca em {freguesia}")
        
        # Parte 3: Estado
        if scores['score_condition'] >= 8:
            parts.append(f"imóvel {estado}")
        elif scores['score_condition'] >= 6:
            parts.append(f"imóvel em bom estado")
        elif scores['score_condition'] >= 4:
            parts.append(f"imóvel em estado aceitável")
        else:
            parts.append(f"imóvel em estado ruim")
        
        # Parte 4: Liquidez
        if scores['score_liquidity'] >= 8:
            parts.append("excelente liquidez")
        elif scores['score_liquidity'] >= 6:
            parts.append("boa liquidez")
        elif scores['score_liquidity'] >= 4:
            parts.append("liquidez aceitável")
        else:
            parts.append("liquidez baixa")
        
        # Parte 5: Frescura
        if scores['score_freshness'] >= 8:
            parts.append("recentemente publicado")
        elif scores['score_freshness'] >= 6:
            parts.append("publicado recentemente")
        elif scores['score_freshness'] >= 4:
            parts.append("há algum tempo no mercado")
        else:
            parts.append("antigo no mercado")
        
        # Parte 6: Red flags (se aplicável)
        if red_flags:
            red_flag_desc = ", ".join([rf['description'] for rf in red_flags[:2]])
            parts.append(f"ATENÇÃO: {red_flag_desc}")
        
        # Combinar partes
        rationale = ", ".join(parts) + "."
        
        logger.info(f"RationaleGenerator: {rationale}")
        
        return rationale
```

---

## 11. CLASSIFICAÇÃO

### 11.1 Definição de Classificação

**Classificação** agrupa listings em 4 categorias baseado no score total:
- Imperdível (8.0-10.0)
- Bom (6.0-7.9)
- Aceitável (4.0-5.9)
- Não recomendado (0.0-3.9)

### 11.2 Implementação Classificação

```python
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class ClassificationEngine:
    """Classifica listings baseado no score."""
    
    def classify(self, score_total: float) -> str:
        """Classifica listing."""
        if score_total >= 8.0:
            classification = "Imperdível"
        elif score_total >= 6.0:
            classification = "Bom"
        elif score_total >= 4.0:
            classification = "Aceitável"
        else:
            classification = "Não recomendado"
        
        logger.info(f"Classification: Score {score_total:.1f} → {classification}")
        
        return classification
```

---

## 12. PERFORMANCE SCORING

### 12.1 Métricas de Performance

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              MÉTRICAS DE PERFORMANCE SCORING                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TEMPO DE SCORING:                                                         │
│  - Score Discount: < 0.001 segundos por listing                           │
│  - Score Location: < 0.001 segundos por listing                             │
│  - Score Condition: < 0.001 segundos por listing                            │
│  - Score Liquidity: < 0.001 segundos por listing                            │
│  - Score Freshness: < 0.001 segundos por listing                            │
│  - Red Flags Detector: < 0.001 segundos por listing                        │
│  - Weighted Score Calculator: < 0.001 segundos por listing                  │
│  - Rationale Generator: < 0.005 segundos por listing                       │
│  - Total: < 0.01 segundos por listing                                     │
│                                                                             │
│  THROUGHPUT:                                                                │
│  - 1000 listings: < 10 segundos                                           │
│  - 5000 listings: < 50 segundos                                           │
│                                                                             │
│  DISTRIBUIÇÃO DE SCORES:                                                    │
│  - Imperdível (8-10): 2-5% dos listings                                   │
│  - Bom (6-7.9): 10-15% dos listings                                      │
│  - Aceitável (4-5.9): 20-30% dos listings                                 │
│  - Não recomendado (0-3.9): 50-68% dos listings                            │
│                                                                             │
│  RED FLAGS:                                                                │
│  - Major red flags: 5-10% dos listings                                    │
│  - Minor red flags: 15-20% dos listings                                   │
│  - Sem red flags: 70-80% dos listings                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 13. THRESHOLDS DE SCORING

### 13.1 Thresholds Detalhados

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              THRESHOLDS DE SCORING DETALHADOS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  IMPERDÍVEL (8.0-10.0):                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Discount ≥ 20%                                                         │   │
│  │ Location ≥ 7/10                                                        │   │
│  │ Condition ≥ 6/10                                                       │   │
│  │ Liquidity ≥ 7/10                                                       │   │
│  │ Freshness ≤ 7 dias                                                     │   │
│  │ SEM red flags                                                          │   │
│  │ Top 3-5 listings/dia notificados                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  BOM (6.0-7.9):                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Discount ≥ 10%                                                         │   │
│  │ Location ≥ 6/10                                                        │   │
│  │ Condition ≥ 5/10                                                       │   │
│  │ Liquidity ≥ 6/10                                                       │   │
│  │ Freshness ≤ 14 dias                                                    │   │
│  │ MÁXIMO 1 red flag menor                                                │   │
│  │ 10-15% dos listings                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ACEITÁVEL (4.0-5.9):                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Discount ≥ 5%                                                          │   │
│  │ Location ≥ 5/10                                                        │   │
│  │ Condition ≥ 4/10                                                       │   │
│  │ Liquidity ≥ 5/10                                                       │   │
│  │ Freshness ≤ 30 dias                                                    │   │
│  │ MÁXIMO 2 red flags menores                                              │   │
│  │ 20-30% dos listings                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  NÃO RECOMENDADO (0.0-3.9):                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Discount < 5% ou overpricing                                          │   │
│  │ Location < 5/10                                                        │   │
│  │ Condition < 4/10                                                        │   │
│  │ Liquidity < 5/10                                                       │   │
│  │ Freshness > 30 dias                                                    │   │
│  │ QUALQUER red flag maior                                               │   │
│  │ 50-68% dos listings                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 14. A/B TESTING DE SCORING

### 14.1 Estratégia de A/B Testing

```python
from typing import Dict, List
import logging
import random

logger = logging.getLogger(__name__)

class ScoringABTester:
    """A/B testing de thresholds de scoring."""
    
    def __init__(self):
        self.variants = {
            'control': {
                'discount_threshold': 20,
                'location_threshold': 7,
                'condition_threshold': 6,
                'liquidity_threshold': 7,
                'freshness_threshold': 7
            },
            'variant_a': {
                'discount_threshold': 15,  # Mais relaxado
                'location_threshold': 6,
                'condition_threshold': 5,
                'liquidity_threshold': 6,
                'freshness_threshold': 14
            },
            'variant_b': {
                'discount_threshold': 25,  # Mais estrito
                'location_threshold': 8,
                'condition_threshold': 7,
                'liquidity_threshold': 8,
                'freshness_threshold': 5
            }
        }
    
    def assign_variant(self, listing_id: str) -> str:
        """Atribui variante a um listing."""
        # Hash do listing_id para consistência
        hash_value = hash(listing_id) % 100
        
        if hash_value < 33:
            return 'control'
        elif hash_value < 66:
            return 'variant_a'
        else:
            return 'variant_b'
    
    def calculate_score_with_variant(self, scores: Dict, variant: str) -> Dict:
        """Calcula score com thresholds da variante."""
        thresholds = self.variants[variant]
        
        # Aplicar thresholds específicos da variante
        # ... implementação específica
        
        return scores
```

---

## 15. GLOSSÁRIO DE SCORING

```
┌─────────────────────────────────────────────────────────────────────────────┐
│            GLOSSÁRIO DE SCORING                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SCORING ENGINE: Motor que calcula score de 0-10 para cada listing         │
│                                                                             │
│  SCORE: Pontuação de 0-10 indicando qualidade como oportunidade            │
│                                                                             │
│  DISCOUNT: Diferença percentual entre valor justo e preço pedido           │
│                                                                             │
│  LOCATION: Qualidade da localização (freguesia, metro, POIs)           │
│                                                                             │
│  CONDITION: Estado do imóvel (conservação, ano, cert. energético)        │
│                                                                             │
│  LIQUIDITY: Facilidade de vender (tempo médio, volume, taxa vendidos)    │
│                                                                             │
│  FRESHNESS: Quão recente é o listing no mercado                           │
│                                                                             │
│  RED FLAG: Sinal de aviso que exclui listing de "Imperdível"              │
│                                                                             │
│  WEIGHTED SCORE: Score combinado usando pesos ponderados                  │
│                                                                             │
│  RATIONALE: Explicação em linguagem natural do score                       │
│                                                                             │
│  CLASSIFICAÇÃO: Categoria do listing (Imperdível, Bom, Aceitável, etc.) │
│                                                                             │
│  IMPERDÍVEL: Score 8-10 (melhores oportunidades)                           │
│                                                                             │
│  BOM: Score 6-7.9 (boas oportunidades)                                    │
│                                                                             │
│  ACEITÁVEL: Score 4-5.9 (oportunidades aceitáveis)                        │
│                                                                             │
│  NÃO RECOMENDADO: Score 0-3.9 (não recomendado)                           │
│                                                                             │
│  THRESHOLD: Limiar para classificação                                      │
│                                                                             │
│  A/B TESTING: Teste de diferentes thresholds para optimizar scoring      │
│                                                                             │
│  OVERPRICING: Preço acima do valor justo                                   │
│                                                                             │
│  MAJOR RED FLAG: Red flag que exclui de "Imperdível"                       │
│                                                                             │
│  MINOR RED FLAG: Red flag que reduz score mas não exclui                  │
│                                                                             │
│  POI: Point of Interest (ponto de interesse)                              │
│                                                                             │
│  FREGUESIA: Subdivisão administrativa de Portugal                         │
│                                                                             │
│  CERTIFICADO ENERGÉTICO: Classificação de eficiência energética          │
│                                                                             │
│  VOLUME DE TRANSAÇÕES: Número de listings vendidos por mês               │
│                                                                             │
│  TAXA VENDIDOS: Percentagem de listings vendidos vs total                 │
│                                                                             │
│  TEMPO MÉDIO VENDA: Tempo médio para vender um imóvel                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*Fim do Documento 07 — Scoring Engine*
