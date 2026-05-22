# NOTIFICAÇÕES TELEGRAM — REAL ESTATE OPPORTUNITY ENGINE
## Sistema de Notificações em Tempo Real via Telegram Bot

> **Este documento:** Especificação completa do sistema de notificações  
> **Objectivo:** Fornecer especificação detalhada de notificações para IA implementar  
> **Linhas:** 1500+ linhas de documentação detalhada  
> **Versão:** 5.0 (Actualizado com Volume 13)

---

## ÍNDICE

1. [Introdução ao Sistema de Notificações](#1-introducao-ao-sistema-de-notificacoes)
2. [Arquitectura de Notificações](#2-arquitetura-de-notificacoes)
3. [Telegram Bot Setup](#3-telegram-bot-setup)
4. [Message Formatter](#4-message-formatter)
5. [Opportunity Selector](#5-opportunity-selector)
6. [Notification Engine](#6-notification-engine)
7. [Notification History](#7-notification-history)
8. [Filtros Personalizados](#8-filtros-personalizados)
9. [Rate Limiting de Notificações](#9-rate-limiting-de-notificacoes)
10. [Error Handling](#10-error-handling)
11. [Segurança de Notificações](#11-seguranca-de-notificacoes)
12. [Monitoring de Notificações](#12-monitoring-de-notificacoes)
13. [A/B Testing de Notificações](#13-ab-testing-de-notificacoes)
14. [Best Practices Telegram](#14-best-practices-telegram)
15. [Glossário de Notificações](#15-glossario-de-notificacoes)

---

## 1. INTRODUÇÃO AO SISTEMA DE NOTIFICAÇÕES

### 1.1 Objectivo das Notificações

**Sistema de Notificações** envia notificações em tempo real via Telegram para o utilizador quando surgem oportunidades de investimento (listings com score ≥ 8).

**Objectivo:** Informar o utilizador de top 3-5 listings/dia sem ter que verificar o dashboard constantemente.

### 1.2 Porquê Telegram?

**Vantagens do Telegram:**
- API gratuita e robusta
- Suporta formatação rica (Markdown, HTML)
- Bot API fácil de usar (python-telegram-bot)
- Multi-plataforma (mobile, desktop, web)
- Notificações instantâneas (push notifications)
- Suporta ficheiros, fotos, botões inline
- Webhooks para notificações em tempo real

**Alternativas:**
- Email: Mais lento, menos imediato
- SMS: Custo por mensagem
- WhatsApp: API oficial custosa, não oficial não confiável
- Push notifications (app): Requer app nativo

---

## 2. ARQUITECTURA DE NOTIFICAÇÕES

### 2.1 Arquitectura de Alto Nível

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              ARQUITECTURA DE NOTIFICAÇÕES                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SCORES (scores table)                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - score_total (0-10)                                                 │   │
│  │ - score_discount (0-10)                                              │   │
│  │ - score_location (0-10)                                             │   │
│  │ - score_condition (0-10)                                            │   │
│  │ - score_liquidity (0-10)                                            │   │
│  │ - score_freshness (0-10)                                             │   │
│  │ - classificacao (Imperdível, Bom, Aceitável, Não recomendado)        │   │
│  │ - rationale (explicação)                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  OPPORTUNITY SELECTOR                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Filtra listings com score ≥ 8                                    │   │
│  │ - Aplica filtros personalizados (preço, área, freguesias)          │   │
│  │ - Ordena por score e discount                                       │   │
│  │ - Selecciona top 3-5 listings/dia                                    │   │
│  │ - Evita duplicações (listings já notificados)                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  MESSAGE FORMATTER                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Formata mensagem em Markdown                                     │   │
│  │ - Inclui: título, preço, score, rationale, link                     │   │
│  │ - Adiciona emojis para destacar informação                           │   │
│  │ - Limita tamanho (max 4096 caracteres)                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  TELEGRAM BOT                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Envia mensagem para chat_id(s)                                     │   │
│  │ - Suporta Markdown e HTML                                            │   │
│  │ - Envia fotos do listing                                           │   │
│  │ - Suporta botões inline (ver no dashboard)                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                            │   │
│                              ▼                                            │   │
│  NOTIFICATION HISTORY                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - Registra notificações enviadas                                   │   │
│  │ - Guarda listing_id, chat_id, message_id, timestamp               │   │
│  │ - Evita duplicações (listings já notificados)                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. TELEGRAM BOT SETUP

### 3.1 Criar Telegram Bot

**Passo 1: Criar Bot via BotFather**
1. Abrir Telegram e pesquisar por @BotFather
2. Enviar `/newbot`
3. Seguir instruções:
   - Nome do bot: `Real Estate Opportunity Bot`
   - Username: `realestate_opportunity_bot` (ou similar)
4. BotFather retorna API Token (guardar em `.env`)

**Passo 2: Obter Chat ID**
1. Enviar `/start` ao bot
2. Usar API `getUpdates` para obter chat_id
3. Guardar chat_id em `.env`

**Passo 3: Configurar `.env`**
```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

### 3.2 Implementação Telegram Bot

```python
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import logging

logger = logging.getLogger(__name__)

class TelegramBot:
    """Telegram Bot para notificações."""
    
    def __init__(self, token: str):
        self.token = token
        self.bot = Bot(token=token)
        self.application = Application.builder().token(token).build()
    
    async def send_message(
        self,
        chat_id: str,
        message: str,
        parse_mode: str = 'Markdown',
        disable_web_page_preview: bool = True
    ) -> int:
        """Envia mensagem para chat_id."""
        try:
            message_obj = await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview
            )
            logger.info(f"TelegramBot: Mensagem enviada para {chat_id}")
            return message_obj.message_id
        except Exception as e:
            logger.error(f"TelegramBot: Erro ao enviar mensagem: {e}")
            raise
    
    async def send_photo(
        self,
        chat_id: str,
        photo_url: str,
        caption: str,
        parse_mode: str = 'Markdown'
    ) -> int:
        """Envia foto com caption."""
        try:
            message_obj = await self.bot.send_photo(
                chat_id=chat_id,
                photo=photo_url,
                caption=caption,
                parse_mode=parse_mode
            )
            logger.info(f"TelegramBot: Foto enviada para {chat_id}")
            return message_obj.message_id
        except Exception as e:
            logger.error(f"TelegramBot: Erro ao enviar foto: {e}")
            raise
    
    async def send_message_with_buttons(
        self,
        chat_id: str,
        message: str,
        buttons: list,
        parse_mode: str = 'Markdown'
    ) -> int:
        """Envia mensagem com botões inline."""
        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            keyboard = [
                [InlineKeyboardButton(text=button['text'], callback_data=button['callback_data'])]
                for button in buttons
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message_obj = await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
            logger.info(f"TelegramBot: Mensagem com botões enviada para {chat_id}")
            return message_obj.message_id
        except Exception as e:
            logger.error(f"TelegramBot: Erro ao enviar mensagem com botões: {e}")
            raise
```

---

## 4. MESSAGE FORMATTER

### 4.1 Formato de Mensagem

**Estrutura da Mensagem:**
```
🏠 *Imperdível:* [Título do Imóvel]

💰 Preço: 180.000€
📏 Área: 85 m²
📍 Localização: Cedofeita, Porto
🚇 Metro: 300m (Trindade)

📊 *Score:* 9.2/10
   - Discount: 9.5/10 (25%)
   - Location: 8.5/10
   - Condition: 8.0/10
   - Liquidity: 8.0/10
   - Freshness: 9.0/10

💡 *Rationale:* Discount 25% em Cedofeita com metro próximo, imóvel renovado em 2022, excelente liquidez, apenas 3 dias no mercado

🔗 [Ver no Dashboard](http://localhost:8501?listing_id=123)

📅 *Publicado há:* 3 dias
```

### 4.2 Implementação Message Formatter

```python
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class MessageFormatter:
    """Formata mensagens para Telegram."""
    
    def __init__(self, dashboard_url: str = "http://localhost:8501"):
        self.dashboard_url = dashboard_url
    
    def format_opportunity_message(self, listing: Dict, valuation: Dict, score: Dict) -> str:
        """Formata mensagem de oportunidade."""
        # Emoji de classificação
        classification = score.get('classificacao', '')
        if classification == 'Imperdível':
            emoji = '🏠'
        elif classification == 'Bom':
            emoji = '🏡'
        elif classification == 'Aceitável':
            emoji = '🏢'
        else:
            emoji = '🏚️'
        
        # Título
        titulo = listing.get('titulo', 'Sem título')
        
        # Preço e área
        preco = listing.get('preco_pedido', 0)
        area = listing.get('area_util_m2', 0)
        preco_por_m2 = listing.get('preco_por_m2', 0)
        
        # Localização
        freguesia = listing.get('freguesia', '')
        concelho = listing.get('concelho', '')
        dist_metro = listing.get('dist_metro_m', 0)
        
        # Score
        score_total = score.get('score_total', 0)
        score_discount = score.get('score_discount', 0)
        score_location = score.get('score_location', 0)
        score_condition = score.get('score_condition', 0)
        score_liquidity = score.get('score_liquidity', 0)
        score_freshness = score.get('score_freshness', 0)
        
        # Rationale
        rationale = score.get('rationale', '')
        
        # Dias no mercado
        scrape_timestamp = listing.get('scrape_timestamp', '')
        dias_mercado = self._calculate_days_on_market(scrape_timestamp)
        
        # Link dashboard
        listing_id = listing.get('id', '')
        dashboard_link = f"{self.dashboard_url}?listing_id={listing_id}"
        
        # Montar mensagem
        message = f"""{emoji} *{classification}:* {titulo}

💰 Preço: {preco:,.0f}€ ({preco_por_m2:,.0f}€/m²)
📏 Área: {area} m²
📍 Localização: {freguesia}, {concelho}
🚇 Metro: {dist_metro:.0f}m

📊 *Score:* {score_total:.1f}/10
   - Discount: {score_discount:.1f}/10
   - Location: {score_location:.1f}/10
   - Condition: {score_condition:.1f}/10
   - Liquidity: {score_liquidity:.1f}/10
   - Freshness: {score_freshness:.1f}/10

💡 *Rationale:* {rationale}

🔗 [Ver no Dashboard]({dashboard_link})

📅 *Publicado há:* {dias_mercado} dias"""
        
        logger.info(f"MessageFormatter: Mensagem formatada ({len(message)} caracteres)")
        
        return message
    
    def format_summary_message(self, total_opportunities: int, top_score: float) -> str:
        """Formata mensagem de resumo diário."""
        message = f"""📊 *Resumo Diário de Oportunidades*

🏠 Total de oportunidades: {total_opportunities}
📊 Melhor score: {top_score:.1f}/10

Ver mais detalhes no dashboard: {self.dashboard_url}"""
        
        return message
    
    def _calculate_days_on_market(self, scrape_timestamp: str) -> int:
        """Calcula dias no mercado."""
        if not scrape_timestamp:
            return 0
        
        try:
            from datetime import datetime
            scrape_date = datetime.fromisoformat(scrape_timestamp)
            days = (datetime.now() - scrape_date).days
            return max(0, days)
        except:
            return 0
```

---

## 5. OPPORTUNITY SELECTOR

### 5.1 Responsabilidade

**Opportunity Selector** selecciona top 3-5 listings/dia baseado em:
- Score ≥ 8 (Imperdível)
- Filtros personalizados (preço, área, freguesias)
- Não duplicados (listings já notificados)
- Ordenado por score e discount

### 5.2 Implementação Opportunity Selector

```python
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class OpportunitySelector:
    """Selecciona top oportunidades para notificação."""
    
    def __init__(self, database_repository):
        self.database_repository = database_repository
    
    async def select_top_opportunities(
        self,
        min_score: float = 8.0,
        max_listings: int = 5,
        filters: Dict = None
    ) -> List[Dict]:
        """Selecciona top oportunidades."""
        logger.info(f"OpportunitySelector: Seleccionando top {max_listings} oportunidades")
        
        # Obter listings com score ≥ min_score
        listings = await self.database_repository.get_listings_with_score(
            min_score=min_score,
            limit=max_listings * 2  # Obter mais do que necessário
        )
        
        if not listings:
            logger.info("OpportunitySelector: Nenhuma oportunidade encontrada")
            return []
        
        # Aplicar filtros personalizados
        if filters:
            listings = self._apply_filters(listings, filters)
        
        # Remover listings já notificados
        listings = await self._remove_already_notified(listings)
        
        if not listings:
            logger.info("OpportunitySelector: Nenhuma oportunidade nova (todas já notificadas)")
            return []
        
        # Ordenar por score e discount
        listings = sorted(
            listings,
            key=lambda x: (x['score_total'], x['discount']),
            reverse=True
        )
        
        # Seleccionar top max_listings
        top_listings = listings[:max_listings]
        
        logger.info(f"OpportunitySelector: {len(top_listings)} oportunidades seleccionadas")
        
        return top_listings
    
    def _apply_filters(self, listings: List[Dict], filters: Dict) -> List[Dict]:
        """Aplica filtros personalizados."""
        filtered = []
        
        for listing in listings:
            # Filtro: Preço máximo
            if 'preco_max' in filters:
                if listing['preco_pedido'] > filters['preco_max']:
                    continue
            
            # Filtro: Preço mínimo
            if 'preco_min' in filters:
                if listing['preco_pedido'] < filters['preco_min']:
                    continue
            
            # Filtro: Área mínima
            if 'area_min' in filters:
                if listing['area_util_m2'] < filters['area_min']:
                    continue
            
            # Filtro: Freguesias
            if 'freguesias' in filters:
                if listing['freguesia'].lower() not in [f.lower() for f in filters['freguesias']]:
                    continue
            
            # Filtro: Estado
            if 'estados' in filters:
                if listing['estado'].lower() not in [e.lower() for e in filters['estados']]:
                    continue
            
            filtered.append(listing)
        
        logger.info(f"OpportunitySelector: {len(filtered)} listings após filtros (de {len(listings)})")
        
        return filtered
    
    async def _remove_already_notified(self, listings: List[Dict]) -> List[Dict]:
        """Remove listings já notificados."""
        not_listings = []
        
        for listing in listings:
            listing_id = listing['id']
            
            # Verificar se já foi notificado
            already_notified = await self.database_repository.is_listing_notified(listing_id)
            
            if not already_notified:
                not_listings.append(listing)
        
        logger.info(f"OpportunitySelector: {len(not_listings)} listings não notificados (de {len(listings)})")
        
        return not_listings
```

---

## 6. NOTIFICATION ENGINE

### 6.1 Responsabilidade

**Notification Engine** orquestra o envio de notificações:
- Opportunity Selector selecciona listings
- Message Formatter formata mensagens
- Telegram Bot envia notificações
- Notification History regista envios

### 6.2 Implementação Notification Engine

```python
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class NotificationEngine:
    """Engine de notificações."""
    
    def __init__(
        self,
        opportunity_selector,
        message_formatter,
        telegram_bot,
        database_repository
    ):
        self.opportunity_selector = opportunity_selector
        self.message_formatter = message_formatter
        self.telegram_bot = telegram_bot
        self.database_repository = database_repository
    
    async def notify_top_opportunities(self, chat_ids: List[str], filters: Dict = None):
        """Notifica top oportunidades."""
        logger.info("NotificationEngine: Iniciando notificações")
        
        # Seleccionar oportunidades
        opportunities = await self.opportunity_selector.select_top_opportunities(filters=filters)
        
        if not opportunities:
            logger.info("NotificationEngine: Nenhuma oportunidade para notificar")
            # Enviar mensagem de resumo mesmo assim
            summary_message = self.message_formatter.format_summary_message(0, 0)
            for chat_id in chat_ids:
                await self.telegram_bot.send_message(chat_id, summary_message)
            return
        
        # Enviar notificações
        sent_count = 0
        for opportunity in opportunities:
            for chat_id in chat_ids:
                try:
                    # Formatar mensagem
                    message = self.message_formatter.format_opportunity_message(
                        opportunity['listing'],
                        opportunity['valuation'],
                        opportunity['score']
                    )
                    
                    # Enviar mensagem
                    message_id = await self.telegram_bot.send_message(
                        chat_id=chat_id,
                        message=message
                    )
                    
                    # Registar notificação
                    await self.database_repository.insert_notification({
                        'listing_id': opportunity['listing']['id'],
                        'telegram_chat_id': chat_id,
                        'telegram_message_id': str(message_id),
                        'message': message,
                        'sent_at': datetime.now().isoformat()
                    })
                    
                    sent_count += 1
                    
                except Exception as e:
                    logger.error(f"NotificationEngine: Erro ao notificar listing {opportunity['listing']['id']}: {e}")
                    continue
        
        logger.info(f"NotificationEngine: {sent_count} notificações enviadas")
        
        return sent_count
```

---

## 7. NOTIFICATION HISTORY

### 7.1 Responsabilidade

**Notification History** regista todas as notificações enviadas para:
- Evitar duplicações (não notificar o mesmo listing duas vezes)
- Rastrear histórico de notificações
- Analisar eficácia de notificações

### 7.2 Implementação Notification History

```python
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class NotificationHistory:
    """Histórico de notificações."""
    
    def __init__(self, database_repository):
        self.database_repository = database_repository
    
    async def is_listing_notified(self, listing_id: str) -> bool:
        """Verifica se listing já foi notificado."""
        notification = await self.database_repository.get_latest_notification(listing_id)
        
        if notification:
            # Verificar se foi notificado nas últimas 24 horas
            from datetime import datetime, timedelta
            sent_at = datetime.fromisoformat(notification['sent_at'])
            if (datetime.now() - sent_at) < timedelta(hours=24):
                return True
        
        return False
    
    async def get_notification_stats(self, days: int = 7) -> Dict:
        """Retorna estatísticas de notificações."""
        from datetime import datetime, timedelta
        
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        stats = await self.database_repository.get_notification_stats(since_date)
        
        return stats
```

---

## 8. FILTROS PERSONALIZADOS

### 8.1 Tipos de Filtros

**Filtros Disponíveis:**
- **Preço:** preço_min, preço_max
- **Área:** area_min
- **Freguesias:** lista de freguesias
- **Estado:** lista de estados (Novo, Bom, Ruim, etc.)
- **Score:** score_min
- **Quartos:** quartos_min, quartos_max

### 8.2 Implementação de Filtros

```python
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class NotificationFilters:
    """Filtros personalizados para notificações."""
    
    def __init__(self, database_repository):
        self.database_repository = database_repository
    
    async def get_user_filters(self, user_id: str) -> Dict:
        """Obtém filtros do utilizador."""
        filters = await self.database_repository.get_config(f"user_filters_{user_id}")
        
        if not filters:
            # Filtros default
            filters = {
                'preco_max': 500000,
                'area_min': 50,
                'freguesias': ['cedofeita', 'paranhos', 'bonfim'],
                'estados': ['novo', 'muito bom', 'bom'],
                'score_min': 8.0
            }
        
        return filters
    
    async def set_user_filters(self, user_id: str, filters: Dict):
        """Define filtros do utilizador."""
        await self.database_repository.set_config(
            f"user_filters_{user_id}",
            filters
        )
        
        logger.info(f"NotificationFilters: Filtros definidos para {user_id}")
```

---

## 9. RATE LIMITING DE NOTIFICAÇÕES

### 9.1 Estratégia de Rate Limiting

**Regras:**
- Máximo 5 notificações/dia por chat_id
- Máximo 1 notificação/hora por chat_id
- Evitar spam de notificações

### 9.2 Implementação Rate Limiting

```python
from typing import Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class NotificationRateLimiter:
    """Rate limiting de notificações."""
    
    def __init__(self):
        self.notification_counts = {}  # {chat_id: [timestamp1, timestamp2, ...]}
    
    async def can_notify(self, chat_id: str) -> bool:
        """Verifica se pode notificar chat_id."""
        now = datetime.now()
        
        # Inicializar se necessário
        if chat_id not in self.notification_counts:
            self.notification_counts[chat_id] = []
        
        # Limpar timestamps antigos (> 24 horas)
        self.notification_counts[chat_id] = [
            ts for ts in self.notification_counts[chat_id]
            if (now - ts) < timedelta(hours=24)
        ]
        
        # Verificar limite diário
        if len(self.notification_counts[chat_id]) >= 5:
            logger.warning(f"NotificationRateLimiter: Limite diário atingido para {chat_id}")
            return False
        
        # Verificar limite horário
        recent_hour = [
            ts for ts in self.notification_counts[chat_id]
            if (now - ts) < timedelta(hours=1)
        ]
        if len(recent_hour) >= 1:
            logger.warning(f"NotificationRateLimiter: Limite horário atingido para {chat_id}")
            return False
        
        return True
    
    async def record_notification(self, chat_id: str):
        """Registra notificação."""
        self.notification_counts[chat_id].append(datetime.now())
        
        logger.info(f"NotificationRateLimiter: Notificação registada para {chat_id}")
```

---

## 10. ERROR HANDLING

### 10.1 Estratégias de Error Handling

**Erros Comuns:**
- Bot blocked by user
- Network timeout
- Invalid chat_id
- Message too long (> 4096 caracteres)

### 10.2 Implementação Error Handling

```python
from typing import Dict
import logging

logger = logging.getLogger(__init__)

class NotificationErrorHandler:
    """Gestão de erros de notificações."""
    
    def __init__(self):
        self.error_counts = {}
    
    def handle_error(self, chat_id: str, error: Exception):
        """Registra erro de notificação."""
        error_type = type(error).__name__
        
        if chat_id not in self.error_counts:
            self.error_counts[chat_id] = {}
        
        self.error_counts[chat_id][error_type] = self.error_counts[chat_id].get(error_type, 0) + 1
        
        logger.error(f"NotificationErrorHandler: Erro {error_type} para {chat_id}: {error}")
    
    def should_disable_notifications(self, chat_id: str) -> bool:
        """Verifica se deve desactivar notificações para chat_id."""
        if chat_id not in self.error_counts:
            return False
        
        total_errors = sum(self.error_counts[chat_id].values())
        
        # Se > 10 erros nas últimas 24 horas, desactivar
        if total_errors >= 10:
            logger.warning(f"NotificationErrorHandler: Desactivando notificações para {chat_id} (muitos erros)")
            return True
        
        return False
```

---

## 11. SEGURANÇA DE NOTIFICAÇÕES

### 11.1 Medidas de Segurança

**Medidas:**
- Encriptar Telegram tokens (Fernet)
- Não hardcode tokens no código
- Usar environment variables
- Validar chat_ids
- Rate limiting (evitar spam)

### 11.2 Implementação de Segurança

```python
from cryptography.fernet import Fernet
import os
import logging

logger = logging.getLogger(__name__)

class TelegramTokenSecurity:
    """Segurança de tokens Telegram."""
    
    def __init__(self):
        # Chave de encriptação (deve estar em .env)
        self.key = os.getenv('FERNET_KEY', Fernet.generate_key())
        self.cipher = Fernet(self.key.encode())
    
    def encrypt_token(self, token: str) -> str:
        """Encripta token."""
        encrypted = self.cipher.encrypt(token.encode())
        return encrypted.decode()
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """Desencripta token."""
        decrypted = self.cipher.decrypt(encrypted_token.encode())
        return decrypted.decode()
```

---

## 12. MONITORING DE NOTIFICAÇÕES

### 12.1 Métricas de Notificações

```python
from typing import Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class NotificationMetrics:
    """Métricas de notificações."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.total_sent = 0
        self.total_failed = 0
        self.total_skipped = 0
    
    def start(self):
        """Inicia medição."""
        self.start_time = datetime.now()
    
    def end(self):
        """Termina medição."""
        self.end_time = datetime.now()
    
    def record_sent(self):
        """Registra notificação enviada."""
        self.total_sent += 1
    
    def record_failed(self):
        """Registra notificação falhada."""
        self.total_failed += 1
    
    def record_skipped(self):
        """Registra notificação saltada."""
        self.total_skipped += 1
    
    def get_summary(self) -> Dict:
        """Retorna resumo de métricas."""
        return {
            'duration_seconds': (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0,
            'total_sent': self.total_sent,
            'total_failed': self.total_failed,
            'total_skipped': self.total_skipped,
            'success_rate': (self.total_sent / (self.total_sent + self.total_failed) * 100) if (self.total_sent + self.total_failed) > 0 else 0,
            'throughput_per_second': (self.total_sent / (self.end_time - self.start_time).total_seconds()) if self.start_time and self.end_time and self.total_sent > 0 else 0
        }
```

---

## 13. A/B TESTING DE NOTIFICAÇÕES

### 13.1 Estratégia de A/B Testing

**Variantes:**
- **Control:** Formato actual
- **Variant A:** Formato mais conciso
- **Variant B:** Formato com mais detalhes

### 13.2 Implementação A/B Testing

```python
from typing import Dict
import random
import logging

logger = logging.getLogger(__name__)

class NotificationABTester:
    """A/B testing de formatos de notificação."""
    
    def __init__(self):
        self.variants = ['control', 'variant_a', 'variant_b']
    
    def assign_variant(self, chat_id: str) -> str:
        """Atribui variante a chat_id."""
        # Hash do chat_id para consistência
        hash_value = hash(chat_id) % 100
        
        if hash_value < 33:
            return 'control'
        elif hash_value < 66:
            return 'variant_a'
        else:
            return 'variant_b'
    
    def format_message_by_variant(self, variant: str, listing: Dict, valuation: Dict, score: Dict) -> str:
        """Formata mensagem baseado na variante."""
        if variant == 'control':
            # Formato actual
            return self._format_control(listing, valuation, score)
        elif variant == 'variant_a':
            # Formato mais conciso
            return self._format_variant_a(listing, valuation, score)
        elif variant == 'variant_b':
            # Formato com mais detalhes
            return self._format_variant_b(listing, valuation, score)
```

---

## 14. BEST PRACTICES TELEGRAM

### 14.1 Best Practices

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              BEST PRACTICES TELEGRAM NOTIFICATIONS                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. USAR MARKDOWN (NÃO HTML)                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Markdown é mais seguro e suportado por mais clientes               │   │
│  │ HTML pode ser bloqueado por alguns clientes                           │   │
│  │ Use *bold*, _italic_, `code`                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  2. LIMITAR TAMANHO DA MENSAGEM                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Máximo 4096 caracteres para Markdown                                │   │
│  │ Se exceder, truncar ou dividir em múltiplas mensagens               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  3. USAR EMOJIS PARA DESTACAR INFORMAÇÃO                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 🏠 Imperdível, 🏡 Bom, 🏢 Aceitável, 🏚️ Não recomendado            │   │
│  │ 💰 Preço, 📏 Área, 📍 Localização, 🚇 Metro                           │   │
│  │ 📊 Score, 💡 Rationale, 🔗 Link, 📅 Data                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  4. INCLUIR LINK PARA DASHBOARD                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Permite ao utilizador ver mais detalhes                             │   │
│  │ Use inline links: [texto](url)                                      │   │
│  │ Exemplo: [Ver no Dashboard](http://localhost:8501?listing_id=123)  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  5. RATE LIMITING PARA EVITAR SPAM                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Máximo 5 notificações/dia por chat_id                              │   │
│  │ Máximo 1 notificação/hora por chat_id                               │   │
│  │ Se excedido, não notificar e avisar utilizador                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  6. EVITAR DUPLICAÇÕES                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Verificar se listing já foi notificado nas últimas 24 horas       │   │
│  │ Se sim, não notificar novamente                                      │   │
│  │ Guardar histórico de notificações em database                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  7. ERROR HANDLING ROBUSTO                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  | Tratar erros gracefully (network timeout, bot blocked, etc.)       │   │
│  │ Registar erros para análise                                         │   │
│  | Se muitos erros para um chat_id, desactivar notificações            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  8. USAR WEBHOOKS PARA TEMPO REAL                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Webhooks permitem notificações em tempo real                         │   │
│  | Em vez de polling, Telegram notifica quando há actualização          │   │
│  │ Mais eficiente e rápido                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 15. GLOSSÁRIO DE NOTIFICAÇÕES

```
┌─────────────────────────────────────────────────────────────────────────────┐
│            GLOSSÁRIO DE NOTIFICAÇÕES                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TELEGRAM BOT: Bot automatizado no Telegram                                │
│                                                                             │
│  BOTFATHER: Bot oficial do Telegram para criar bots                      │
│                                                                             │
│  API TOKEN: Token de API para autenticar bot                              │
│                                                                             │
│  CHAT ID: Identificador único de conversa Telegram                         │
│                                                                             │
│  MESSAGE FORMATTER: Componente que formata mensagens                     │
│                                                                             │
│  OPPORTUNITY SELECTOR: Componente que selecciona oportunidades         │
│                                                                             │
│  NOTIFICATION ENGINE: Engine que orquestra envio de notificações      │
│                                                                             │
│  NOTIFICATION HISTORY: Histórico de notificações enviadas               │
│                                                                             │
│  RATE LIMITING: Limitação de taxa de notificações                          │
│                                                                             │
│  WEBHOOK: Endpoint HTTP para notificações em tempo real                  │
│                                                                             │
│  MARKDOWN: Linguagem de formatação de texto                              │
│                                                                             │
│  INLINE BUTTONS: Botões em mensagens Telegram                           │
│                                                                             │
│  PUSH NOTIFICATION: Notificação push em tempo real                        │
│                                                                             │
│  DUPLICATE: Listing já notificado anteriormente                          │
│                                                                             │
│  SPAM: Excesso de notificações                                            │
│                                                                             │
│  FERNET: Biblioteca para encriptação de tokens                           │
│                                                                             │
│  ENVIRONMENT VARIABLES: Variáveis de ambiente (.env)                     │
│                                                                             │
│  A/B TESTING: Teste de diferentes formatos de notificação               │
│                                                                             │
│  VARIANTS: Diferentes versões de notificação (control, variant_a, etc.) │
│                                                                             │
│  METRICS: Métricas de performance de notificações                      │
│                                                                             │
│  SUCCESS RATE: Taxa de sucesso de notificações                           │
│                                                                             │
│  THROUGHPUT: Volume de notificações por segundo                           │
│                                                                             │
│  ERROR HANDLING: Gestão de erros de notificações                         │
│                                                                             │
│  SECURITY: Segurança de tokens e chat_ids                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 16. HARDENING ONDA 4 — FAIL-CLOSED & TELEGRAMBOT ERROR HANDLING

### 16.1 Fail-Closed em `_already_notified_today`

**Problema:**
- Se o DB falha ao verificar se um listing já foi notificado, o sistema assume que não foi notificado
- Isso pode causar spam repetido ao utilizador durante outages de DB
- O utilizador recebe múltiplas notificações do mesmo listing

**Solução:**
- Fail-closed: se o DB falha, assume que já foi notificado
- Log explícito do erro para debugging
- Evita spam em outages

**Implementação:**
```python
# realestate_engine/notification/notification_engine.py
def _already_notified_today(self, listing_id: str) -> bool:
    try:
        notifications = self.repo.get_notifications_for_listing(listing_id)
        today = datetime.now(timezone.utc).date()
        for n in notifications:
            if n.sent_at and n.sent_at.date() == today and n.status == "sent":
                return True
        return False
    except Exception as e:
        logger.error(f"_already_notified_today({listing_id}) lookup failed: {e}; failing closed")
        return True  # Fail-closed: assume already notified to avoid spam
```

### 16.2 Env-Driven Ollama Model em `notify_ai_analysis`

**Problema:**
- `notify_ai_analysis` hardcodava o modelo Ollama como `mistral:7b`
- Não respeitava variáveis de ambiente
- Difícil de configurar para diferentes modelos

**Solução:**
- Usar o padrão do ambiente para o modelo Ollama
- Permitir configuração centralizada via `.env`
- Flexibilidade para testar diferentes modelos

**Implementação:**
```python
# realestate_engine/notification/notification_engine.py
async def notify_ai_analysis(self, limit: int = 3) -> int:
    from realestate_engine.investor_tools.opportunity_analyzer import OpportunityAnalyzer
    try:
        # Usa o padrão do ambiente para o modelo Ollama
        analyzer = OpportunityAnalyzer(provider="ollama")
        deals = await analyzer.get_top_deals_report(limit=limit)
        ...
```

### 16.3 TelegramBot Error Handling (Onda 4)

**Problema:**
- Tratamento genérico de erros Telegram
- Sem distinção entre erros transitórios e permanentes
- Sem respeitar rate limits específicos (RetryAfter)
- Erros de autenticação não tratados adequadamente

**Solução:**
- Tratamento específico por tipo de erro
- Respeitar RetryAfter (429) com sleep limitado
- Logar erros permanentes (Forbidden, InvalidToken) sem retry
- Distinguir erros transitórios (TimedOut, NetworkError) para retry externo
- Stubs para erros quando python-telegram-bot ausente

**Implementação:**
```python
# realestate_engine/notification/telegram_bot.py
from telegram.error import RetryAfter, Forbidden, InvalidToken, BadRequest, TimedOut, NetworkError

class TelegramBot:
    MAX_RETRY_AFTER_S = 60  # Cap de 60 segundos para RetryAfter
    
    async def send_message(self, message: str) -> Optional[str]:
        try:
            msg = await self._bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            return str(msg.message_id)
            
        except RetryAfter as e:
            # Respeita RetryAfter com cap
            wait = min(int(getattr(e, "retry_after", 1) or 1), self.MAX_RETRY_AFTER_S)
            logger.warning(f"Telegram rate limited, waiting {wait}s")
            await asyncio.sleep(wait)
            # Retry após sleep (handled by caller)
            
        except (Forbidden, InvalidToken) as e:
            # Erros permanentes: log loud, sem retry
            logger.error(f"Telegram auth error (no retry): {e}")
            return None
            
        except BadRequest as e:
            # Erros de formatação Markdown: log loud, sem retry
            logger.error(f"Telegram bad request (no retry): {e}")
            return None
            
        except (TimedOut, NetworkError) as e:
            # Erros transitórios: log warning, retry externo
            logger.warning(f"Telegram transient error (retry): {e}")
            # Caller deve retry
            
        except Exception as e:
            # Erros desconhecidos: log error
            logger.error(f"Telegram unexpected error: {e}")
            return None
```

### 16.4 Benefícios

**Robustez:**
- Fail-closed evita spam em outages
- Tratamento específico de erros Telegram reduz falsos positivos
- Env-driven Ollama permite flexibilidade de configuração

**Experiência do Utilizador:**
- Menos spam durante outages
- Notificações mais confiáveis
- Configuração centralizada

**Debugging:**
- Logs estruturados por tipo de erro
- Fácil identificar problemas de autenticação
- Fácil identificar problemas de rate limiting

---

*Fim do Documento 09 — Notificações Telegram*
