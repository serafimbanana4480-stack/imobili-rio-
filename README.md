# 🏠 Real Estate Opportunity Engine — Grande Porto

> **Motor autónomo de análise do mercado imobiliário português** — Scraping multi-portal, valuation, scoring de oportunidades, notificações Telegram e tese de investimento por LLM local (Ollama).

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-📊-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](Dockerfile)

---

## 🎯 Visão Geral

O **Real Estate Opportunity Engine** é um sistema automatizado que:

1. **Rastreia** milhares de imóveis no Grande Porto (Idealista, Imovirtual, CustoJusto)
2. **Avalia** o preço justo usando Machine Learning (ensemble de modelos)
3. **Deteta** oportunidades de investimento (bargains, below-market)
4. **Pontua** as melhores oportunidades (opportunity score)
5. **Notifica** via Telegram quando encontra uma "peek deal"
6. **Gera** tese de investimento com LLM local (Ollama)

---

## ✨ Funcionalidades Principais

| Funcionalidade | Descrição | Estado |
|----------------|-------------|--------|
| **Multi-Portal Scraping** | Idealisto, Imovirtual, CustoJusto (Playwright) | ✅ Ativo |
| **ML Valuation** | Ensemble (XGBoost + LightGBM + CatBoost) | ✅ Ativo (R²=0.72) |
| **Opportunity Scoring** | Algoritmo que cruza preço previsto vs. preço anúncio | ✅ Ativo |
| **Telegram Bot** | Notificações em tempo real | ✅ Ativo |
| **Dashboard Streamlit** | Interface web com filtros, mapa, gráficos | ✅ Ativo (localhost:8501) |
| **LLM Investment Thesis** | Ollama local gera tese de investimento | ✅ Ativo |
| **PostgreSQL** | Base de dados robusta (SQLite opcional) | ✅ Ativo |
| **Docker Ready** | Deploy completo com Docker Compose | ✅ Ativo |

---

## 🏗️ Arquitetura

```
realestate_engine/
├── scrapers/             # Módulos de scraping
│   ├── idealisto_scraper.py
│   ├── imovirtual_scraper.py
│   └── custojusto_scraper.py
├── valuation/            # Avaliação ML
│   ├── train_model.py
│   ├── predict.py
│   └── ensemble.py
├── scoring/             # Opportunity scoring
│   ├── scorer.py
│   └── features.py
├── notification/         # Notificações Telegram
│   └── telegram_bot.py
├── dashboard/            # Streamlit dashboard
│   └── app.py
├── llm/                  # LLM local (Ollama)
│   └── investment_thesis.py
├── database/             # Camada de base de dados
│   ├── models.py
│   └── db.py
├── api/                  # FastAPI REST API
│   └── main.py
├── docker/              # Configurações Docker
├── data/                 # Diretório de dados
├── models/               # Modelos ML treinados
├── logs/                 # Ficheiros de log
├── .env.example          # Template de ambiente
├── start.bat            # Windows startup
├── start.sh             # Linux/macOS startup
└── README.md            # Este ficheiro
```

---

## 🚀 Quick Start

### Opção 1: Docker (Recomendado)

```bash
# 1. Clonar o repositório
git clone https://github.com/serafimbanana4480-stack/imobili-rio-.git
cd imobili-rio-

# 2. Configurar ambiente
cp .env.example .env
# Editar .env com as tuas configurações

# 3. Iniciar com Docker Compose
docker-compose up -d

# 4. Aceder ao dashboard
http://localhost:8501
```

### Opção 2: Instalação Local (Windows)

```powershell
# 1. Setup inicial (venv + dependências + DB)
.\start.bat install

# 2. Verificar ambiente
.\start.bat doctor

# 3. Abrir dashboard + API
.\start.bat dashboard
```

### Opção 3: Instalação Local (Linux/macOS)

```bash
# 1. Tornar executável
chmod +x start.sh

# 2. Setup inicial (venv312 + deps + DB)
./start.sh install

# 3. Verificar ambiente
./start.sh doctor

# 4. Abrir dashboard + API
./start.sh dashboard
```

---

## 📖 Guia de Uso

### 1. Scraping de Imóveis

```bash
# Grande Porto, apartamentos, máximo 100 anúncios
python main.py scrape --district "Grande Porto" --property-type apartamento --max-listings 100

# Múltiplos portais
python main.py scrape --source idealista,imovirtual --district "Porto"

# Com debug
python main.py scrape --district "Porto" --debug
```

### 2. Treino do Modelo ML

```bash
# Treino completo (apaga modelo anterior)
python main.py train --force

# Treino incremental (usa novos dados)
python main.py train --incremental
```

**Métricas do Modelo Atual:**
- **R²:** 0.72 (expllica 72% da variação de preço)
- **MAE:** €12,450 (erro médio absoluto)
- **Features:** 18 (área, quartos, casas de banho, ano, localização, etc.)

### 3. Avaliação de Imóveis

```bash
# Avaliar um imóvel específico
python main.py valuate --listing-id 12345

# Avaliar todos os novos imóveis
python main.py valuate --batch-size 100
```

### 4. Descoberta de Oportunidades

```bash
# Encontrar as 20 melhores oportunidades (desconto > 15%)
python main.py find-opportunities --limit 20 --min-discount 15

# Critérios:
# - opportunity_score ≥ 7.0
# - Diferença preço_previsto - preço_anúncio > 15%
# - LLM (se disponível): "Approved"
```

### 5. Dashboard Streamlit

Aceder a `http://localhost:8501` após iniciar o dashboard:

- **Visão Geral:** Métricas principais, gráfico de preços
- **Lista de Imóveis:** Tabela filtrável e ordenável
- **Mapa:** Localização geográfica (Folium)
- **Top Oportunidades:** As melhores oportunidades (LLM analisada)
- **Analytics:** Histórico de preços, tendências de mercado
- **Export:** Descarregar resultados em CSV

### 6. Notificações Telegram

Configurar no `.env`:

```bash
TELEGRAM_BOT_TOKEN=teu_token_aqui
TELEGRAM_CHAT_ID=teu_chat_id
```

O bot enviará mensagens quando:
- Nova oportunidade com score > 8.0
- Imóvel com desconto > 20%
- Tese de investimento gerada (LLM)

---

## 🤖 Funcionalidades de LLM (Ollama Local)

### Investment Thesis Generation

O sistema usa Ollama (LLM local) para gerar tese de investimento:

- ✅ **Análise de localização** (proximidade a transportes, escolas, serviços)
- ✅ **Potencial de valorização** (planos urbanísticos, tendências)
- ✅ **Risco de investimento** (estado do imóvel, mercado)
- ✅ **Recomendação final** (Buy/Rent/Hold)

**Exemplo:**
```
Tese de Investimento Gerada (Ollama):
"Este imóvel no Bonfim (Porto) apresenta um desconto de 18% 
relativamente ao mercado. A localização é excelente (próximo ao metro, 
escolas e comércio). O estado de conservação é bom. Recomendo 
como oportunidade de investimento para arrendamento (yield estimado: 5.2%)."
```

---

## ⚙️ Configuração

### Ficheiro `.env`

| Variável | Descrição | Defeito |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | SQLite (realestate.db) |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot token | - |
| `TELEGRAM_CHAT_ID` | Telegram Chat ID | - |
| `OLLAMA_URL` | URL da API Ollama | `http://localhost:11434` |
| `SCRAPING_INTERVAL_HOURS` | Frequência de scraping | `6` |
| `OPPORTUNITY_SCORE_THRESHOLD` | Pontuação mínima | `7.0` |
| `MIN_DISCOUNT_PERCENTAGE` | Desconto mínimo | `15` |

---

## 📊 Scheduler Autónomo

O scheduler executa tarefas automáticas:

| Tarefa | Frequência | Descrição |
|--------|------------|-------------|
| Scraping diário | Configurável (6h) | Descarregar novos anúncios |
| Avaliação periódica | Configurável (12h) | Avaliar imóveis novos |
| Descoberta de oportunidades | Configurável (24h) | Executar opportunity finder |
| Envio de notificações | Após cada descoberta | Alertar sobre top deals |

```bash
# Iniciar scheduler (contínuo)
python main.py scheduler
```

---

## 🌐 Deploy

### Railway

1. Conectar repositório GitHub ao Railway
2. Adicionar variáveis de ambiente
3. Fazer deploy

### Render

1. Fazer push do código para GitHub
2. Criar novo Web Service no Render
3. Configurar variáveis de ambiente
4. Fazer deploy

### VPS (Linux)

```bash
# 1. SSH para o servidor
ssh user@server-ip

# 2. Clonar repositório
git clone https://github.com/serafimbanana4480-stack/imobili-rio-.git

# 3. Configurar `.env`
nano .env

# 4. Iniciar com Docker Compose
docker-compose up -d

# 5. Verificar logs
docker-compose logs -f
```

---

## 📂 Estrutura do Projeto

```
imobili-rio-/
├── main.py                 # Ponto de entrada
├── config.py              # Configuração
├── requirements.txt       # Dependências
├── .env.example          # Template de ambiente
├── start.bat            # Windows startup script
├── start.sh             # Linux/macOS startup script
├── scrapers/             # Módulos de scraping
├── valuation/            # Avaliação ML
├── scoring/             # Opportunity scoring
├── notification/         # Notificações Telegram
├── dashboard/            # Dashboard Streamlit
├── llm/                  # LLM local (Ollama)
├── database/             # Camada de base de dados
├── api/                  # FastAPI REST API
├── docker/              # Configurações Docker
├── data/                 # Diretório de dados
├── models/               # Modelos ML
├── logs/                 # Ficheiros de log
├── exports/              # Ficheiros exportados
├── Dockerfile            # Imagem Docker
├── docker-compose.yml    # Config Docker Compose
└── README.md            # Este ficheiro
```

---

## 🔍 Troubleshooting

### Problemas de Conexão à Base de Dados

Verificar se PostgreSQL está a correr:

```bash
docker-compose ps postgres
```

### Erros de Scraping

- Verificar conexão à internet
- Confirmar que os websites estão acessíveis
- Ajustar delays na configuração se houver rate-limiting

### Falha no Treino do Modelo

Garantir dados suficientes:

```bash
python main.py scrape --max-listings 200
```

### Funcionalidades de LLM Não Funcionam

- Verificar se Ollama está a correr: `curl http://localhost:11434/api/version`
- Confirmar que o modelo está instalado: `ollama list`
- Rever logs em `logs/realestate.log`

---

## 📝 Licença

Este projeto é para fins **educacionais e uso pessoal**. Respeitar os termos de serviço dos websites ao fazer scraping.

---

## 🤝 Contribuições

Contribuições são bem-vindas! Por favor:

1. Fazer fork do repositório
2. Criar uma branch de funcionalidade
3. Fazer as tuas alterações
4. Submeter um Pull Request

---

## 📞 Suporte

Para problemas e questões:

- Consultar a seção de troubleshooting
- Rever logs em `logs/realestate.log`
- Abrir uma issue no GitHub

---

## 🙏 Agradecimentos

- **Idealista Scraper:** https://github.com/.../idealista-scraper
- **Imovirtual Scraper:** https://github.com/.../imovirtual-scraper
- **Playwright:** https://playwright.dev
- **XGBoost:** https://xgboost.readthedocs.io
- **Streamlit:** https://streamlit.io
- **Ollama:** https://ollama.ai/

---

## 📈 Estatísticas do Projeto

- **Última atualização:** 2026-06-28
- **Branch:** `main`
- **Total de ficheiros:** ~150 (código fonte)
- **Módulos Python:** 30+
- **Cobertura de testes:** 80%+
- **Modelo ML:** Ensemble (R²=0.72, MAE=€12,450)

---

**Feito com ❤️ em Portugal** 🇵🇹🇵🇬
