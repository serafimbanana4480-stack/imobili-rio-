# Guia de Instalação — Real Estate Opportunity Engine

Este documento descreve como configurar e executar o sistema no seu computador Windows 11.

## 1. Pré-requisitos
- **Python 3.12+**: Baixe e instale do site oficial [python.org](https://python.org). Certifique-se de marcar a opção "Add Python to PATH" durante a instalação.
- **Git** (Opcional): Para clonar o repositório.

## 2. Instalação Automática (Recomendado)
1. Abra a pasta do projeto.
2. Dê um clique duplo no arquivo `install_windows.bat`.
3. O script irá:
   - Criar as pastas necessárias (`data/`, `logs/`, etc.).
   - Instalar todas as dependências do Python.
   - Inicializar a base de dados SQLite.
   - Configurar o motor para iniciar automaticamente ao ligar o PC (via Windows Task Scheduler).

## 3. Configuração do Telegram
1. Obtenha um Token de Bot conversando com o [@BotFather](https://t.me/botfather).
2. Obtenha seu Chat ID conversando com o [@userinfobot](https://t.me/userinfobot).
3. Abra o arquivo `realestate_engine/.env` com o Bloco de Notas.
4. Preencha os campos `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID`.

## 4. Como Executar
- **Motor (Background)**: Execute o arquivo `start_system.bat`. Ele ficará monitorando os portais a cada 30 minutos.
- **Interface (Dashboard)**: Execute o arquivo `start_dashboard.bat`. Uma aba abrirá no seu navegador no endereço `http://localhost:8501`.

## 5. Manutenção
- Os logs do sistema podem ser encontrados em `data/logs/`.
- A base de dados local está em `data/db/realestate.db`.
- O sistema limpa automaticamente dados antigos a cada 7 dias.

---
© 2026 Real Estate Opportunity Engine. Operação local e gratuita.
