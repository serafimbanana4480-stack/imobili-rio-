# VALUATION ENGINE — REAL ESTATE OPPORTUNITY ENGINE
## Motor de Avaliação: 4 Modelos + Meta-Ensemble e Explainability

> **Este documento:** Especificação completa do motor de avaliação  
> **Objectivo:** Fornecer especificação detalhada de valuation para IA implementar  
> **Linhas:** 1500+ linhas de documentação detalhada  
> **Versão:** 5.0 (Actualizado com Volume 13)

---

## ÍNDICE

1. [Introdução ao Valuation Engine](#1-introducao-ao-valuation-engine)
2. [Arquitectura de Valuation](#2-arquitetura-de-valuation)
3. [Camada 1: Hedonic Model](#3-camada-1-hedonic-model)
4. [Camada 2: Comps Engine](#4-camada-2-comps-engine)
5. [Camada 3: INE Macro Data](#5-camada-3-ine-macro-data)
6. [Camada 4: XGBoost Model](#6-camada-4-xgboost-model)
7. [Weighted Ensemble](#7-weighted-ensemble)
8. [Explainability (SHAP)](#8-explainability-shap)
9. [Confidence Intervals](#9-confidence-intervals)
10. [Performance Valuation](#10-performance-valuation)
11. [Training e Retraining](#11-training-e-retraining)
12. [Model Evaluation](#12-model-evaluation)
13. [Deployment do Model](#13-deployment-do-model)
14. [Monitoring Valuation](#14-monitoring-valuation)
15. [Glossário de Valuation](#15-glossário-de-valuation)

---

## 1. INTRODUÇÃO AO VALUATION ENGINE

### 1.1 O Que é Valuation Engine?

**Valuation Engine** é o motor que calcula o **valor justo estimado** para cada imóvel. O valor justo é o preço de mercado esperado, baseado em características do imóvel, dados históricos e contexto macro.

**Objectivo:** Fornecer uma estimativa precisa e confiável do valor de mercado de cada listing, para calcular o discount (diferença entre preço pedido e valor justo).

### 1.2 Porquê Valuation Engine?

**Problema sem Valuation Engine:**
- Impossível saber se um listing está subvalorizado ou sobrevalorizado
- Decisões baseadas em intuição ou comparações manuais
- Sem contexto de mercado (preços médios da freguesia, tendências)

**Solução com Valuation Engine:**
- Valor justo estimado para cada listing
- Discount calculado automaticamente (preço pedido vs valor justo)
- Contexto de mercado integrado (INE, POIs)
- Explainability (saber porquê valor é X)

---

## 2. ARQUITECTURA DE VALUATION

### 2.1 Arquitectura de 4 Modelos com Meta-Ensemble

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              ARQUITECTURA DE VALUATION (4 MODELOS + META-ENSEMBLE)    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MODELO 1: XGBOOST (Gradient Boosting)                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Gradient boosting com XGBoost                                        │   │
│  │ Features: área, quartos, freguesia, POIs, estado, etc.            │   │
│  │ Captura não-linearidades e interações                                │   │
│  │ SHAP para explainability                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  MODELO 2: HEDONIC MODEL (Regressão Linear)                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Regressão linear (statsmodels OLS)                                  │   │
│  │ Features: área, quartos, freguesia, estado, ano construção, etc.  │   │
│  │ Interpretação clara (coeficientes)                                  │   │
│  │ Valor hedónico: preço baseado em características                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  MODELO 3: NEURAL NETWORK (Deep Learning)                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Rede neuronal (TensorFlow/Keras ou PyTorch)                         │   │
│  │ Captura padrões complexos não-lineares                              │   │
│  │ Arquitectura: 3-4 camadas ocultas                                   │   │
│  │ Requer muitos dados para treinar                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  MODELO 4: CATBOOST (Gradient Boosting)                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Gradient boosting com CatBoost (otimizado para features categóricas)│   │
│  │ Features: área, quartos, freguesia (categórica), etc.              │   │
│  │ Tratamento automático de features categóricas                       │   │
│  │ Alta performance em dados tabulares                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  MODELO 5: RANDOM FOREST (Ensemble de Árvores)                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Random Forest (scikit-learn)                                        │   │
│  │ Ensemble de árvores de decisão                                      │   │
│  │ Robusto a overfitting                                               │   │
│  │ Feature importance automática                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  MODELO 6: LINEAR MODEL (Regressão Linear Simples)                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Regressão linear simples (scikit-learn)                             │   │
│  │ Baseline simples                                                    │   │
│  │ Interpretação direta                                                │   │
│  │ Rápido de treinar e inferir                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  MODELO 7: COMPS ENGINE (Comparables)                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Encontra listings similares na mesma freguesia                      │   │
│  │ Filtros: área ±20%, quartos ±1, estado similar                       │   │
│  │ Calcula preço médio de comparáveis                                     │   │
│  │ Ajusta por características (quartos, estado)                           │   │
│  │ Valor comps: preço baseado em listings similares                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  MODELO 8: INE MACRO DATA (Contexto Macro)                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Preço médio por m² da freguesia (INE)                                │   │
│  │ Tendências de preços (mensal, trimestral)                           │   │
│  │ Volume de transações                                                 │   │
│  │ Valor INE: preço baseado em contexto macro                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  META-LEARNING ENSEMBLE                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Combina 4 modelos com pesos dinâmicos:                             │  │ │
│  │ - Meta-Learning: optimização de pesos baseada em meta-features    │   │
│  │ - Target R² > 0.85                                                  │   │
│  │ - Pesos adaptam-se automaticamente por região/tipo de imóvel       │   │
│  │ Valor justo estimado = weighted average dinâmico                    │   │
│  │ Intervalo de confiança (CI lower, CI upper)                         │   │
│  │ Confiança (%) = 70-85%                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. CAMADA 1: HEDONIC MODEL

### 3.1 O Que é Hedonic Model?

**Hedonic Model** é um modelo de regressão linear que estima o preço de um imóvel baseado nas suas características hedónicas (características que contribuem para o valor).

**Equação:**
```
Preço = β₀ + β₁×Área + β₂×Quartos + β₃×Freguesia_Cedofeita + β₄×Freguesia_Paranhos + ... + ε
```

Onde:
- β₀: Intercepto (preço base)
- β₁, β₂, β₃, ...: Coeficientes (impacto de cada característica no preço)
- ε: Erro (variabilidade não explicada)

### 3.2 Features do Hedonic Model

```python
from dataclasses import dataclass
from typing import List

@dataclass
class HedonicFeatures:
    """Features para Hedonic Model."""
    
    # Características principais
    area_util_m2: float
    quartos: int
    casas_banho: int
    
    # Freguesia (one-hot encoding)
    freguesia_cedofeita: int
    freguesia_paranhos: int
    freguesia_bonfim: int
    freguesia_baixa: int
    # ... mais freguesias
    
    # Estado
    estado_novo: int
    estado_muito_bom: int
    estado_bom: int
    estado_aceitavel: int
    estado_ruim: int
    
    # Ano de construção
    ano_construcao: int
    
    # Certificado energético
    cert_energetico_a: int
    cert_energetico_b: int
    cert_energetico_c: int
    cert_energetico_d: int
    cert_energetico_e: int
    cert_energetico_f: int
    cert_energetico_g: int
    
    # POIs
    dist_metro_m: float
    dist_escola_m: float
    dist_comercio_m: float
    
    def to_list(self) -> List[float]:
        """Converte features para lista."""
        return [
            self.area_util_m2,
            self.quartos,
            self.casas_banho,
            self.freguesia_cedofeita,
            self.freguesia_paranhos,
            self.freguesia_bonfim,
            self.freguesia_baixa,
            self.estado_novo,
            self.estado_muito_bom,
            self.estado_bom,
            self.estado_aceitavel,
            self.estado_ruim,
            self.ano_construcao,
            self.cert_energetico_a,
            self.cert_energetico_b,
            self.cert_energetico_c,
            self.cert_energetico_d,
            self.cert_energetico_e,
            self.cert_energetico_f,
            self.cert_energetico_g,
            self.dist_metro_m,
            self.dist_escola_m,
            self.dist_comercio_m,
        ]
```

### 3.3 Implementação Hedonic Model

```python
import statsmodels.api as sm
import numpy as np
import pandas as pd
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class HedonicModel:
    """Hedonic Model usando statsmodels OLS."""
    
    def __init__(self):
        self.model = None
        self.feature_names = None
        self.is_trained = False
    
    def train(self, listings: List[Dict]):
        """Treina o modelo com dados históricos."""
        logger.info("HedonicModel: Treinando modelo")
        
        # Converter para DataFrame
        df = pd.DataFrame(listings)
        
        # Extrair features
        X = self._extract_features(df)
        y = df['preco_pedido'].values
        
        # Treinar modelo OLS
        X = sm.add_constant(X)  # Adicionar intercepto
        self.model = sm.OLS(y, X).fit()
        
        self.feature_names = X.columns.tolist()
        self.is_trained = True
        
        logger.info(f"HedonicModel: Modelo treinado (R² = {self.model.rsquared:.3f})")
    
    def predict(self, listing: Dict) -> float:
        """Prediz preço para um listing."""
        if not self.is_trained:
            raise ValueError("Modelo não treinado")
        
        # Extrair features
        features = self._extract_features_dict(listing)
        
        # Prever
        X = np.array([features])
        X = sm.add_constant(X)
        prediction = self.model.predict(X)
        
        return float(prediction[0])
    
    def _extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extrai features do DataFrame."""
        features = []
        
        for _, row in df.iterrows():
            feature_list = []
            
            # Características principais
            feature_list.append(row.get('area_util_m2', 0))
            feature_list.append(row.get('quartos', 0))
            feature_list.append(row.get('casas_banho', 0))
            
            # Freguesia (one-hot encoding)
            freguesias = ['cedofeita', 'paranhos', 'bonfim', 'baixa', 'vitória', 'santo_ildefonso']
            for freg in freguesias:
                feature_list.append(1 if row.get('freguesia', '').lower() == freg else 0)
            
            # Estado (one-hot encoding)
            estados = ['novo', 'muito bom', 'bom', 'aceitável', 'ruim']
            estado = row.get('estado', '').lower()
            for est in estados:
                feature_list.append(1 if estado == est else 0)
            
            # Ano de construção
            feature_list.append(row.get('ano_construcao', 0))
            
            # Certificado energético (one-hot encoding)
            cert = row.get('cert_energetico', '').upper()
            cert_letras = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
            for cert_letra in cert_letras:
                feature_list.append(1 if cert == cert_letra else 0)
            
            # POIs
            feature_list.append(row.get('dist_metro_m', 0))
            feature_list.append(row.get('dist_escola_m', 0))
            feature_list.append(row.get('dist_comercio_m', 0))
            
            features.append(feature_list)
        
        return pd.DataFrame(features)
    
    def _extract_features_dict(self, listing: Dict) -> List[float]:
        """Extrai features de um listing."""
        feature_list = []
        
        # Características principais
        feature_list.append(listing.get('area_util_m2', 0))
        feature_list.append(listing.get('quartos', 0))
        feature_list.append(listing.get('casas_banho', 0))
        
        # Freguesia (one-hot encoding)
        freguesias = ['cedofeita', 'paranhos', 'bonfim', 'baixa', 'vitória', 'santo_ildefonso']
        freguesia = listing.get('freguesia', '').lower()
        for freg in freguesias:
            feature_list.append(1 if freguesia == freg else 0)
        
        # Estado (one-hot encoding)
        estados = ['novo', 'muito bom', 'bom', 'aceitável', 'ruim']
        estado = listing.get('estado', '').lower()
        for est in estados:
            feature_list.append(1 if estado == est else 0)
        
        # Ano de construção
        feature_list.append(listing.get('ano_construcao', 0))
        
        # Certificado energético (one-hot encoding)
        cert = listing.get('cert_energetico', '').upper()
        cert_letras = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
        for cert_letra in cert_letras:
            feature_list.append(1 if cert == cert_letra else 0)
        
        # POIs
        feature_list.append(listing.get('dist_metro_m', 0))
        feature_list.append(listing.get('dist_escola_m', 0))
        feature_list.append(listing.get('dist_comercio_m', 0))
        
        return feature_list
    
    def get_coefficients(self) -> Dict[str, float]:
        """Retorna coeficientes do modelo."""
        if not self.is_trained:
            return {}
        
        return dict(zip(self.feature_names, self.model.params))
```

---

## 4. CAMADA 2: COMPS ENGINE

### 4.1 O Que é Comps Engine?

**Comps Engine** (Comparables Engine) encontra listings similares na mesma freguesia e calcula o preço médio desses comparáveis.

**Estratégia:**
1. Encontrar listings na mesma freguesia
2. Filtrar por área (±20%)
3. Filtrar por quartos (±1)
4. Filtrar por estado similar
5. Calcular preço médio dos comparáveis
6. Ajustar por diferenças de características

### 4.2 Implementação Comps Engine

```python
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class CompsEngine:
    """Engine para encontrar comparáveis."""
    
    def __init__(self, database_repository):
        self.database_repository = database_repository
    
    async def find_comparables_value(self, listing: Dict) -> float:
        """Encontra valor baseado em comparáveis."""
        logger.info(f"CompsEngine: Encontrando comparáveis para listing {listing.get('id', '')}")
        
        # Encontrar comparáveis
        comparables = await self._find_comparables(listing)
        
        if not comparables:
            logger.warning("CompsEngine: Nenhum comparável encontrado")
            return 0.0
        
        # Calcular preço médio dos comparáveis
        mean_price = self._calculate_mean_price(comparables)
        
        # Ajustar por diferenças de características
        adjusted_price = self._adjust_for_differences(listing, comparables, mean_price)
        
        logger.info(f"CompsEngine: Valor comps = {adjusted_price:.2f} (baseado em {len(comparables)} comparáveis)")
        
        return adjusted_price
    
    async def _find_comparables(self, listing: Dict) -> List[Dict]:
        """Encontra listings similares."""
        freguesia = listing.get('freguesia', '')
        area = listing.get('area_util_m2', 0)
        quartos = listing.get('quartos', 0)
        
        # Query database
        comparables = await self.database_repository.find_comparables(
            freguesia=freguesia,
            area_min=area * 0.8,  # ±20%
            area_max=area * 1.2,
            quartos_min=quartos - 1,
            quartos_max=quartos + 1,
            exclude_id=listing.get('id', '')
        )
        
        return comparables
    
    def _calculate_mean_price(self, comparables: List[Dict]) -> float:
        """Calcula preço médio dos comparáveis."""
        prices = [comp['preco_pedido'] for comp in comparables]
        return sum(prices) / len(prices)
    
    def _adjust_for_differences(self, listing: Dict, comparables: List[Dict], base_price: float) -> float:
        """Ajusta preço por diferenças de características."""
        # Implementação simplificada
        # Em produção, usar regressão para ajustar por diferenças
        
        listing_area = listing.get('area_util_m2', 0)
        listing_quartos = listing.get('quartos', 0)
        
        avg_area = sum(comp.get('area_util_m2', 0) for comp in comparables) / len(comparables)
        avg_quartos = sum(comp.get('quartos', 0) for comp in comparables) / len(comparables)
        
        # Ajuste por área (€/m²)
        area_diff = listing_area - avg_area
        price_per_m2 = base_price / avg_area
        area_adjustment = area_diff * price_per_m2
        
        # Ajuste por quartos (€/quarto)
        quartos_diff = listing_quartos - avg_quartos
        price_per_quarto = base_price / avg_quartos / 10  # Aproximação
        quartos_adjustment = quartos_diff * price_per_quarto
        
        adjusted_price = base_price + area_adjustment + quartos_adjustment
        
        return max(adjusted_price, 0.0)  # Não pode ser negativo
```

---

## 5. CAMADA 3: INE MACRO DATA

### 5.1 O Que é INE Macro Data?

**INE Macro Data** adiciona contexto macro ao valuation, usando dados do INE (Instituto Nacional de Estatística).

**Dados INE:**
- Preço médio por m² da freguesia
- Tendências de preços (mensal, trimestral)
- Volume de transações

### 5.2 Implementação INE Macro Data

```python
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class INEMacroData:
    """Dados macro do INE."""
    
    def __init__(self, ine_client):
        self.ine_client = ine_client
    
    async def add_ine_context(self, listing: Dict) -> Dict:
        """Adiciona contexto INE ao listing."""
        freguesia = listing.get('freguesia', '')
        
        # Obter dados INE da freguesia
        ine_data = await self.ine_client.get_freguesia_data(freguesia)
        
        # Calcular valor baseado em INE
        area = listing.get('area_util_m2', 0)
        ine_price_m2 = ine_data.get('preco_medio_m2', 0)
        ine_value = area * ine_price_m2
        
        logger.info(f"INEMacroData: Valor INE = {ine_value:.2f} (baseado em {ine_price_m2:.2f} €/m²)")
        
        listing['ine_value'] = ine_value
        listing['ine_preco_medio_m2'] = ine_price_m2
        listing['ine_tendencia_mensal'] = ine_data.get('tendencia_mensal', 0)
        
        return listing
```

---

## 6. CAMADA 4: XGBOOST MODEL

### 6.1 O Que é XGBoost Model?

**XGBoost Model** é um modelo de gradient boosting que captura não-linearidades nos dados. É opcional para MVP, mas recomendado para produção.

**Vantagens:**
- Captura não-linearidades (interações entre features)
- Alta precisão (se bem treinado)
- SHAP para explainability

**Desvantagens:**
- Requer muitos dados para treinar (min 10.000 listings)
- Mais complexo de treinar e manter
- "Black box" (sem SHAP)

### 6.2 Implementação XGBoost Model

```python
import xgboost as xgb
import numpy as np
import pandas as pd
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class XGBoostModel:
    """XGBoost Model para valuation."""
    
    def __init__(self):
        self.model = None
        self.feature_names = None
        self.is_trained = False
    
    def train(self, listings: List[Dict]):
        """Treina o modelo XGBoost."""
        logger.info("XGBoostModel: Treinando modelo")
        
        # Converter para DataFrame
        df = pd.DataFrame(listings)
        
        # Extrair features
        X = self._extract_features(df)
        y = df['preco_pedido'].values
        
        # Treinar modelo
        self.model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42
        )
        self.model.fit(X, y)
        
        self.feature_names = X.columns.tolist()
        self.is_trained = True
        
        logger.info("XGBoostModel: Modelo treinado")
    
    def predict(self, listing: Dict) -> float:
        """Prediz preço para um listing."""
        if not self.is_trained:
            raise ValueError("Modelo não treinado")
        
        # Extrair features
        features = self._extract_features_dict(listing)
        
        # Prever
        X = np.array([features])
        prediction = self.model.predict(X)
        
        return float(prediction[0])
    
    def _extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extrai features do DataFrame."""
        # Similar ao Hedonic Model
        return df  # Simplificado para exemplo
    
    def _extract_features_dict(self, listing: Dict) -> List[float]:
        """Extrai features de um listing."""
        # Similar ao Hedonic Model
        return []  # Simplificado para exemplo
```

---

## 7. WEIGHTED ENSEMBLE

### 7.1 O Que é Meta-Learning Ensemble?

**Meta-Learning Ensemble** combina os 4 modelos de valuation usando pesos dinâmicos optimizados por meta-learning.

**Modelos:**
- XGBoost (Gradient Boosting)
- Hedonic Model (Regressão Linear)
- Neural Network (Deep Learning)
- CatBoost (Gradient Boosting com features categóricas)
- Random Forest (Ensemble de Árvores)
- Linear Model (Regressão Linear Simples)
- Comps Engine (Comparables)
- INE Macro Data (Contexto Macro)

**Meta-Learning:**
- Pesos dinâmicos baseados em meta-features (região, tipo de imóvel, disponibilidade de dados)
- Optimização automática de pesos para maximizar R²
- Target R² > 0.85

### 7.2 Implementação Weighted Ensemble

```python
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class WeightedEnsemble:
    """Meta-Learning Ensemble dos 4 modelos de valuation."""
    
    def __init__(
        self,
        xgboost_model=None,
        hedonic_model=None,
        neural_network_model=None,
        catboost_model=None,
        random_forest_model=None,
        linear_model=None,
        comps_engine=None,
        ine_client=None
    ):
        self.xgboost_model = xgboost_model
        self.hedonic_model = hedonic_model
        self.neural_network_model = neural_network_model
        self.catboost_model = catboost_model
        self.random_forest_model = random_forest_model
        self.linear_model = linear_model
        self.comps_engine = comps_engine
        self.ine_client = ine_client
        
        # Pesos dinâmicos (serão calculados por meta-learning)
        self.weights = {
            'xgboost': 0.15,
            'hedonic': 0.15,
            'neural_network': 0.15,
            'catboost': 0.15,
            'random_forest': 0.10,
            'linear': 0.10,
            'comps': 0.10,
            'ine': 0.10
        }
    
    async def combine(self, listing: Dict) -> Dict:
        """Combina os 4 modelos usando pesos dinâmicos."""
        logger.info(f"WeightedEnsemble: Calculando valor justo para listing {listing.get('id', '')}")
        
        values = {}
        
        # Modelo 1: XGBoost
        if self.xgboost_model and self.xgboost_model.is_trained:
            try:
                xgboost_value = self.xgboost_model.predict(listing)
                values['xgboost'] = xgboost_value
                logger.info(f"MetaLearningEnsemble: XGBoost = {xgboost_value:.2f}")
            except Exception as e:
                logger.error(f"MetaLearningEnsemble: Erro em XGBoost: {e}")
                values['xgboost'] = 0.0
        else:
            values['xgboost'] = 0.0
        
        # Modelo 2: Hedonic
        if self.hedonic_model:
            try:
                hedonic_value = self.hedonic_model.predict(listing)
                values['hedonic'] = hedonic_value
                logger.info(f"MetaLearningEnsemble: Hedonic = {hedonic_value:.2f}")
            except Exception as e:
                logger.error(f"MetaLearningEnsemble: Erro em Hedonic: {e}")
                values['hedonic'] = 0.0
        else:
            values['hedonic'] = 0.0
        
        # Modelo 3: Neural Network
        if self.neural_network_model and self.neural_network_model.is_trained:
            try:
                nn_value = self.neural_network_model.predict(listing)
                values['neural_network'] = nn_value
                logger.info(f"MetaLearningEnsemble: Neural Network = {nn_value:.2f}")
            except Exception as e:
                logger.error(f"MetaLearningEnsemble: Erro em Neural Network: {e}")
                values['neural_network'] = 0.0
        else:
            values['neural_network'] = 0.0
        
        # Modelo 4: CatBoost
        if self.catboost_model and self.catboost_model.is_trained:
            try:
                catboost_value = self.catboost_model.predict(listing)
                values['catboost'] = catboost_value
                logger.info(f"MetaLearningEnsemble: CatBoost = {catboost_value:.2f}")
            except Exception as e:
                logger.error(f"MetaLearningEnsemble: Erro em CatBoost: {e}")
                values['catboost'] = 0.0
        else:
            values['catboost'] = 0.0
        
        # Modelo 5: Random Forest
        if self.random_forest_model and self.random_forest_model.is_trained:
            try:
                rf_value = self.random_forest_model.predict(listing)
                values['random_forest'] = rf_value
                logger.info(f"MetaLearningEnsemble: Random Forest = {rf_value:.2f}")
            except Exception as e:
                logger.error(f"MetaLearningEnsemble: Erro em Random Forest: {e}")
                values['random_forest'] = 0.0
        else:
            values['random_forest'] = 0.0
        
        # Modelo 6: Linear Model
        if self.linear_model and self.linear_model.is_trained:
            try:
                linear_value = self.linear_model.predict(listing)
                values['linear'] = linear_value
                logger.info(f"MetaLearningEnsemble: Linear Model = {linear_value:.2f}")
            except Exception as e:
                logger.error(f"MetaLearningEnsemble: Erro em Linear Model: {e}")
                values['linear'] = 0.0
        else:
            values['linear'] = 0.0
        
        # Modelo 7: Comps
        if self.comps_engine:
            try:
                comps_value = await self.comps_engine.find_comparables_value(listing)
                values['comps'] = comps_value
                logger.info(f"MetaLearningEnsemble: Comps = {comps_value:.2f}")
            except Exception as e:
                logger.error(f"MetaLearningEnsemble: Erro em Comps: {e}")
                values['comps'] = 0.0
        else:
            values['comps'] = 0.0
        
        # Modelo 8: INE
        if self.ine_client:
            try:
                ine_listing = await self.ine_client.add_ine_context(listing)
                ine_value = ine_listing.get('ine_value', 0)
                values['ine'] = ine_value
                logger.info(f"MetaLearningEnsemble: INE = {ine_value:.2f}")
            except Exception as e:
                logger.error(f"MetaLearningEnsemble: Erro em INE: {e}")
                values['ine'] = 0.0
        else:
            values['ine'] = 0.0
        
        # Calcular valor final (weighted average com pesos dinâmicos)
        final_value = (
            values['xgboost'] * self.weights['xgboost'] +
            values['hedonic'] * self.weights['hedonic'] +
            values['neural_network'] * self.weights['neural_network'] +
            values['catboost'] * self.weights['catboost'] +
            values['random_forest'] * self.weights['random_forest'] +
            values['linear'] * self.weights['linear'] +
            values['comps'] * self.weights['comps'] +
            values['ine'] * self.weights['ine']
        )
        
        # Calcular confiança
        confidence = self._calculate_confidence(values)
        
        # Calcular intervalo de confiança
        ci_lower = final_value * 0.9  # ±10% (simplificado)
        ci_upper = final_value * 1.1  # ±10% (simplificado)
        
        logger.info(f"WeightedEnsemble: Valor justo = {final_value:.2f} (confiança: {confidence:.1f}%)")
        
        return {
            'valor_justo': final_value,
            'xgboost_value': values['xgboost'],
            'hedonic_value': values['hedonic'],
            'neural_network_value': values['neural_network'],
            'catboost_value': values['catboost'],
            'random_forest_value': values['random_forest'],
            'linear_value': values['linear'],
            'comps_value': values['comps'],
            'ine_value': values['ine'],
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'confianca': confidence,
            'discount': (listing['preco_pedido'] - final_value) / final_value * 100 if final_value > 0 else 0
        }
    
    def _calculate_confidence(self, values: Dict) -> float:
        """Calcula confiança baseado na variância dos valores."""
        # Simplificado: confiança baseada em quantas camadas têm valores válidos
        valid_count = sum(1 for v in values.values() if v > 0)
        
        if valid_count == 0:
            return 0.0
        
        # Mais camadas = mais confiança
        confidence = (valid_count / 8) * 100
        
        # Ajuste se modelos ML não treinados
        trained_ml_models = sum([
            1 if (self.xgboost_model and self.xgboost_model.is_trained) else 0,
            1 if (self.neural_network_model and self.neural_network_model.is_trained) else 0,
            1 if (self.catboost_model and self.catboost_model.is_trained) else 0,
            1 if (self.random_forest_model and self.random_forest_model.is_trained) else 0,
        ])
        
        if trained_ml_models < 4:
            confidence = confidence * 0.9  # Reduz 10% se menos de 4 modelos ML treinados
        
        return min(confidence, 85.0)  # Máximo 85%
```

---

## 8. EXPLAINABILITY (SHAP)

### 8.1 O Que é SHAP?

**SHAP** (SHapley Additive exPlanations) é um framework para explainability de modelos ML. Explica porquê o modelo prediz um valor específico.

### 8.2 Implementação SHAP

```python
import shap
import numpy as np
import logging

logger = logging.getLogger(__name__)

class SHAPExplainer:
    """Explainer SHAP para XGBoost Model."""
    
    def __init__(self, xgboost_model):
        self.model = xgboost_model
        self.explainer = None
        self.is_initialized = False
    
    def initialize(self):
        """Inicializa explainer SHAP."""
        if not self.model or not self.model.is_trained:
            raise ValueError("Modelo não treinado")
        
        self.explainer = shap.TreeExplainer(self.model.model)
        self.is_initialized = True
        logger.info("SHAPExplainer: Explainer inicializado")
    
    def explain(self, listing: Dict) -> Dict:
        """Explica predição para um listing."""
        if not self.is_initialized:
            raise ValueError("Explainer não inicializado")
        
        # Extrair features
        features = self.model._extract_features_dict(listing)
        
        # Calcular SHAP values
        shap_values = self.explainer.shap_values(np.array([features]))
        
        # Explicação
        explanation = {
            'base_value': float(shap_values.base_values[0]),
            'shap_values': shap_values.values[0].tolist(),
            'feature_names': self.model.feature_names
        }
        
        return explanation
```

---

## 9. CONFIDENCE INTERVALS

### 9.1 O Que são Confidence Intervals?

**Confidence Intervals** (IC) são intervalos onde o valor real tem 95% de probabilidade de estar.

**Exemplo:**
- Valor justo estimado: 200.000€
- CI lower: 180.000€
- CI upper: 220.000€
- Interpretação: Há 95% de probabilidade que o valor real esteja entre 180.000€ e 220.000€

### 9.2 Cálculo de Confidence Intervals

```python
import numpy as np
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class ConfidenceIntervalCalculator:
    """Calcula intervalos de confiança."""
    
    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level
        self.z_score = 1.96  # Para 95% confiança
    
    def calculate(self, predicted_value: float, std_error: float) -> Dict:
        """Calcula intervalo de confiança."""
        margin = self.z_score * std_error
        
        ci_lower = predicted_value - margin
        ci_upper = predicted_value + margin
        
        return {
            'ci_lower': max(ci_lower, 0),  # Não pode ser negativo
            'ci_upper': ci_upper,
            'confidence_level': self.confidence_level
        }
    
    def calculate_from_ensemble(self, values: Dict) -> Dict:
        """Calcula IC baseado na variância do ensemble."""
        # Calcular desvio padrão dos valores
        valid_values = [v for v in values.values() if v > 0]
        
        if len(valid_values) < 2:
            # Se só um valor válido, usar ±10%
            predicted_value = valid_values[0]
            return {
                'ci_lower': predicted_value * 0.9,
                'ci_upper': predicted_value * 1.1,
                'confidence_level': self.confidence_level
            }
        
        # Calcular desvio padrão
        std_error = np.std(valid_values)
        mean_value = np.mean(valid_values)
        
        return self.calculate(mean_value, std_error)
```

---

## 10. PERFORMANCE VALUATION

### 10.1 Métricas de Performance

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              MÉTRICAS DE PERFORMANCE VALUATION                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PRECISÃO (MAE):                                                          │
│  - Mean Absolute Error (MAE): < 10% do valor de mercado               │
│  - Exemplo: Valor real = 200.000€, Predição = 190.000€, MAE = 5%         │
│  - Objectivo: MAE < 10%                                                    │
│                                                                             │
│  CONFIDENCE:                                                               │
│  - Confiança: 70-85% (dependendo da disponibilidade de dados)             │
│  - Mais dados = mais confiança                                            │
│  - Menos dados = menos confiança                                          │
│                                                                             │
│  TEMPO DE PREDIÇÃO:                                                        │
│  - Hedonic Model: < 0.1 segundos por listing                              │
│  - Comps Engine: 0.5-1 segundos por listing (query database)              │
│  - INE Macro Data: < 0.1 segundos por listing                             │
│  - XGBoost Model: < 0.05 segundos por listing                              │
│  - Weighted Ensemble: < 0.2 segundos por listing                           │
│  - Total: < 2 segundos por listing                                       │
│                                                                             │
│  THROUGHPUT:                                                                │
│  - 1000 listings: < 2000 segundos (33 minutos)                           │
│  - 5000 listings: < 10000 segundos (167 minutos)                         │
│                                                                             │
│  OPTIMIZAÇÃO:                                                            │
│  - Batch predictions (XGBoost)                                            │
│  - Cache de comparáveis (Comps Engine)                                   │
│  - Lazy loading de dados INE                                              │
│  - Resultado: 50% redução de tempo                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 11. TRAINING E RETRAINING

### 11.1 Estratégia de Training

```python
from typing import List, Dict
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ValuationTrainer:
    """Gestão de training e retraining dos modelos."""
    
    def __init__(self):
        self.last_training_date = None
        self.retraining_interval_days = 30  # Retreinar a cada 30 dias
        self.min_samples = 1000  # Mínimo 1000 listings para treinar
    
    async def should_retrain(self, database_repository) -> bool:
        """Verifica se deve retreinar modelo."""
        if not self.last_training_date:
            return True
        
        days_since_training = (datetime.now() - self.last_training_date).days
        
        if days_since_training >= self.retraining_interval_days:
            # Verificar se há dados suficientes
            sample_count = await database_repository.count_clean_listings()
            if sample_count >= self.min_samples:
                return True
        
        return False
    
    async def train_all_models(self, database_repository):
        """Treina todos os modelos."""
        logger.info("ValuationTrainer: Iniciando training de todos os modelos")
        
        # Obter dados de treino
        listings = await database_repository.get_clean_listings_for_training()
        
        if len(listings) < self.min_samples:
            logger.warning(f"ValuationTrainer: Dados insuficientes ({len(listings)} < {self.min_samples})")
            return
        
        # Treinar Hedonic Model
        hedonic_model = HedonicModel()
        hedonic_model.train(listings)
        
        # Treinar XGBoost (opcional)
        xgboost_model = XGBoostModel()
        xgboost_model.train(listings)
        
        # Guardar modelos
        self._save_models(hedonic_model, xgboost_model)
        
        # Actualizar data de training
        self.last_training_date = datetime.now()
        
        logger.info("ValuationTrainer: Training completo")
    
    def _save_models(self, hedonic_model, xgboost_model):
        """Guarda modelos em ficheiro."""
        # Implementação: guardar modelos com pickle/joblib
        pass
```

---

## 12. MODEL EVALUATION

### 12.1 Métricas de Avaliação

```python
from typing import Dict, List
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import logging

logger = logging.getLogger(__name__)

class ModelEvaluator:
    """Avaliação de modelos de valuation."""
    
    def __init__(self):
        pass
    
    def evaluate(self, y_true: List[float], y_pred: List[float]) -> Dict:
        """Avalia modelo com múltiplas métricas."""
        mae = mean_absolute_error(y_true, y_pred)
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_true, y_pred)
        
        # MAE percentual
        mae_percentual = np.mean(np.abs((np.array(y_true) - np.array(y_pred)) / np.array(y_true))) * 100
        
        return {
            'mae': mae,
            'mae_percentual': mae_percentual,
            'mse': mse,
            'rmse': rmse,
            'r2': r2
        }
```

---

## 13. DEPLOYMENT DO MODEL

### 13.1 Deployment Strategy

```python
import pickle
import logging

logger = logging.getLogger(__name__)

class ModelDeployment:
    """Deployment de modelos de valuation."""
    
    def __init__(self):
        self.model_dir = 'data/models/'
    
    def save_model(self, model, model_name: str):
        """Guarda modelo em ficheiro."""
        model_path = f"{self.model_dir}{model_name}.pkl"
        
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        logger.info(f"ModelDeployment: Modelo {model_name} guardado em {model_path}")
    
    def load_model(self, model_name: str):
        """Carrega modelo de ficheiro."""
        model_path = f"{self.model_dir}{model_name}.pkl"
        
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        logger.info(f"ModelDeployment: Modelo {model_name} carregado de {model_path}")
        
        return model
```

---

## 14. MONITORING VALUATION

### 14.1 Métricas de Valuation

```python
from typing import Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ValuationMetrics:
    """Métricas do Valuation Engine."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.total_valuations = 0
        self.total_discount_positive = 0
        self.total_discount_negative = 0
        self.avg_confidence = 0.0
    
    def start(self):
        """Inicia medição."""
        self.start_time = datetime.now()
    
    def end(self):
        """Termina medição."""
        self.end_time = datetime.now()
    
    def record_valuation(self, valuation: Dict):
        """Registra valuation."""
        self.total_valuations += 1
        
        discount = valuation.get('discount', 0)
        if discount > 0:
            self.total_discount_positive += 1
        elif discount < 0:
            self.total_discount_negative += 1
        
        confidence = valuation.get('confianca', 0)
        self.avg_confidence = (self.avg_confidence * (self.total_valuations - 1) + confidence) / self.total_valuations
    
    def get_summary(self) -> Dict:
        """Retorna resumo de métricas."""
        return {
            'duration_seconds': (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0,
            'total_valuations': self.total_valuations,
            'total_discount_positive': self.total_discount_positive,
            'total_discount_negative': self.total_discount_negative,
            'avg_confidence': self.avg_confidence,
            'discount_positive_rate': (self.total_discount_positive / self.total_valuations * 100) if self.total_valuations > 0 else 0,
            'throughput_valuations_per_second': self.total_valuations / ((self.end_time - self.start_time).total_seconds()) if self.start_time and self.end_time and self.total_valuations > 0 else 0
        }
```

---

## 15. GLOSSÁRIO DE VALUATION

```
┌─────────────────────────────────────────────────────────────────────────────┐
│            GLOSSÁRIO DE VALUATION                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  VALUATION ENGINE: Motor que calcula valor justo estimado                 │
│                                                                             │
│  VALOR JUSTO: Preço de mercado esperado para um imóvel                   │
│                                                                             │
│  DISCOUNT: Diferença entre valor justo e preço pedido (%)               │
│                                                                             │
│  HEDONIC MODEL: Modelo de regressão linear para valuation               │
│                                                                             │
│  COMPS ENGINE: Engine que encontra comparáveis similares                 │
│                                                                             │
│  INE MACRO DATA: Dados macro do INE (preço médio, tendências)            │
│                                                                             │
│  XGBOOST MODEL: Modelo de gradient boosting para ML não-linear            │
│                                                                             │
│  WEIGHTED ENSEMBLE: Combinação de múltiplos modelos com pesos          │
│                                                                             │
│  SHAP: Framework para explainability de modelos ML                      │
│                                                                             │
│  CONFIDENCE INTERVAL: Intervalo onde o valor real tem X% de probabilidade│
│                                                                             │
│  MAE (Mean Absolute Error): Erro médio absoluto                             │
│                                                                             │
│  MSE (Mean Squared Error): Erro médio quadrático                          │
│                                                                             │
│  RMSE (Root Mean Squared Error): Raiz do erro médio quadrático        │
│                                                                             │
│  R² (R-Squared): Coeficiente de determinação                              │
│                                                                             │
│  CONFIDENCE: Grau de confiança na predição (0-100%)                     │
│                                                                             │
│  RETRAINING: Retreinar modelo com novos dados                             │
│                                                                             │
│  TRAINING: Treinar modelo pela primeira vez                              │
│                                                                             │
│  FEATURE: Característica usada pelo modelo (área, quartos, etc.)      │
│                                                                             │
│  COEFFICIENT: Valor que representa impacto de uma feature no preço      │
│                                                                             │
│  INTERCEPT: Preço base (quando todas as features são zero)               │
│                                                                             │
│  ONE-HOT ENCODING: Representação de variáveis categóricas como binárias │
│                                                                             │
│  GRADIENT BOOSTING: Técnica de ML que usa múltiplos modelos fracos     │
│                                                                             │
│  ENSEMBLE: Combinação de múltiplos modelos para melhor predição        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*Fim do Documento 06 — Valuation Engine*
