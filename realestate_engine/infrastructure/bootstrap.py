"""End-to-end bootstrap / healthcheck for a real production deployment.

Run after `docker compose up -d postgres redis` to verify:
  1. PostgreSQL is reachable and schema is up.
  2. Redis is reachable (cache + rate-limit).
  3. Telegram bot credentials work against the live API.
  4. Residential proxy is configured.

Every check is REAL — no mocks, no fallbacks that silently pass.
Exit code 0 = all green, >0 = number of failed checks.

Usage:
    python -m realestate_engine.infrastructure.bootstrap
"""
from __future__ import annotations

import asyncio
import sys

from loguru import logger

from realestate_engine.database.models import init_db
from realestate_engine.database.repository import DatabaseRepository
from realestate_engine.infrastructure.redis_client import get_redis
from realestate_engine.notification.notification_engine import NotificationEngine
from realestate_engine.utils.config import config


def check_postgres() -> bool:
    if config.database_url.startswith("sqlite"):
        logger.error("❌ DATABASE_URL still points to SQLite — refuse to run in prod mode")
        return False
    try:
        init_db()
        repo = DatabaseRepository()
        with repo.Session() as session:
            session.execute(__import__("sqlalchemy").text("SELECT 1"))
        logger.info(f"✅ PostgreSQL reachable at {config.database_url.split('@')[-1]}")
        return True
    except Exception as e:
        logger.error(f"❌ PostgreSQL unreachable: {e}")
        return False


def check_redis() -> bool:
    r = get_redis()
    if r.healthy():
        logger.info(f"✅ Redis healthy at {config.redis_url}")
        return True
    logger.error(f"❌ Redis not healthy at {config.redis_url}")
    return False


def check_proxy() -> bool:
    if config.residential_proxy_url or config.proxy_list:
        logger.info("✅ Residential proxy configured")
        return True
    logger.error(
        "❌ RESIDENTIAL_PROXY_URL and PROXY_LIST are both empty — "
        "Idealista/Imovirtual will be blocked in production"
    )
    return False


async def check_telegram() -> bool:
    if not config.telegram_bot_token or not config.telegram_chat_id:
        logger.error("❌ Telegram not configured (missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID)")
        return False
    engine = NotificationEngine()
    ok = await engine.healthcheck()
    if ok:
        logger.info("✅ Telegram bot healthcheck OK (message sent)")
    else:
        logger.error("❌ Telegram healthcheck failed — token/chat invalid or network down")
    return ok


async def main() -> int:
    logger.info("=" * 72)
    logger.info("Real Estate Engine — production bootstrap")
    logger.info("=" * 72)

    results = {
        "postgres": check_postgres(),
        "redis": check_redis(),
        "proxy": check_proxy(),
        "telegram": await check_telegram(),
    }

    failed = [k for k, v in results.items() if not v]
    if not failed:
        logger.info("🎉 All checks passed — system is ready for real scraping")
        return 0
    logger.error(f"❌ {len(failed)} checks failed: {failed}")
    logger.error("Fix the failing checks before starting the scheduler.")
    return len(failed)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
