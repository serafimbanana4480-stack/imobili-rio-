# Entry Points — Real Estate Engine

Este documento descreve os diferentes entry points disponíveis no projeto.

## 📋 Entry Points Disponíveis

### 1. main.py
**Localização:** `realestate_engine/main.py`  
**Propósito:** Entry point principal de produção com inicialização completa

**Funcionalidade:**
- Inicializa sistema (logging, database, metrics server)
- Inicia o scheduler com o orchestrator
- Inicia servidor de métricas Prometheus (se disponível)
- Executa em foreground (Ctrl+C para parar)

**Uso:**
```bash
python -m realestate_engine.main
# ou
python realestate_engine/main.py
```

**Quando usar:**
- Produção com monitorização completa
- Necessário servidor de métricas
- Inicialização completa do sistema

### 2. main_engine.py
**Localização:** `realestate_engine/main_engine.py`  
**Propósito:** Entry point simplificado para desenvolvimento

**Funcionalidade:**
- Configura logging (engine.log, errors.log)
- Executa ciclo inicial de boot no arranque
- Inicia o scheduler 24/7
- Sem servidor de métricas
- Logging mais detalhado para debug

**Uso:**
```bash
python -m realestate_engine.main_engine
# ou
python realestate_engine/main_engine.py
```

**Quando usar:**
- Desenvolvimento e testes
- Debug com logging detalhado
- Boot inicial automático (sem espera pelo scheduler)
- Sem necessidade de métricas Prometheus

### 3. api/main.py
**Localização:** `realestate_engine/api/main.py`  
**Propósito:** Entry point da API FastAPI

**Funcionalidade:**
- Inicializa FastAPI application
- Configura CORS, rate limiting
- Inicializa database
- Expose endpoints REST
- Executa com Uvicorn

**Uso:**
```bash
python -m realestate_engine.api.main
# ou
uvicorn realestate_engine.api.main:app --host 0.0.0.0 --port 8000
```

**Quando usar:**
- Apenas API (sem dashboard)
- Integração com outros sistemas
- Testes de API

### 4. dashboard/app.py
**Localização:** `realestate_engine/dashboard/app.py`  
**Propósito:** Entry point do dashboard Streamlit

**Funcionalidade:**
- Inicializa Streamlit application
- Carrega views lazy-loaded
- Expose interface visual

**Uso:**
```bash
streamlit run realestate_engine/dashboard/app.py
```

**Quando usar:**
- Apenas dashboard (sem API)
- Visualização de dados
- Interação com utilizadores

### 5. start.bat / start.sh
**Localização:** Raiz do projeto  
**Propósito:** Launcher unificado para Windows/macOS/Linux

**Comandos disponíveis:**
```bash
start.bat install      # Setup inicial
start.bat doctor       # Verifica ambiente
start.bat dashboard    # Abre dashboard + API
start.bat engine       # Pipeline 24h autónomo
start.bat api          # Só a API
start.bat ui           # Só a dashboard
start.bat test         # Suite pytest
```

**Quando usar:**
- Uso diário recomendado
- Inicialização padronizada
- Ambientes Windows/macOS/Linux

## 🔄 Diferenças Entre main.py e main_engine.py

| Característica | main.py | main_engine.py |
|----------------|---------|----------------|
| **Propósito** | Produção | Desenvolvimento |
| **Logging** | Padrão (loguru) | Detalhado (engine.log, errors.log) |
| **Metrics Server** | ✅ Sim | ❌ Não |
| **Boot Cycle** | ❌ Não | ✅ Sim (executa pipeline no boot) |
| **Inicialização** | Completa | Simplificada |
| **Uso recomendado** | Produção | Dev/Test |

## 📝 Decisão de Manutenção

**Decisão:** Manter ambos os ficheiros separados

**Justificação:**
1. Servem propósitos diferentes (produção vs desenvolvimento)
2. main_engine.py tem boot cycle automático útil para testes
3. main.py tem métricas necessárias para produção
4. Diferentes níveis de logging para diferentes cenários
5. Consolidar complicaria a lógica condicional

**Melhorias futuras (opcionais):**
- Renomear para mais descritivo:
  - `main.py` → `orchestrator_cli.py` ou `production_entry.py`
  - `main_engine.py` → `dev_entry.py` ou `scheduler_daemon.py`
- Adicionar argumentos de linha de comando para selecionar modo
- Criar um entry point unificado com flags

## 🚀 Recomendação de Uso

### Para Produção
```bash
# Usar start.bat (recomendado)
start.bat dashboard

# Ou main.py direto
python -m realestate_engine.main
```

### Para Desenvolvimento
```bash
# Usar main_engine.py para debug rápido
python -m realestate_engine.main_engine

# Ou start.bat
start.bat engine
```

### Para Testes
```bash
# Usar pytest diretamente
pytest tests/ -v

# Ou start.bat
start.bat test
```

---

**Última atualização:** 2026-05-05  
**Versão:** 1.0
