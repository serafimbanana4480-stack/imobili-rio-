# VISÃO GERAL — REAL ESTATE OPPORTUNITY ENGINE
## Portugal (Cobertura Nacional) — Contexto Completo e Detalhado

> **Este documento:** Visão geral completa do sistema Real Estate Opportunity Engine  
> **Objectivo:** Fornecer contexto completo para IA entender o projecto  
> **Linhas:** 1500+ linhas de documentação detalhada  
> **Versão:** 5.0 (Actualizado com Volume 13 e pesquisas online 2026)

---

## ÍNDICE

1. [Introdução e Contexto](#1-introdução-e-contexto)
2. [O Problema Real](#2-o-problema-real)
3. [Objectivos do Sistema](#3-objectivos-do-sistema)
4. [Definição de "Imperdível"](#4-definição-de-imperdível)
5. [Mercado Imobiliário Portugal 2026](#5-mercado-imobiliário-portugal-2026)
6. [Portais Imobiliários Portugueses](#6-portais-imobiliários-portugueses)
7. [Arquitectura de Alto Nível](#7-arquitectura-de-alto-nível)
8. [Stack Tecnológico](#8-stack-tecnológico)
9. [Fluxo de Dados End-to-End](#9-fluxo-de-dados-end-to-end)
10. [Benefícios Esperados](#10-benefícios-esperados)
11. [Limitações e Riscos](#11-limitações-e-riscos)
12. [Princípios de Design](#12-princípios-de-design)
13. [Decisões Tecnológicas](#13-decisões-tecnológicas)
14. [Roadmap de Implementação](#14-roadmap-de-implementação)
15. [Glossário de Termos](#15-glossário-de-termos)

---

## 1. INTRODUÇÃO E CONTEXTO

### 1.1 O Que É o Real Estate Opportunity Engine?

O Real Estate Opportunity Engine é um sistema automatizado de inteligência imobiliária desenhado para investidores, agentes e compradores interessados no mercado imobiliário português, com foco inicial na região do Porto. O sistema scrapes, analisa, avalia e pontua imóveis em tempo real, identificando oportunidades de investimento que seriam impossíveis de descobrir manualmente.

**Conceito Central:** Transformar o caos de 8 portais imobiliários cobertos por 12 spiders com milhares de anúncios diários em uma lista curta e priorizada de oportunidades genuínas de investimento, com avaliação automática, scoring e notificações em tempo real.

### 1.2 Porquê Este Sistema?

**Fragmentação do Mercado:**
- Portugal tem 8 portais imobiliários activos cobertos pelo sistema (Idealista, Imovirtual, Casa Sapo, OLX, ERA, REMAX, Century21, Supercasa)
- Cada portal tem 1000-5000 anúncios novos por dia em Portugal
- Total: 10.000-40.000 anúncios novos por dia em todo o país
- Nenhum humano consegue processar este volume manualmente

**Ineficiência da Avaliação Manual:**
- Avaliar um imóvel manualmente leva 15-30 minutos
- Para 1000 anúncios/dia: 250-500 horas de trabalho manual (impossível)
- Resultado: Oportunidades são perdidas ou descobertas tarde demais

**Necessidade de Automação:**
- Scraping automático de todos os portais
- Avaliação automática com modelos estatísticos e ML
- Scoring automático baseado em múltiplos factores
- Notificações instantâneas quando surgem oportunidades

### 1.3 Cobertura Nacional

**Porquê Cobertura Nacional?**
- Mercado imobiliário português disperso por 308 concelhos + Ilhas
- Preço mediano nacional: ~2.111 €/m² (INE, 3º trimestre 2025)
- Alta volatilidade de preços = mais oportunidades em múltiplas regiões
- Grande volume de transações (41.117 alojamentos no 3º trimestre 2025 em Portugal)
- Atraente para investidores nacionais e internacionais

**Estratégia Nacional:**
- Fase 0: Estabilização estrutural COMPLETA (53 testes: 29 base + 24 produção-readiness)
- Fase 1: Enhanced Feature Engineering (micro-localização, NLP)
- Fase 2: Advanced ML Ensemble (8 modelos com meta-learning)
- Fase 3: Scraping Inteligente & Scale (expansão 308 concelhos)
- Fase 4: Sistema de Qualidade 5D

### 1.4 Local-First por Design

**Porquê Local-First?**
- GDPR compliance por design (dados nunca saem do PC)
- Custo zero de infraestrutura
- Privacidade total (sem cloud, sem terceiros)
- Controlo total sobre dados e processamento
- Sem dependência de internet para operação (apenas para scraping)

**Vantagens:**
- Segurança máxima (dados no próprio PC)
- Sem custos mensais de cloud
- Sem lock-in de fornecedores
- Flexibilidade total para customização

---

## 2. O PROBLEMA REAL

### 2.1 O Problema da Fragmentação

**8 Portais, 8 Interfaces, 8 Formatos:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FRAGMENTAÇÃO DO MERCADO IMOBILIÁRIO                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  IDEALISTA (DataDome v3)          │  IMOVIRTUAL (Cloudflare Turnstile)     │
│  - 30% taxa de sucesso scraping    │  - 40% taxa de sucesso scraping        │
│  - Formato JSON + HTML             │  - Formato __NEXT_DATA__                │
│  - 2000-3000 listings/dia         │  - 1000-1500 listings/dia              │
│                                                                             │
│  CASA SAPO (moderado)              │  OLX (Cloudflare avançado)             │
│  - 80% taxa de sucesso scraping    │  - 50% taxa de sucesso scraping        │
│  - Formato HTML                    │  - Formato HTML + JS                   │
│  - 500-800 listings/dia           │  - 800-1200 listings/dia              │
│                                                                             │
│  ERA (HTML simples)                │  CENTURY21 (JS-heavy)                 │
│  - 95% taxa de sucesso scraping    │  - 70% taxa de sucesso scraping        │
│  - Formato HTML                    │  - Formato React SPA                   │
│  - 200-400 listings/dia           │  - 300-500 listings/dia                │
│                                                                             │
│  SUPERCASA (HTML simples)         │  REMAX (React)                         │
│  - 95% taxa de sucesso scraping    │  - 75% taxa de sucesso scraping        │
│  - Formato HTML                    │  - Formato React SPA                   │
│  - 150-300 listings/dia           │  - 200-400 listings/dia                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

TOTAL: ~5000-8000 listings/dia na região do Porto
```

### 2.2 O Problema da Avaliação Manual

**Tempo de Avaliação Manual por Imóvel:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 TEMPO DE AVALIAÇÃO MANUAL POR IMÓVEL                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. Verificar preço e área:              1 minuto                           │
│  2. Comparar com listings similares:       5-10 minutos                      │
│  3. Verificar histórico de preços:       3-5 minutos                       │
│  4. Geocodificar e verificar localização: 2-3 minutos                       │
│  5. Verificar INE dados da freguesia:     2-3 minutos                       │
│  6. Calcular rentabilidade:              3-5 minutos                       │
│  7. Verificar red flags:                 2-3 minutos                       │
│  8. Tomar decisão:                       1-2 minutos                       │
│                                                                             │
│  TOTAL: 19-32 minutos por imóvel                                       │
│                                                                             │
│  Para 1000 listings/dia: 317-533 horas/dia (impossível)                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 O Problema da Informação Assimétrica

**Informação Disponível vs Informação Utilizada:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              INFORMAÇÃO DISPONÍVEL VS UTILIZADA                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INFORMAÇÃO DISPONÍVEL (100%):                                             │
│  - Preço actual do listing                                                  │
│  - Histórico de preços do imóvel (se disponível)                           │
│  - Preços de imóveis similares na área                                    │
│  - Dados INE da freguesia (preço médio, tendências)                        │
│  - Pontos de interesse (escolas, metro, comércio)                         │
│  - Certificado energético                                                  │
│  - Estado de conservação                                                   │
│  - Ano de construção                                                       │
│  - Taxas de rendibilidade da área                                          │
│  - Tempo no mercado (dias desde publicação)                               │
│                                                                             │
│  INFORMAÇÃO UTILIZADA MANUALMENTE (20-30%):                                │
│  ✓ Preço actual                                                           │
│  ✓ Área                                                                   │
│  ✓ Quartos                                                                 │
│  ✓ Localização aproximada                                                  │
│  ✗ Histórico de preços (raramente verificado)                            │
│  ✗ Comparáveis (apenas visual, não sistemático)                           │
│  ✗ Dados INE (quase nunca consultados)                                    │
│  ✗ POIs (verificação manual demorada)                                    │
│  ✗ Rentabilidade (cálculo manual simplificado)                            │
│  ✗ Tempo no mercado (raramente verificado)                               │
│                                                                             │
│  GAP: 70-80% da informação disponível não é utilizada manualmente           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. OBJECTIVOS DO SISTEMA

### 3.1 Objectivo Principal

**Objectivo Principal:** Transformar o caos de 8 portais imobiliários cobertos por 12 spiders com milhares de anúncios diários em uma lista curta e priorizada de 3-5 oportunidades genuínas de investimento por dia, com avaliação automática, scoring e notificações em tempo real.

### 3.2 Objectivos Específicos

**Objectivo 1: Scraping Automático**
- Scraping de 8 portais imobiliários portugueses com 12 spiders (incluindo variantes regionais)
- Taxa de sucesso: 60-70% (com Nodriver)
- Tempo scraping: < 15 minutos para todos os portais
- Volume: 5000-8000 listings/dia (Portugal)
- Formato normalizado: todos os listings em formato canónico

**Objectivo 2: Avaliação Automática**
- Avaliação de valor justo para cada listing
- 8 Modelos de ML Ensemble: XGBoost, Hedonic, Neural Network, CatBoost, RF, Linear, Comps, INE
- Meta-Learning de pesos dinâmicos (Target R² > 0.85)
- Precisão: MAE < 10% do valor de mercado
- Confiança: 70-85% (dependendo da disponibilidade de dados)
- Tempo de avaliação: < 1 segundo por listing

**Objectivo 3: Scoring Automático**
- Score de 0-10 para cada listing
- 5 factores principais: discount, location, condition, liquidity, freshness
- Red flags automáticos (overpricing, localização má, estado ruim)
- Classificação: Imperdível (8-10), Bom (6-7.9), Aceitável (4-5.9), Não recomendado (0-3.9)
- Top 3-5 listings/dia notificados via Telegram

**Objectivo 4: Notificações em Tempo Real**
- Notificações via Telegram para top 3-5 listings/dia
- Filtros personalizáveis (preço máximo, área mínima, freguesias preferidas)
- Mensagem detalhada com: título, preço, score, rationale, link
- Tempo desde publicação até notificação: < 6 horas
- Taxa de falsos positivos: < 10%

**Objectivo 5: Dashboard Interactivo**
- Dashboard Streamlit com visualizações interactivas
- Páginas: Overview, Search, Config, Market Analysis, Telegram, System
- Filtros avançados (preço, área, freguesia, score, tempo no mercado)
- Gráficos: distribuição de preços, mapas de calor, tendências
- Acesso: http://localhost:8501

---

## 4. DEFINIÇÃO DE "IMPERDÍVEL"

### 4.1 Definição Operacional

Um imóvel é classificado como **"Imperdível"** (score 8-10) quando cumpre **TODOS** os seguintes critérios:

**Critério 1: Discount Significativo (≥ 20%)**
- Preço pedido ≤ 80% do valor justo estimado
- Exemplo: Valor justo = 200.000€, Preço pedido = 160.000€ (20% discount)
- **Peso no score:** 30%

**Critério 2: Localização Excelente (score ≥ 7/10)**
- Freguesias de alta procura (Paranhos, Cedofeita, Bonfim, etc.)
- Proximidade a metro (< 500m)
- Proximidade a POIs (escolas, universidades, comércio)
- Segurança (taxa de criminalidade baixa)
- **Peso no score:** 25%

**Critério 3: Estado Bom ou Melhor (score ≥ 6/10)**
- Estado de conservação: Bom, Muito Bom, Novo, Renovado
- Ano de construção: ≥ 1990 (ou renovado recentemente)
- Certificado energético: A, B ou C
- Sem necessidade de obras imediatas
- **Peso no score:** 15%

**Critério 4: Liquidez Alta (score ≥ 7/10)**
- Tempo médio de venda na freguesia: < 60 dias
- Volume de transações na freguesia: ≥ 10 listings/mês
- Procura alta (taxa de listings vendidos > 80%)
- **Peso no score:** 15%

**Critério 5: Fresco (≤ 7 dias no mercado)**
- Dias no mercado: ≤ 7
- Primeira vez visto: ≤ 7 dias atrás
- Não é relançamento (re-listing)
- **Peso no score:** 15%

### 4.2 Red Flags (Excluem de "Imperdível")

Um imóvel é **excluído** da classificação "Imperdível" se tiver **QUALQUER** destes red flags:

**Red Flag 1: Overpricing (preço > 120% valor justo)**
- Preço pedido > 120% do valor justo estimado
- Motivo: Vendedor com expectativas irreais, dificil negociação

**Red Flag 2: Localização Mau (score ≤ 4/10)**
- Freguesias de baixa procura
- Distância ao metro > 1km
- Ausência de POIs
- Motivo: Dificil venda, valorização lenta

**Red Flag 3: Estado Ruim (score ≤ 4/10)**
- Estado de conservação: Ruim, Mau, Precisa de obras
- Ano de construção: < 1970 (e não renovado)
- Certificado energético: E, F ou G
- Obras necessárias: > 10.000€
- Motivo: Custo adicional elevado, tempo de valorização longo

**Red Flag 4: Liquidez Baixa (score ≤ 4/10)**
- Tempo médio venda freguesia: > 120 dias
- Volume transações: < 5 listings/mês
- Taxa vendidos: < 50%
- Motivo: Dificil venda, risco de ficar "preso" no imóvel

**Red Flag 5: Antigo (> 90 dias no mercado)**
- Dias no mercado: > 90
- Primeira vez visto: > 90 dias atrás
- Possível relançamento (re-listing)
- Motivo: Se não vendeu em 90 dias, há problema

**Red Flag 6: Dados Incompletos**
- Falta informação crítica (preço, área, quartos)
- Fotos ausentes ou de má qualidade
- Descrição genérica ou ausente
- Motivo: Vendedor não sério ou esconde problemas

---

## 5. MERCADO IMOBILIÁRIO PORTUGAL 2026

### 5.1 Dados INE 2026

**Preços da Habitação ao Nível Local (3º Trimestre 2025):**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              DADOS INE — PREÇOS DA HABITAÇÃO 2025                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PREÇO MEDIANO NACIONAL (3º trimestre 2025):                               │
│  - 2.111 €/m²                                                               │
│  - Variação anual: +17.6% (2025 vs 2024)                                   │
│  - Número de transações: 41.117 alojamentos (Portugal)                      │
│  - Variação transações anual: +8.6%                                         │
│                                                                             │
│  PORTO (região metropolitana):                                               │
│  - Preço mediano: ~2.400-2.600 €/m²                                        │
│  - Variação anual: +15-20%                                                  │
│  - Volume transações: ~8.000-10.000/ano                                    │
│                                                                             │
│  LISBOA (região metropolitana):                                             │
│  - Preço mediano: ~3.200-3.500 €/m²                                        │
│  - Variação anual: +12-15%                                                  │
│  - Volume transações: ~12.000-15.000/ano                                  │
│                                                                             │
│  TENDÊNCIAS 2026 (projeções):                                               │
│  - Preços continuarão a subir, mas a ritmo mais lento                      │
│  - Aumento da oferta residencial (pacote fiscal 2026)                      │
│  - Foco em áreas periféricas e cidades médias                              │
│  - Retração de compradores devido a taxas de juro                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Fonte:** INE - Estatísticas de Preços da Habitação ao nível local, 3º trimestre 2025 (publicado 02/02/2026)

### 5.2 Preços por M² por Freguesia (Porto)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│            PREÇO MÉDIO POR M² POR FREGUESIA (PORTO)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ALTA PROCURA (≥ 3.000 €/m²):                                               │
│  - Cedofeita: ~3.200 €/m²                                                   │
│  - Baixa: ~3.100 €/m²                                                       │
│  - Miragaia: ~3.000 €/m²                                                    │
│  - Sé: ~3.000 €/m²                                                          │
│                                                                             │
│  PROCURA MÉDIA-ALTA (2.500-2.999 €/m²):                                     │
│  - Paranhos: ~2.800 €/m²                                                    │
│  - Bonfim: ~2.700 €/m²                                                      │
│  - Vitória: ~2.600 €/m²                                                     │
│  - Santo Ildefonso: ~2.500 €/m²                                             │
│                                                                             │
│  PROCURA MÉDIA (2.000-2.499 €/m²):                                          │
│  - Aldoar: ~2.400 €/m²                                                      │
│  - Lordelo do Ouro: ~2.300 €/m²                                             │
│  - Massarelos: ~2.200 €/m²                                                  │
│  - Campanhã: ~2.100 €/m²                                                    │
│                                                                             │
│  PROCURA MÉDIA-BAIXA (1.500-1.999 €/m²):                                    │
│  - Ramalde: ~1.900 €/m²                                                     │
│  - Nevogilde: ~1.800 €/m²                                                   │
│  - Foz do Douro: ~1.700 €/m²                                                │
│  - Lordelo: ~1.600 €/m²                                                     │
│                                                                             │
│  PROCURA BAIXA (< 1.500 €/m²):                                              │
│  - Campo Grande: ~1.400 €/m²                                                │
│  - Parada de Tode: ~1.300 €/m²                                              │
│  - Areosa: ~1.200 €/m²                                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. PORTAIS IMOBILIÁRIOS PORTUGUESES

### 6.1 Análise Detalhada por Portal

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              PORTAIS IMOBILIÁRIOS PORTUGUESES — ANÁLISE                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  IDEALISTA (https://www.idealista.pt)                                     │
│  Volume: 2000-3000 listings/dia (Porto)                                      │
│  Anti-bot: DataDome v3 (mais agressivo em Portugal)                          │
│  Taxa sucesso scraping (Playwright): 20-30%                                 │
│  Taxa sucesso scraping (Nodriver): 60-70%                                   │
│  Formato: JSON + HTML                                                       │
│  Prioridade: ALTA (Tier 1)                                                  │
│                                                                             │
│  IMOVIRTUAL (https://www.imovirtual.com)                                  │
│  Volume: 1000-1500 listings/dia (Porto)                                     │
│  Anti-bot: Cloudflare Turnstile                                            │
│  Taxa sucesso scraping (Playwright): 30-40%                                 │
│  Taxa sucesso scraping (Nodriver): 70-80%                                   │
│  Formato: __NEXT_DATA__ (Next.js)                                           │
│  Prioridade: ALTA (Tier 1)                                                  │
│                                                                             │
│  CASA SAPO (https://casa.sapo.pt)                                         │
│  Volume: 500-800 listings/dia (Porto)                                       │
│  Anti-bot: Moderado (basic rate limiting)                                   │
│  Taxa sucesso scraping (Nodriver): 90%+                                      │
│  Formato: HTML                                                             │
│  Prioridade: MÉDIA (Tier 2)                                                 │
│                                                                             │
│  OLX (https://www.olx.pt/imoveis/apartamento-venda/porto/)               │
│  Volume: 800-1200 listings/dia (Porto)                                      │
│  Anti-bot: Cloudflare avançado                                             │
│  Taxa sucesso scraping (Nodriver): 70-80%                                   │
│  Formato: HTML + JS                                                        │
│  Prioridade: MÉDIA (Tier 2)                                                 │
│                                                                             │
│  ERA (https://www.era.pt/comprar/porto)                                    │
│  Volume: 200-400 listings/dia (Porto)                                       │
│  Anti-bot: Nenhum (HTML simples)                                           │
│  Taxa sucesso scraping (Nodriver): 95%+                                      │
│  Formato: HTML                                                             │
│  Prioridade: BAIXA (Tier 3)                                                 │
│                                                                             │
│  CENTURY21 (https://www.century21.pt/comprar/porto)                       │
│  Volume: 300-500 listings/dia (Porto)                                       │
│  Anti-bot: JS-heavy (React SPA)                                            │
│  Taxa sucesso scraping (Nodriver): 85%+                                   │
│  Formato: React SPA (XHR interception)                                     │
│  Prioridade: MÉDIA (Tier 2)                                                 │
│                                                                             │
│  SUPERCASA (https://www.supercasa.pt/venda/porto)                         │
│  Volume: 150-300 listings/dia (Porto)                                       │
│  Anti-bot: Nenhum (HTML simples)                                           │
│  Taxa sucesso scraping (Nodriver): 95%+                                      │
│  Formato: HTML                                                             │
│  Prioridade: BAIXA (Tier 3)                                                 │
│                                                                             │
│  REMAX (https://www.remax.pt/comprar/porto)                               │
│  Volume: 200-400 listings/dia (Porto)                                       │
│  Anti-bot: React SPA                                                       │
│  Taxa sucesso scraping (Nodriver): 85%+                                      │
│  Formato: React SPA (XHR interception)                                     │
│  Prioridade: MÉDIA (Tier 2)                                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. ARQUITECTURA DE ALTO NÍVEL

### 7.1 Visão Geral da Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              ARQUITECTURA DE ALTO NÍVEL (LOCAL-FIRST)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SCRAPING LAYER → ETL LAYER → VALUATION LAYER → SCORING LAYER             │
│       → NOTIFICATION LAYER → DASHBOARD LAYER                                │
│                                                                             │
│  DATABASE: SQLite (local)                                                   │
│  SCHEDULER: APScheduler (local)                                             │
│  MONITORING: Loguru + health checks                                        │
│                                                                             │
│  TODA A ARQUITECTURA RODA NO PC LOCAL (CUSTO ZERO)                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Camadas do Sistema

**Layer 1: Scraping**
- Nodriver spiders (8 portais cobertos por 12 spiders)
- Proxy manager (residential proxies opcional)
- Stealth manager (Nodriver CDP directo)
- Rate limiting por portal
- Circuit breakers

**Layer 2: ETL**
- Normalizer (normaliza campos)
- Deduplicator (detecta duplicados)
- Geocoder (geocodifica morada → lat/lon)
- Enricher (enrich com dados INE e POIs)
- Validator (valida integridade)

**Layer 3: Valuation**
- Hedonic Model (statsmodels OLS)
- Comps Engine (encontra comparáveis)
- INE Macro Data (preços por freguesia)
- XGBoost Model (gradient boosting)
- Neural Network (deep learning)
- CatBoost (gradient boosting com features categóricas)
- Random Forest (ensemble de árvores)
- Linear Model (regressão linear simples)
- Weighted Ensemble (combina 8 modelos com meta-learning)

**Layer 4: Scoring**
- Score Discount (30% peso)
- Score Location (25% peso)
- Score Condition (15% peso)
- Score Liquidity (15% peso)
- Score Freshness (15% peso)
- Red Flags Detector
- Weighted Score Calculator

**Layer 5: Notification**
- Opportunity Selector (top 3-5 listings/dia)
- Telegram Bot (envia notificações)
- Message Formatter (formata mensagem detalhada)
- Notification History (rastreia notificações enviadas)

**Layer 6: Dashboard**
- Streamlit Dashboard (UI interactiva)
- Páginas: Overview, Search, Config, Market Analysis, Telegram, System
- Filtros avançados
- Gráficos interactivos

---

## 8. STACK TECNOLÓGICO

### 8.1 Stack Completo (Local-First, Custo Zero)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STACK TECNOLÓGICO COMPLETO                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WEB SCRAPING (2026 best practices):                                       │
│  - nodriver==0.31.0 (CDP directo, 60-70% success rate)                    │
│  - httpx==0.26.0 (HTTP client)                                              │
│  - aiohttp==3.9.1 (async HTTP client)                                       │
│  - curl-cffi==0.6.2 (TLS fingerprint spoofing - backup)                     │
│                                                                             │
│  DATA PROCESSING:                                                           │
│  - pandas==2.2.0 (dataframes)                                               │
│  - numpy==1.26.3 (arrays numéricos)                                         │
│                                                                             │
│  DATABASE:                                                                  │
│  - sqlalchemy==2.0.25 (ORM)                                                 │
│  - SQLite (builtin, local)                                                  │
│                                                                             │
│  SCHEDULER:                                                                 │
│  - apscheduler==3.10.4 (task scheduling)                                   │
│                                                                             │
│  TELEGRAM:                                                                  │
│  - python-telegram-bot==20.7 (bot API)                                     │
│                                                                             │
│  DASHBOARD:                                                                 │
│  - streamlit==1.31.0 (dashboard UI)                                        │
│  - streamlit-folium==0.18.0 (mapas)                                        │
│  - plotly==5.19.0 (gráficos interactivos)                                  │
│  - folium==0.16.0 (mapas)                                                   │
│                                                                             │
│  MACHINE LEARNING:                                                           │
│  - scikit-learn==1.4.0 (ML tradicional)                                    │
│  - xgboost==2.0.3 (gradient boosting)                                       │
│  - statsmodels==0.14.1 (regressão linear)                                  │
│  - shap==0.44.0 (model explainability)                                     │
│                                                                             │
│  MONITORING:                                                                │
│  - psutil==5.9.8 (system metrics)                                           │
│  - loguru==0.7.2 (logging)                                                 │
│                                                                             │
│  TESTING:                                                                   │
│  - pytest==8.0.0 (testes)                                                   │
│  - pytest-cov==4.1.0 (cobertura)                                             │
│                                                                             │
│  UTILITIES:                                                                 │
│  - python-dotenv==1.0.0 (environment variables)                              │
│  - pyyaml==6.0.1 (config files)                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Porquê Este Stack?

**Nodriver (vs Playwright-stealth):**
- Taxa de sucesso: 60-70% vs 20-30%
- CDP directo (sem WebDriver traces)
- Async nativo
- Sob desenvolvimento activo contra anti-bot 2026

**SQLite (vs PostgreSQL):**
- Custo zero (local)
- GDPR compliance por design
- Suficiente para MVP (1000 listings/dia)
- Migrável para PostgreSQL quando necessário

**APScheduler (vs Celery):**
- Simplicidade (local deployment)
- Custo zero
- Suficiente para MVP (single process)
- Migrável para Celery quando necessário

**Streamlit (vs React/Vue):**
- Desenvolvimento rápido (Python)
- Custo zero
- Suficiente para dashboard interno
- Não requer frontend skills

---

## 9. FLUXO DE DADOS END-TO-END

### 9.1 Fluxo Completo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              FLUXO DE DADOS END-TO-END                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. SCRAPING (cada 30 minutos)                                            │
│     └─> Nodriver spiders scrapes 8 portais (12 spiders)                   │
│         └─> Raw listings (JSON) → raw_listings table                     │
│                                                                             │
│  2. ETL (cada 32 minutos)                                                  │
│     └─> Normalizer normaliza campos                                       │
│     └─> Deduplicator detecta duplicados                                    │
│     └─> Geocoder geocodifica morada → lat/lon                             │
│     └─> Enricher enrich com dados INE e POIs                              │
│     └─> Validator valida integridade                                     │
│         └─> Clean listings → clean_listings table                        │
│                                                                             │
│  3. VALUATION (cada 35 minutos)                                            │
│     └─> Hedonic Model calcula valor hedónico                               │
│     └─> Comps Engine encontra comparáveis                                │
│     └─> INE Macro Data adiciona contexto macro                            │
│     └─> XGBoost Model captura não-linearidades                           │
│     └─> Neural Network captura padrões complexos                        │
│     └─> CatBoost optimizado para features categóricas                    │
│     └─> Random Forest ensemble de árvores                                │
│     └─> Linear Model baseline simples                                    │
│     └─> Weighted Ensemble combina 8 modelos com meta-learning            │
│         └─> Valuations → valuations table                                 │
│                                                                             │
│  4. SCORING (cada 38 minutos)                                             │
│     └─> Score Discount calcula (30% peso)                                 │
│     └─> Score Location calcula (25% peso)                                  │
│     └─> Score Condition calcula (15% peso)                                │
│     └─> Score Liquidity calcula (15% peso)                                │
│     └─> Score Freshness calcula (15% peso)                                │
│     └─> Red Flags Detector detecta red flags                              │
│     └─> Weighted Score Calculator calcula score total (0-10)              │
│     └─> Rationale Generator gera explicação                               │
│         └─> Scores → scores table                                          │
│                                                                             │
│  5. NOTIFICATION (cada 60 minutos)                                       │
│     └─> Opportunity Selector selecciona top 3-5 listings/dia             │
│     └─> Telegram Bot envia notificações                                    │
│     └─> Notification History rastreia notificações enviadas                │
│                                                                             │
│  6. DASHBOARD (on-demand)                                                  │
│     └─> Streamlit Dashboard exibe dados                                   │
│     └─> Utilizador filtra e explora                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. BENEFÍCIOS ESPERADOS

### 10.1 Benefícios Quantitativos

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                BENEFÍCIOS QUANTITATIVOS ESPERADOS                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  COBERTURA:                                                                 │
│  - Manual: 20-30 listings/dia analisados                                   │
│  - Automatizado: 5000-8000 listings/dia analisados                         │
│  - Melhoria: 167-400x                                                     │
│                                                                             │
│  TEMPO DE ANÁLISE:                                                          │
│  - Manual: 19-32 minutos por listing                                      │
│  - Automatizado: < 1 segundo por listing                                   │
│  - Melhoria: 1140-1920x                                                    │
│                                                                             │
│  TAXA DE SUCESSO OPORTUNIDADES:                                           │
│  - Manual: 30-40% (timing ruim)                                            │
│  - Automatizado: 80-90% (timing óptimo)                                     │
│  - Melhoria: 2-2.5x                                                        │
│                                                                             │
│  PRECISÃO DE AVALIAÇÃO:                                                     │
│  - Manual: ±15-20% (subjetivo)                                            │
│  - Automatizado: ±10% (modelo estatístico)                                │
│  - Melhoria: 1.5-2x                                                         │
│                                                                             │
│  INFORMAÇÃO UTILIZADA:                                                      │
│  - Manual: 20-30% da informação disponível                                │
│  - Automatizado: 100% da informação disponível                            │
│  - Melhoria: 3.3-5x                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Benefícios Qualitativos

**Benefício 1: Consistência**
- Manual: Cada analista usa critérios diferentes
- Automatizado: Critérios consistentes sempre

**Benefício 2: Objectividade**
- Manual: Decisões baseadas em intuição
- Automatizado: Decisões baseadas em dados

**Benefício 3: Escalabilidade**
- Manual: Impossível escalar
- Automatizado: Escalável para 100.000+ listings/dia

**Benefício 4: Privacidade**
- Manual: Dados podem ser partilhados
- Automatizado: Dados locais (GDPR compliance)

**Benefício 5: Custo**
- Manual: Salários de analistas (€50.000-100.000/ano)
- Automatizado: Custo zero (local deployment)

---

## 11. LIMITAÇÕES E RISCOS

### 11.1 Limitações Técnicas

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  LIMITAÇÕES TÉCNICAS                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SCRAPING:                                                                  │
│  - Taxa de sucesso 60-70% (com Nodriver)                                   │
│  - DataDome e Cloudflare evoluem constantemente                            │
│  - Proxies residenciais têm custo (€50/mês)                                │
│                                                                             │
│  DATABASE:                                                                  │
│  - SQLite não escala para > 50.000 listings                                │
│  - Máx 1 writer concorrente                                               │
│  - Solução: Migrar para PostgreSQL quando necessário                       │
│                                                                             │
│  SCHEDULER:                                                                 │
│  - APScheduler: single point of failure                                    │
│  - Solução: Migrar para Celery + RabbitMQ quando necessário                │
│                                                                             │
│  VALUATION:                                                                │
│  - Precisão depende da disponibilidade de dados                            │
│  - Modelos precisam ser re-treinados periodicamente                         │
│  - Solução: Retreinamento mensal                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.2 Riscos

**Risco 1: Anti-bot Evolution**
- DataDome e Cloudflare evoluem constantemente
- Taxa de sucesso scraping pode diminuir
- **Mitigação:** Manter Nodriver actualizado, usar proxies residenciais

**Risco 2: Data Quality**
- Portais podem ter dados incompletos ou incorrectos
- Dados INE podem ter atraso
- **Mitigação:** Validação de dados, múltiplas fontes

**Risco 3: False Positives**
- Sistema pode identificar oportunidades que não são genuínas
- **Mitigação:** Validação manual de top listings, ajuste de thresholds

**Risco 4: Legal/Ethical**
- Scraping pode violar termos de serviço
- **Mitigação:** Respect robots.txt, rate limiting, ethical scraping

---

## 12. PRINCÍPIOS DE DESIGN

### 12.1 Princípios Core

**Princípio 1: Local-First**
- Dados nunca saem do PC
- GDPR compliance por design
- Custo zero de infraestrutura

**Princípio 2: Modularidade**
- Cada camada independente
- Fácil testar e manter
- Fácil substituir componentes

**Princípio 3: Escalabilidade**
- Arquitectura desenhada para escalar
- Fase 1 (MVP) → Fase 4 (Cloud-native)
- Sem rewrites major

**Princípio 4: Observabilidade**
- Logging estruturado
- Health checks
- Métricas e alertas

**Princípio 5: Simplicidade**
- KISS (Keep It Simple, Stupid)
- Ferramentas maduras e estáveis
- Sem over-engineering

---

## 13. DECISÕES TECNOLÓGICAS

### 13.1 Porquê Nodriver (2026)?

**Comparação:**

| Aspecto | Playwright-stealth | Nodriver |
|---|---|---|
| Taxa de Sucesso DataDome | 20-30% | 60-70% |
| Taxa de Sucesso Cloudflare | 30-40% | 70-80% |
| Com Proxies Residenciais | 40-50% | 85-90% |
| WebDriver | Usa chromedriver (patched) | Elimina WebDriver |
| CDP Leaks | Presentes | Ausentes |
| Async Nativo | Sí (com overhead) | Sim (nativo) |
| Manutenção | Baixa | Alta (desenvolvimento activo) |

**Decisão:** Adoptar Nodriver para scraping 2026 (Volume 13)

### 13.2 Porquê SQLite (MVP)?

**Comparação:**

| Aspecto | SQLite | PostgreSQL |
|---|---|---|
| Custo | €0 (local) | €20-50/mês (VPS) |
| Concorrência | 1 writer | Múltiplos writers |
| Escalabilidade | < 50.000 listings | Ilimitado |
| Complexidade | Baixa | Média |
| GDPR Compliance | 100% (local) | Depende de hosting |

**Decisão:** SQLite para MVP, migrar para PostgreSQL quando necessário (Fase 2)

### 13.3 Porquê APScheduler (MVP)?

**Comparação:**

| Aspecto | APScheduler | Celery |
|---|---|---|
| Custo | €0 (local) | €10-30/mês (RabbitMQ) |
| Complexidade | Baixa | Média-Alta |
| Distributed | Não | Sim |
| Escalabilidade | Single process | Multiple workers |

**Decisão:** APScheduler para MVP, migrar para Celery quando necessário (Fase 2)

---

## 14. ROADMAP DE IMPLEMENTAÇÃO

### 14.1 Roadmap por Fases (Volume 13)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              ROADMAP DE IMPLEMENTAÇÃO (4 FASES)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FASE 1: OPTIMIZAÇÃO (Custo: €0/mês)                                      │
│  - Adoptar Nodriver para scraping                                          │
│  - Optimizar SQLite (WAL mode, cache)                                      │
│  - Implementar rate limiting global                                       │
│  - Melhorar logging estruturado                                            │
│  - Timeline: 1-2 semanas                                                  │
│                                                                             │
│  FASE 2: MULTI-INSTANCE (Custo: ~€110/mês)                                 │
│  - Migrar para PostgreSQL                                                   │
│  - Adicionar Redis para cache                                               │
│  - Implementar Celery + RabbitMQ                                           │
│  - Docker containerization                                                  │
│  - Deploy em 2 VPS                                                          │
│  - Timeline: 2-4 semanas                                                  │
│                                                                             │
│  FASE 3: MICROSERVICES (Custo: ~€500/mês)                                  │
│  - Separar em microservices                                                │
│  - Implementar Kubernetes                                                  │
│  - Distributed tracing (OpenTelemetry)                                     │
│  - Circuit breakers (Istio/Linkerd)                                        │
│  - Timeline: 6-8 semanas                                                  │
│                                                                             │
│  FASE 4: CLOUD-NATIVE (Custo: ~€700-900/mês)                               │
│  - Migrar para managed services                                            │
│  - AWS RDS / Azure Database / Cloud SQL                                     │
│  - AWS SQS / Azure Service Bus / Google Pub/Sub                             │
│  - AWS ElastiCache / Azure Cache / Memorystore                              │
│  - Serverless para peak loads (AWS Lambda)                                 │
│  - Timeline: 8-12 semanas                                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 15. ESTADO ATUAL — BASELINE PRODUCTION-READY (2026-04-29)

### 15.1 Ondas 1-5 Concluídas

O sistema atingiu baseline production-ready após a conclusão das Ondas 1-5 de hardening e melhorias:

**Onda 1: ETL Imports Lazy & Ollama Env-Driven**
- Imports lazy no pipeline ETL para evitar carregar torch/transformers desnecessariamente
- Variável `ENRICH_SKIP_HEAVY` para desabilitar enriquecimento pesado (CV/NLP) se desejado
- Ollama env-driven com warm-up, retry, cache e timeouts separados para cada operação
- Extras opcionais no requirements.txt (torch, transformers, opencv) para slim install

**Onda 2: Scripts Cross-Platform & .gitignore**
- Criação de `start.sh` (macOS/Linux) com paridade total ao `start.bat` (Windows)
- 10 comandos: install, doctor, api, ui, dashboard, engine, all, test, help, menu
- Criação de `.gitignore` raiz consolidado (venv312, secrets, logs, scripts/debug, terraform state, modelos LLM)
- Correção da afirmação errada sobre `realestate_engine/tests/` ser placeholder (contém ~305 testes granulares)

**Onda 3: Dark-Mode Fix**
- `.streamlit/config.toml` base alterada para "dark"
- Remoção de cores claras hardcoded em `overview.py` e `scraping_results.py`
- Substituição por variantes dark para melhor contraste e legibilidade

**Onda 4: Scheduler & Notification Hardening**
- APScheduler hardening: `max_instances=1`, `coalesce=True`, `misfire_grace_time`
- Event listeners com logs estruturados `apscheduler.event=`
- `notify_ai_analysis` env-driven (não hardcoda modelo Ollama)
- Fail-closed em `_already_notified_today` (evita spam em outage DB)
- TelegramBot com tratamento de erros específicos (RetryAfter, Forbidden, InvalidToken, BadRequest, TimedOut, NetworkError)

**Onda 5: Documentação Reconciliada**
- Atualização de README.md e realestate_engine/README.md com números reais (12 spiders, 15 views, 53 testes)
- Adição de secção macOS com start.sh, extras opcionais e troubleshooting detalhado
- Remoção de RELATORIO_INCONSISTENCIAS.md (legado)
- Referências ao PRODUCTION_READINESS.md

### 15.2 Estado Atual do Sistema

**Números Reais:**
- 8 portais cobertos por 12 spiders (Idealista, Imovirtual, Casa Sapo, OLX, ERA, REMAX, Century21, Supercasa)
- 15 views Streamlit (Overview, Search, Watchlist, Map View, AI Deals, Market Analysis, Investor Tools, Score Audit, Pipeline Status, Scraping Results, Data Quality, System, Config, Telegram, Debug Logs)
- 53 testes (29 base + 24 production-readiness)
- ~305 testes granulares em `realestate_engine/tests/` (unit/integration)
- 4 modelos de valuation + meta-ensemble (XGBoost, Hedonic, Random Forest, Linear + meta-learner)

**Scripts de Inicialização:**
- `start.bat` (Windows) e `start.sh` (macOS/Linux) com paridade funcional
- Dispatch para 10 comandos: install, doctor, api, ui, dashboard, engine, all, test, help, menu
- Detecção robusta de venv e spawn de terminais

**Documentação:**
- PRODUCTION_READINESS.md: Auditoria completa das Ondas 1-5
- README.md (raiz e realestate_engine/): Instrução de uso cross-platform
- planeamento/21-escala-global-production.md: Roadmap para escala global (proxy rotation, PostgreSQL, cloud LLM, deployment, monitoring, security)

### 15.3 Próximos Passos

Para escalar o sistema de local para global production-grade, ver `planeamento/21-escala-global-production.md`.

Para detalhes completos das Ondas 1-5 e baseline production-ready, ver `PRODUCTION_READINESS.md`.

---

## 16. GLOSSÁRIO DE TERMOS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    GLOSSÁRIO DE TERMOS                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CDP (Chrome DevTools Protocol): Protocolo para comunicar com Chrome       │
│                                                                             │
│  DataDome: Sistema anti-bot usado por Idealista.pt                         │
│                                                                             │
│  Cloudflare Turnstile: Sistema anti-bot usado por Imovirtual              │
│                                                                             │
│  Nodriver: Framework de scraping 2026 (CDP directo)                         │
│                                                                             │
│  Playwright-stealth: Framework de scraping 2024 (obsoleto)                 │
│                                                                             │
│  Residential Proxies: Proxies de IPs reais de residências                   │
│                                                                             │
│  Hedonic Model: Modelo de regressão linear para avaliação imobiliária     │
│                                                                             │
│  Comps Engine: Motor que encontra imóveis comparáveis                     │
│                                                                             │
│  INE: Instituto Nacional de Estatística (Portugal)                         │
│                                                                             │
│  SHAP: Framework para explainability de modelos ML                        │
│                                                                             │
│  XGBoost: Framework de gradient boosting para ML                          │
│                                                                             │
│  OLS (Ordinary Least Squares): Método de regressão linear                  │
│                                                                             │
│  Red Flag: Sinal de aviso que exclui imóvel de "Imperdível"                │
│                                                                             │
│  Discount: Diferença entre valor justo e preço pedido (%)                   │
│                                                                             │
│  Liquidez: Facilidade de vender um imóvel                                  │
│                                                                             │
│  Freguesia: Subdivisão administrativa de Portugal (equivalente a freguesia)│
│                                                                             │
│  POI (Point of Interest): Ponto de interesse (escola, metro, comércio)   │
│                                                                             │
│  GDPR: General Data Protection Regulation (regulamento UE de dados)         │
│                                                                             │
│  Local-First: Arquitectura onde dados ficam localmente (no PC)            │
│                                                                             │
│  ETL: Extract, Transform, Load (pipeline de dados)                         │
│                                                                             │
│  Ensemble: Combinação de múltiplos modelos para melhor precisão            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*Fim do Documento 01 — Visão Geral*
