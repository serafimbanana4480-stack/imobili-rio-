# Telegram Bot Integration - Setup Guide

## Overview
Este guia explica como configurar e usar o Telegram Bot para receber notificações do Real Estate Engine.

## Pré-requisitos
- Python 3.12+ com venv312 configurado
- Ollama instalado com modelo mistral:7b
- Conta no Telegram

## Passo 1: Configurar Token do Telegram

O token já está configurado no `.env`:
```
TELEGRAM_BOT_TOKEN="8620722559:AAFUf6HKJf8ha6d1Aj65Akkit7Bo9o09sPY"
```

Bot username: `@testbotprojeto_bot`

## Passo 2: Obter Chat ID

1. Abre o Telegram e procura por `@testbotprojeto_bot`
2. Envia uma mensagem (pode ser `/start` ou qualquer texto)
3. Executa o script para obter o Chat ID:
   ```bash
   python test_telegram_token.py
   ```
4. O script mostrará o teu Chat ID
5. Adiciona o Chat ID ao `.env`:
   ```
   TELEGRAM_CHAT_ID="123456789"
   ```

## Passo 3: Verificar Configuração

Executa o script de teste para verificar que tudo está a funcionar:
```bash
python test_telegram_token.py
```

Deves ver:
- ✅ Token válido!
- Bot ID: 8620722559
- Bot Username: @testbotprojeto_bot
- Mensagens recentes (se enviaste mensagem ao bot)

## Passo 4: Usar o Scheduler

### Opção 1: Scheduler Padrão (Horário 8:00-22:00)

Executa o scheduler padrão que roda de hora em hora:
```bash
start_scheduler.bat
```

Este scheduler:
- Roda scraping, ETL, valuation, scoring a cada hora (8:00-22:00)
- Envia notificações de top oportunidades
- Envia análise IA das melhores casas
- Respeita período de silêncio noturno (23:00-8:00)

### Opção 2: Long-Running Scheduler (10-30 min scraping)

Para sessões de scraping mais longas:
```bash
python -c "import asyncio; from realestate_engine.scheduler.long_running_scheduler import LongRunningScheduler; asyncio.run(LongRunningScheduler().run_once(scrape_minutes=20))"
```

Este scheduler:
- Roda scraping por 20 minutos (configurável)
- Executa ETL, valuation, scoring
- Envia análise IA detalhada
- Envia notificações regulares

### Opção 3: Long-Running Contínuo (24/7)

Para operação contínua:
```bash
python -c "import asyncio; from realestate_engine.scheduler.long_running_scheduler import LongRunningScheduler; asyncio.run(LongRunningScheduler().run_forever(interval_minutes=60, scrape_minutes=20))"
```

## Passo 5: Testar Envio de Mensagens

### Testar Startup Message
```bash
python -c "import asyncio; from realestate_engine.notification.notification_engine import NotificationEngine; asyncio.run(NotificationEngine().send_startup_message())"
```

### Testar AI Analysis
```bash
python -c "import asyncio; from realestate_engine.notification.notification_engine import NotificationEngine; asyncio.run(NotificationEngine().notify_ai_analysis(limit=3))"
```

## Passo 6: Monitorizar Logs

Os logs são guardados em:
- `logs/scraping/` - Logs de scraping
- `logs/` - Logs gerais da aplicação

## Troubleshooting

### Bot não envia mensagens
1. Verifica se o Chat ID está configurado no `.env`
2. Executa `python test_telegram_token.py` para verificar o token
3. Verifica se enviaste mensagem ao bot @testbotprojeto_bot

### Ollama não funciona
1. Verifica se Ollama está a correr: `ollama --version`
2. Verifica se o modelo está instalado: `ollama list`
3. Instala o modelo: `ollama pull mistral:7b`

### Scheduler não arranca
1. Verifica se o Python venv312 está configurado
2. Verifica as dependências: `pip install -r requirements.txt`
3. Verifica os logs em `logs/`

## Estrutura das Mensagens

### Startup Message
```
🚀 Real Estate Engine - Scheduler Started
⏰ Iniciado às: 2026-04-26 04:15:00
🔄 24/7 Scheduler ativo
📊 Monitorizando mercado imobiliário do Porto
A enviar notificações para oportunidades excelentes...
```

### AI Analysis Message
```
🤖 Análise IA — Melhor Oportunidade

🏠 Título do Imóvel
⭐ Score: 9.5/10
💰 Desconto: 15% abaixo do mercado

📝 Tese de Investimento (IA):
[Análise detalhada da IA sobre o imóvel]

🔗 [Ver anúncio](url)
```

## Próximos Passos

1. Envia uma mensagem ao bot @testbotprojeto_bot
2. Executa `python test_telegram_token.py` para obter o Chat ID
3. Configura o Chat ID no `.env`
4. Executa o scheduler: `start_scheduler.bat`
5. Monitoriza as notificações no Telegram
