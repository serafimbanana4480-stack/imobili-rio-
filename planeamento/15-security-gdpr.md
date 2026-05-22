# SECURITY E GDPR — REAL ESTATE OPPORTUNITY ENGINE
## Segurança, Proteção de Dados e Compliance com GDPR

> **Este documento:** Especificação completa de security e GDPR  
> **Objectivo:** Fornecer especificação detalhada de security para IA implementar  
> **Linhas:** 1500+ linhas de documentação detalhada  
> **Versão:** 5.0 (Actualizado com Volume 13)

---

## ÍNDICE

1. [Introdução à Security](#1-introducao-a-security)
2. [Arquitectura de Security](#2-arquitetura-de-security)
3. [GDPR Compliance](#3-gdpr-compliance)
4. [Data Protection](#4-data-protection)
5. [Secrets Management](#5-secrets-management)
6. [Authentication e Authorization](#6-authentication-e-authorization)
7. [Input Validation](#7-input-validation)
8. [SQL Injection Prevention](#8-sql-injection-prevention)
9. [XSS Prevention](#9-xss-prevention)
10. [Rate Limiting](#10-rate-limiting)
11. [Logging Security](#11-logging-security)
12. [Network Security](#12-network-security)
13. [Ethical Scraping](#13-ethical-scraping)
14. [Security Audit](#14-security-audit)
15. [Glossário de Security](#15-glossario-de-security)

---

## 1. INTRODUÇÃO À SECURITY

### 1.1 Objectivo da Security

**Security** é o conjunto de práticas para proteger o sistema e os dados:
- Proteger dados pessoais (GDPR compliance)
- Prevenir acessos não autorizados
- Prevenir ataques (SQL injection, XSS, etc.)
- Proteger secrets (tokens, passwords)
- Ethical scraping (respeitar termos de serviço)

**Objectivo:** Garantir que o sistema é seguro e compliant com GDPR, dado que opera localmente com dados pessoais.

### 1.2 Porquê Security?

**Riscos sem Security:**
- Dados pessoais podem ser expostos
- Tokens podem ser roubados
- Sistema pode ser vulnerável a ataques
- Violação de GDPR (multas até €20M ou 4% faturação)
- Perda de confiança dos utilizadores

**Solução com Security:**
- Dados encriptados em repouso
- Secrets protegidos (encriptação, environment variables)
- Input validation para prevenir ataques
- Rate limiting para prevenir abuso
- Ethical scraping (respeitar robots.txt, rate limits)

---

## 2. ARQUITECTURA DE SECURITY

### 2.1 Arquitectura de Security

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              ARQUITECTURA DE SECURITY (LOCAL-FIRST)                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DATA PROTECTION                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Database encriptado (Fernet)                                     │   │
│  │ - Secrets encriptados (Fernet)                                     │   │
│  │ - Logs sem dados pessoais                                          │   │
│  │ - Backup encriptado                                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  SECRETS MANAGEMENT                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Environment variables (.env)                                      │   │
│  │ - Encriptação de secrets (Fernet)                                  │   │
│  │ - .env no .gitignore                                               │   │
│  │ - Chave de encriptação separada                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  INPUT VALIDATION                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Validar todos os inputs (preço, área, quartos, etc.)          │   │
│  │ - Sanitizar strings (remover HTML, SQL injection)                  │   │
│  │ - Validar ranges (preço > 0, área > 0, quartos ≥ 0)                 │   │
│  │ - Validar tipos (float para preço, int para quartos)                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  AUTHORIZATION                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Dashboard sem autenticação (local deployment)                   │   │
│  │ - Telegram bot com autenticação (token)                            │   │
│  │ - API endpoints (se expostos) com autenticação                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  RATE LIMITING                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Rate limiting por portal (1 request/15 segundos)                 │   │
│  │ - Rate limiting por dashboard (1 request/segundo)                    │   │
│  │ - Rate limiting por Telegram (5 notificações/dia)                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  LOGGING SECURITY                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Logs sem dados pessoais (sem nomes, moradas, contactos)       │   │
│  │ - Logs estruturados (JSON)                                         │   │
│  │ - Log rotation (30 dias)                                             │   │
│  │ - Logs encriptados (opcional, para produção)                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  ETHICAL SCRAPING                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Respeitar robots.txt                                              │   │
│  │ - Respeitar rate limits                                              │   │
│  │ - Não sobrecarregar servidores                                       │   │
│  │ - Respeitar termos de serviço                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. GDPR COMPLIANCE

### 3.1 O Que é GDPR?

**GDPR** (General Data Protection Regulation) é o regulamento europeu de proteção de dados pessoais, aplicável desde 25 Maio 2018.

**Princípios Fundamentais:**
1. **Lawfulness, Fairness, Transparency:** Dados processados legalmente, de forma transparente
2. **Purpose Limitation:** Dados só podem ser usados para propósito especificado
3. **Data Minimization:** Apenas dados necessários para o propósito
4. **Accuracy:** Dados devem ser exactos e actualizados
5. **Storage Limitation:** Dados guardados apenas pelo tempo necessário
6. **Integrity and Confidentiality:** Dados protegidos de forma segura
7. **Accountability:** Responsável por compliance

### 3.2 GDPR no Contexto do Projecto

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              GDPR NO CONTEXTO DO PROJECTO                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DADOS PESSOAIS:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Nome do proprietário (se disponível)                               │   │
│  │ - Morada completa (rua, número, freguesia)                           │   │
│  │ - Contacto (telefone, email) - se disponível                         │   │
│  │ - Dados de agência (nome, contacto) - se disponível                   │   │
│  │                                                                     │   │
│  │ NOTA: O sistema NÃO guarda dados pessoais intencionalmente.       │   │
│  │ Apenas dados públicos dos portais imobiliários.                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DADOS NÃO PESSOAIS:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Preço, área, quartos                                               │   │
│  │ - Estado, ano construção, certificado energético                       │   │
│  │ - Lat/lon (coordenadas)                                              │   │
│  │ - Freguesia, concelho                                                │   │
│  │ - URLs dos listings                                                 │   │
│  │                                                                     │   │
│  │ Estes dados são públicos nos portais e não são dados pessoais.     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  LOCAL-FIRST APPROACH:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Dados ficam localmente no PC do utilizador                         │   │
│  │ - Nada é enviado para cloud                                         │   │
│  │ - Utilizador tem controlo total dos dados                              │   │
│  │ - Compliance por design                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  RIGHT TO BE FORGOTTEN:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Utilizador pode pedir eliminação de dados                          │   │
│  │ - Implementar endpoint DELETE /listings/{id}                       │   │
│  │ - Confirmar identidade antes de eliminar                              │   │
│  │ - Eliminação permanente (hard delete)                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DATA RETENTION:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Dados guardados por 90 dias (configurável)                       │   │
│  │ - Após 90 dias, dados são eliminados automaticamente                │   │
│  │ - Logs guardados por 30 dias                                        │   │
│  │ - Backups guardados por 30 dias                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. DATA PROTECTION

### 4.1 Encriptação de Database

```python
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)

class DatabaseEncryption:
    """Encriptação de database."""
    
    def __init__(self, key: str = None):
        if key is None:
            # Gerar chave aleatória (guardar em .env)
            key = Fernet.generate_key()
        
        self.cipher = Fernet(key.encode())
    
    def encrypt_data(self, data: str) -> str:
        """Encripta dados."""
        encrypted = self.cipher.encrypt(data.encode())
        return encrypted.decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Desencripta dados."""
        decrypted = self.cipher.decrypt(encrypted_data.encode())
        return decrypted.decode()
    
    def encrypt_listing(self, listing: Dict) -> Dict:
        """Encripta campos sensíveis do listing."""
        # Campos sensíveis
        sensitive_fields = ['morada_raw', 'contacto', 'agencia_contacto']
        
        encrypted_listing = listing.copy()
        
        for field in sensitive_fields:
            if field in listing and listing[field]:
                encrypted_listing[field] = self.encrypt_data(listing[field])
        
        return encrypted_listing
```

### 4.2 Encriptação de Secrets

```python
class SecretEncryption:
    """Encriptação de secrets."""
    
    def __init__(self, master_key: str = None):
        if master_key is None:
            master_key = os.getenv('FERNET_KEY', Fernet.generate_key())
        
        self.cipher = Fernet(master_key.encode())
    
    def encrypt_secret(self, secret: str) -> str:
        """Encripta secret."""
        encrypted = self.cipher.encrypt(secret.encode())
        return encrypted.decode()
    
    def decrypt_secret(self, encrypted_secret: str) -> str:
        """Desencripta secret."""
        decrypted = self.cipher.decrypt(encrypted_secret.encode())
        return decrypted.decode()
```

---

## 5. SECRETS MANAGEMENT

### 5.1 Estratégia de Secrets Management

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              ESTRATÉGIA DE SECRETS MANAGEMENT                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SECRETS:                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - TELEGRAM_BOT_TOKEN (token do bot Telegram)                         │   │
│  │ - TELEGRAM_CHAT_ID (chat_id do Telegram)                            │   │
│  │ - FERNET_KEY (chave de encriptação)                                │   │
│  │ - DATABASE_PASSWORD (se us PostgreSQL)                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ARMAZENAMENTO:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ .env (não versionado no git)                                       │   │
│  │ Environment variables (em runtime)                                  │   │
│  │ Encriptação com Fernet (em repouso)                                │   │
│  │ Chave de encriptação separada (não no .env)                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  .GITIGNORE:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ .env                                                               │   │
│  │ venv/                                                              │   │
│  │ __pycache__/                                                        │   │
│  │ *.pyc                                                              │   │
│  │ data/                                                              │   │
│  │ logs/                                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ROTATION DE SECRETS:                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Rotacionar Telegram bot token a cada 90 dias                       │   │
│  │ Rotacionar Fernet key a cada 180 dias                               │   │
│  │ Rotacionar database password a cada 90 dias (se PostgreSQL)       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. AUTHENTICATION E AUTHORIZATION

### 6.1 Dashboard (Local Deployment)

**Para local deployment, o dashboard não tem autenticação:**
- Apenas o utilizador do PC tem acesso
- Dashboard não é exposto na internet (localhost:8501)
- Se necessário, pode adicionar password simples

**Implementação Opcional de Password:**

```python
import streamlit as st
from streamlit_option_menu import option_menu

# Configurar password
PASSWORD = st.secrets.get("DASHBOARD_PASSWORD", "default_password")

# Página de login
if "authenticated" not in st.session_state:
    st.title("🔐 Login")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if password == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Password incorrect")
    
    st.stop()

# Se autenticado, mostrar dashboard
st.title("🏠 Real Estate Opportunity Engine")
```

### 6.2 Telegram Bot (Token-based)

**Telegram bot usa token para autenticação:**
- Token é gerado pelo BotFather
- Token é secret (não deve ser partilhado)
- Bot pode ser controlado por chat_id

---

## 7. INPUT VALIDATION

### 7.1 Implementação de Input Validation

```python
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class InputValidator:
    """Validação de inputs."""
    
    def validate_price(self, price: any) -> Tuple[bool, float, List[str]]:
        """Valida preço."""
        errors = []
        
        # Verificar tipo
        if isinstance(price, str):
            # Remover símbolos
            price = price.replace("€", "").replace(".", "").replace(" ", "").strip()
            try:
                price = float(price)
            except ValueError:
                errors.append("Preço inválido: não é um número")
                return (False, 0.0, errors)
        
        # Verificar se é float
        if not isinstance(price, (int, float)):
            errors.append("Preço inválido: não é um número")
            return (False, 0.0, errors)
        
        # Verificar range
        if price <= 0:
            errors.append("Preço deve ser > 0")
        elif price > 10000000:  # 10 milhões
            errors.append("Preço suspeito: > 10M€")
        
        return (len(errors) == 0, float(price), errors)
    
    def validate_area(self, area: any) -> Tuple[bool, float, List[str]]:
        """Valida área."""
        errors = []
        
        # Verificar tipo
        if isinstance(area, str):
            # Remover símbolos
            area = area.replace("m²", "").replace(" ", "").strip()
            try:
                area = float(area)
            except ValueError:
                errors.append("Área inválida: não é um número")
                return (False, 0.0, errors)
        
        # Verificar se é float
        if not isinstance(area, (int, float)):
            errors.append("Área inválida: não é um número")
            return (False, 0.0, errors)
        
        # Verificar range
        if area <= 0:
            errors.append("Área deve ser > 0")
        elif area > 1000:  # 1000 m²
            errors.append("Área suspeita: > 1000 m²")
        
        return (len(errors) == 0, float(area), errors)
    
    def validate_rooms(self, rooms: any) -> Tuple[bool, int, List[str]]:
        """Valida quartos."""
        errors = []
        
        # Verificar tipo
        if isinstance(rooms, str):
            try:
                rooms = int(rooms)
            except ValueError:
                errors.append("Quartos inválido: não é um número")
                return (False, 0, errors)
        
        # Verificar se é int
        if not isinstance(rooms, int):
            errors.append("Quartos inválido: não é um número")
            return (False, 0, errors)
        
        # Verificar range
        if rooms < 0:
            errors.append("Quartos deve ser ≥ 0")
        elif rooms > 20:  # 20 quartos
            errors.append("Quartos suspeito: > 20")
        
        return (len(errors) == 0, int(rooms), errors)
```

---

## 8. SQL INJECTION PREVENTION

### 8.1 SQLAlchemy ORM

**SQLAlchemy ORM previne SQL injection automaticamente:**
- Usa parameterized queries
- Escapes automaticamente
- Não permite SQL injection

```python
# Seguro (SQLAlchemy ORM)
from sqlalchemy import text

# ✅ Seguro (parameterized)
result = session.execute(
    text("SELECT * FROM listings WHERE price > :price"),
    {"price": 100000}
)

# ❌ Inseguro (string concatenation - NÃO FAZER ISTO)
# result = session.execute(f"SELECT * FROM listings WHERE price > {price}")
```

---

## 9. XSS PREVENTION

### 9.1 XSS Prevention no Dashboard

**Streamlit previne XSS automaticamente:**
- Escapes automaticamente
- Não permite execução de JavaScript injectado
- Usa sanitização de inputs

```python
# Seguro (Streamlit)
st.markdown(user_input)  # Streamlit sanitiza automaticamente

# ❌ Inseguro (HTML raw - NÃO FAZER ISTO)
# st.html(f"<div>{user_input}</div>")
```

---

## 10. RATE LIMITING

### 10.1 Rate Limiting Implementation

```python
from typing import Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiting."""
    
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # {key: [timestamp1, timestamp2, ...]}
    
    def is_allowed(self, key: str) -> bool:
        """Verifica se request é permitido."""
        now = datetime.now()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Limpar timestamps antigos
        self.requests[key] = [
            ts for ts in self.requests[key]
            if (now - ts).total_seconds() < self.window_seconds
        ]
        
        # Verificar limite
        if len(self.requests[key]) >= self.max_requests:
            logger.warning(f"RateLimiter: Limite excedido para {key}")
            return False
        
        # Registar request
        self.requests[key].append(now)
        return True
```

---

## 11. LOGGING SECURITY

### 11.1 Logging Sem Dados Pessoais

```python
from loguru import logger

# ❌ INSEGURO (log dados pessoais)
logger.info(f"Listing de João Silva na Rua do Cedofeita 123")

# ✅ SEGURO (sem dados pessoais)
logger.info(f"Listing {listing_id} processado")

# ❌ INSEGURO (log morada completa)
logger.info(f"Morada: {morada_raw}")

# ✅ SEGURO (log apenas freguesia)
logger.info(f"Freguesia: {freguesia}")
```

---

## 12. NETWORK SECURITY

### 12.1 Firewall (Windows)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              FIREWALL (WINDOWS DEFENDER)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  REGRAS DE INBOUND:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Permitir: Porta 8501 (Streamlit) - apenas localhost            │   │
│  │ - Bloquear: Todas as outras portas                                   │   │
│  │ - Windows Defender Firewall activado                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  REGRAS DE OUTBOUND:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Permitir: HTTPS (443) para portais imobiliários                  │   │
│  │ - Permitir: HTTPS (443) para Telegram API                             │   │
│  │ - Bloquear: Portas desconhecidas                                     │   │
│  │ - Windows Defender Firewall activado                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 13. ETHICAL SCRAPING

### 13.1 Princípios de Ethical Scraping

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              PRINCÍPIOS DE ETHICAL SCRAPING                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. RESPEITAR ROBOTS.TXT                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Verificar robots.txt de cada portal                                  │   │
│  │ Respeitar Disallow directives                                      │   │
│  │ Não scraping páginas proibidas                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  2. RESPEITAR RATE LIMITS                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Rate limiting por portal (1 request/15 segundos)                 │   │
│  │ Backoff em falhas (1s, 2s, 4s, 8s...)                                │   │
│  │ Não sobrecarregar servidores                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  3. RESPEITAR TERMOS DE SERVIÇO                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Verificar termos de serviço de cada portal                            │   │
│  │ Respeitar proibições de scraping                                    │   │
│  │ Não usar dados para fins comerciais sem autorização                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  4. NÃO COMPETIR COM UTILIZADORES REAIS                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Não usar scraping para ganhar vantagem injusta                     │   │
│  │ Não usar dados para spam                                             │   │
│  │ Respeitar utilizadores reais                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  5. IDENTIFICAR-SE                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ User-Agent claro (identifica bot, não se faz passar por humano)    │   │
│  │ Contact information (se solicitado)                                 │   │
│  │ Não tentar esconder que é um bot                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 14. SECURITY AUDIT

### 14.1 Checklist de Security

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              SECURITY CHECKLIST                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DATA PROTECTION:                                                         │
│  □ Database encriptado?                                                   │
│  □ Secrets encriptados?                                                   │
│  □ .env no .gitignore?                                                   │
│  □ FERNET_KEY separada?                                                 │
│                                                                             │
│  INPUT VALIDATION:                                                       │
│  □ Todos os inputs validados?                                            │
│  □ Ranges verificados?                                                   │
│  □ Tipos verificados?                                                     │
│  □ SQL injection prevenido?                                              │
│  □ XSS prevenido?                                                         │
│                                                                             │
│  AUTHORIZATION:                                                           │
│  □ Dashboard protegido? (local deployment: não necessário)              │
│  □ Telegram token secreto?                                               │
│  □ API endpoints protegidos?                                            │
│                                                                             │
│  RATE LIMITING:                                                           │
│  □ Rate limiting por portal?                                             │
│  □ Rate limiting por dashboard?                                          │
│  □ Rate limiting por Telegram?                                           │
│                                                                             │
│  LOGGING SECURITY:                                                        │
│  □ Logs sem dados pessoais?                                               │
│  □ Logs encriptados (opcional)?                                          │
│  □ Log rotation activa?                                                  │
│  □ Retenção 30 dias?                                                    │
│                                                                             │
│  NETWORK SECURITY:                                                        │
│  □ Firewall activado?                                                     │
│  □ Portas desnecessárias bloqueadas?                                     │
│  □ Windows Defender activado?                                            │
│  □ Antivírus activado?                                                   │
│                                                                             │
│  ETHICAL SCRAPING:                                                        │
│  □ robots.txt respeitado?                                               │
│  □ Rate limits respeitados?                                             │
│  □ Termos de serviço respeitados?                                       │
│  □ User-Agent claro?                                                    │
│                                                                             │
│  GDPR COMPLIANCE:                                                        │
│  □ Dados minimizados?                                                    │
│  □ Dados retidos apenas 90 dias?                                        │
│  □ Right to be forgotten implementado?                                  │
│  □ Consentimento obtido? (não aplicável, dados públicos)                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 15. GLOSSÁRIO DE SECURITY

```
┌─────────────────────────────────────────────────────────────────────────────┐
│            GLOSSÁRIO DE SECURITY                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SECURITY: Segurança (proteção do sistema e dados)                     │
│                                                                             │
│  GDPR: General Data Protection Regulation (regulamento UE de dados)   │
│                                                                             │
│  DATA PROTECTION: Proteção de dados (encriptação, backup)            │
│                                                                             │
│  ENCRYPTION: Encriptação (proteção de dados em repouso)              │
│                                                                             │
│  DECRYPTION: Desencriptação (recuperação de dados encriptados)        │
│                                                                             │
│  FERNET: Biblioteca de encriptação simétrica                             │
│                                                                             │
│  SECRET: Secret (token, password, chave)                               │
│                                                                             │
│  SECRETS MANAGEMENT: Gestão de secrets (armazenamento, rotação)    │
│                                                                             │
│  ENVIRONMENT VARIABLES: Variáveis de ambiente (.env)                   │
│                                                                             │
│  .ENV: Ficheiro de variáveis de ambiente (não versionado)               │
│                                                                             │
│  .GITIGNORE: Ficheiro gitignore (exclui ficheiros do versionamento)  │
│                                                                             │
│  AUTHENTICATION: Autenticação (verificação de identidade)             │
│                                                                             │
│  AUTHORIZATION: Autorização (verificação de permissões)               │
│                                                                             │
│  INPUT VALIDATION: Validação de inputs (prevenção de ataques)        │
│                                                                             │
│  SQL INJECTION: SQL injection (ataque via queries SQL maliciosas)    │
│                                                                             │
│  XSS: Cross-Site Scripting (ataque via scripts injectados)           │
│                                                                             │
│  RATE LIMITING: Rate limiting (limitação de taxa de requests)          │
│                                                                             │
│  FIREWALL: Firewall (proteção de rede)                                 │
│                                                                             │
│  LOGGING SECURITY: Logging security (proteção de logs)                │
│                                                                             │
│  ETHICAL SCRAPING: Scraping ético (respeito de termos e limites)    │
│                                                                             │
│  ROBOTS.TXT: Ficheiro robots.txt (regras para bots)                    │
│                                                                             │
│  RATE LIMIT: Rate limit (limite de taxa de requests)                     │
│                                                                             │
│  TERMS OF SERVICE: Termos de serviço                                   │
│                                                                             │
│  USER-AGENT: User-Agent (identificador de browser/bot)                 │
│                                                                             │
│  RIGHT TO BE FORGOTTEN: Direito ao esquecimento (GDPR)                │
│                                                                             │
│  DATA MINIMIZATION: Minimização de dados (apenas dados necessários)    │
│                                                                             │
│  DATA RETENTION: Retenção de dados (tempo de guarda)                     │
│                                                                             │
│  ACCOUNTABILITY: Responsabilidade (dever de compliance)               │
│                                                                             │
│  LAWFULNESS: Legalidade (processamento legal de dados)                 │
│                                                                             │
│  FAIRNESS: Equidade (processamento justo de dados)                       │
│                                                                             │
│  TRANSPARENCY: Transparência (informação clara sobre processamento)    │
│                                                                             │
│  ACCURACY: Exactidão (dados exactos e actualizados)                     │
│                                                                             │
│  INTEGRITY: Integridade (proteção contra alterações não autorizadas)  │
│                                                                             │
│  CONFIDENTIALITY: Confidencialidade (proteção contra acesso não autorizado)│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*Fim do Documento 15 — Security e GDPR*
