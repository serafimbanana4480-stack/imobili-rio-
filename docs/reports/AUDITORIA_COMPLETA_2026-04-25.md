# Auditoria Completa - Real Estate Engine
## 2026-04-25

---

## 1. Resumo Executivo

| Componente | Estado | Notas |
|---|---|---|
| **Imovirtual Spider** | Funcional | 1375 listings, direct HTTP, __NEXT_DATA__ JSON |
| **ETL Pipeline** | Funcional | Normaliza, dedup, geocode, enrich, validate, load |
| **Valuation Engine** | Funcional | XGBoost + Hedonic + Comps, 1375/1375 avaliados |
| **Scoring Engine** | Funcional | 10 Excelente, 116 Bom, 1249 restantes |
| **Dashboard** | Funcional | 13/13 views carregam, Streamlit OK |
| **Scheduler** | Funcional | 24/7, circuit breakers, night silence |
| **Outros Spiders** | Parcial | Casa Sapo direct (JSON-LD) pronto mas nao integrado; resto precisa nodriver+proxies |
| **Geocoordenadas** | Limitado | 8% coverage - Imovirtual redacta; Casa Sapo tem coords |
| **Fotos** | OK | 98% listings com URLs de fotos; CV analysis skipped (heavy) |
| **NLP/IA** | OK | Rule-based funciona; BERT base corrigido para nao carregar pesos aleatorios |

**Veredicto: 75% funcional para producao.** Faltam: integrar Casa Sapo/REMAX direct, melhorar geocoding, adicionar mais regioes.

---

## 2. Database Schema - Cobertura de Campos

### CleanListing (3012 total apos varias corridas)

| Campo | Cobertura | Nota |
|---|---|---|
| preco_pedido | 100% | Extraido de todos os spiders |
| area_util_m2 | 100% | Extraido de todos os spiders |
| quartos | 100% | Extraido de todos os spiders |
| source_url | 100% | Todos tem URL |
| fotos_urls | 100% | Todos tem (array, pode estar vazio) |
| num_fotos | 68% | 2041/3012 com fotos > 0 |
| freguesia | ~100% | Imovirtual extrai bem |
| concelho | ~100% | |
| distrito | ~100% | Porto 684, Lisboa 690, Santarem 1 |
| lat/lon | 8% | Imovirtual redacta por privacidade |
| cert_energetico | Baixa | Nao extraido do __NEXT_DATA__ |
| ano_construcao | Baixa | Nao extraido do __NEXT_DATA__ |
| image_quality_score | 0% | Heavy enrichment skipped |
| image_phash | 0% | Heavy enrichment skipped |
| bert_sentiment_score | 0% | Heavy enrichment skipped |
| extracted_entities | 0% | Heavy enrichment skipped |
| description_summary | 0% | Heavy enrichment skipped |
| detected_rooms | 0% | Heavy enrichment skipped |
| tem_garagem, tem_piscina, etc. | ~100% | Rule-based do enricher (cheap) |

### Problema Schema: Amenities nao persistem!

O `enricher.enrich_amenities()` adiciona `tem_garagem`, `tem_piscina`, `tem_vista_mar`, etc. mas estes campos **NAO existem no schema CleanListing**! Sao descartados na pipeline ETL porque o `pipeline_etl.py` so carrega campos definidos no modelo ORM.

**Impacto:** O scoring engine pode usar estas flags (se o scoring engine as ler do dict), mas elas nao ficam guardadas na DB.

---

## 3. Spiders - Estado Detalhado

### Funcionais (Direct HTTP, sem browser)

| Spider | Tecnica | Fotos | Coords | Estado |
|---|---|---|---|---|
| **ImovirtualNextDataSpider** | __NEXT_DATA__ JSON | Sim | Nao (redacted) | **PRODUCAO** |
| **CasaSapoDirectSpider** | JSON-LD schema.org | Sim | **SIM** | Pronto, nao integrado |
| **REMAXDirectSpider** | Sitemap + JSON-LD | Sim | ? | Pronto, nao integrado |

### Necessitam Nodriver (Chrome) + Proxies

| Spider | Problema |
|---|---|
| IdealistaSpider | Anti-bot agressivo, 403/429 |
| CasaSapoSpider (nodriver) | Rate-limits, 429s |
| ERASpider | SPA render, selectors frageis |
| REMAXSpider (nodriver) | SPA render |
| SuperCasaSpider | DOM-based, frageis |
| Century21Spider | DOM-based, frageis |
| OLXSpider | Anti-bot, CAPTCHAs |

---

## 4. NLP / IA - Estado

| Componente | Estado | Nota |
|---|---|---|
| **Sentiment Analyzer** | Corrigido | Usa rule-based (keywords PT); BERT base nao carrega mais pesos aleatorios |
| **NER Extractor** | Corrigido | Usa rule-based (regex patterns); BERT base nao carrega mais pesos aleatorios |
| **Summarizer** | Fallback OK | T5 quebra (spiece.model no Py3.14); extractive summary funciona |
| **BERT Embeddings** | Funcional | Para similarity, nao para classification |
| **spaCy** | Quebrado (Py3.14) | Usa rule-based NLP Portuguese como fallback |
| **Image Quality CV** | Skipped | Precisa download de imagens + OpenCV; skipped por ENRICH_SKIP_HEAVY |

### Modelos Fine-tuned Disponiveis (para upgrade futuro)

- Sentimento: `cardiffnlp/twitter-xlm-roberta-base-sentiment` (multilingue, funciona PT)
- NER PT: `pierreguillou/ner-bert-base-cased-pt-lenerbr`
- Summarization: `facebook/bart-large-cnn` (ingles, precisa fine-tuning PT)

---

## 5. Fotos - Estado

| Aspecto | Estado |
|---|---|
| URLs de fotos | 98% dos listings tem (Imovirtual fornece array `images`) |
| Thumbnails no dashboard | Funcionam (URLs sao publicas) |
| Download local | Nao implementado |
| Analise CV (blur, brightness, quality) | Skipped (ENRICH_SKIP_HEAVY=1) |
| Perceptual hash (dedup por imagem) | Skipped |
| Room detection (contar quartos por foto) | Skipped |

---

## 6. Geocoding - Estado

| Aspecto | Estado |
|---|---|
| Nominatim geocoder | Funciona com circuit breaker |
| Cache (SQLite + Redis) | Funciona |
| Coverage atual | 8% (Imovirtual nao fornece coords) |
| Casa Sapo Direct | **Fornece lat/lon no JSON-LD** - nao integrado |
| REMAX Direct | Sitemap-based, coords desconhecidas |
| Custo API | Nominatim = gratis (rate limit); Google Maps = pago |

---

## 7. O que Falta para 100% Funcional

### Prioridade 1 (Bloco para Producao)

1. **Integrar CasaSapoDirectSpider no SpiderManager** - Duplicar coverage, geocoordenadas!
2. **Integrar REMAXDirectSpider no SpiderManager** - Terceira fonte de dados
3. **Adicionar campos de amenities ao schema CleanListing** - `tem_garagem`, `tem_piscina`, etc.
4. **Adicionar mais regioes** - Braga, Aveiro, Coimbra, Faro, Setubal, Leiria

### Prioridade 2 (Melhorias)

5. **Melhorar extracao de certificado energetico** - Regex mais robusta ou detail page
6. **Melhorar extracao de ano de construcao** - Regex mais robusta ou detail page
7. **Batch geocoding** - Usar Nominatim bulk ou Google Maps API para todos os listings
8. **Testar nodriver spiders com proxies** - Idealista, ERA, etc.

### Prioridade 3 (Opcional)

9. **Python 3.12 environment** - Para heavy NLP (spaCy, BERT fine-tuned, CV)
10. **Image download + CV analysis** - Se necessario para scoring (impacto limitado)
11. **Fine-tuned sentiment model** - Se rule-based nao for suficiente

---

## 8. Recomendacao Final

**O projeto ja esta funcional para venda/demonstracao.** O pipeline end-to-end funciona: scrape -> ETL -> valuation -> scoring -> dashboard. Com 1375+ listings, o dashboard mostra dados reais e oportunidades de investimento.

**Para tornar 100% funcional, implementar Prioridade 1 (4 items):**
- Casa Sapo direct spider integrado -> +1000 listings, +coords
- REMAX direct spider integrado -> +500 listings
- Amenities no schema -> scoring mais preciso
- Mais regioes -> cobertura nacional

**Estimativa: 2-3 horas de trabalho para Prioridade 1.**
