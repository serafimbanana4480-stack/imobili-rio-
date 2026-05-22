"""Test script for single best opportunity selector.

Tests:
1. Selection logic with existing database data
2. Message formatting with full details
3. Telegram message sending
"""
import sys
import os
import asyncio
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Override to use SQLite for testing
os.environ["DATABASE_URL"] = "sqlite:///data/db/realestate.db"

from realestate_engine.notification.best_opportunity_selector import BestOpportunitySelector
from realestate_engine.notification.message_formatter import MessageFormatter
from realestate_engine.notification.telegram_bot import TelegramBot
from loguru import logger


import pytest

@pytest.fixture
def best_opportunity():
    """Fixture que seleciona a melhor oportunidade."""
    logger.info("=" * 60)
    logger.info("TEST 1: Selection Logic")
    logger.info("=" * 60)

    selector = BestOpportunitySelector()

    # Select single best opportunity
    best = selector.select_single_best(min_score=6.0)

    if best:
        listing = best["listing"]
        score = best["score"]

        logger.info(f"✅ Selected opportunity:")
        logger.info(f"   ID: {listing.id}")
        logger.info(f"   Title: {listing.titulo}")
        logger.info(f"   Price: {listing.preco_pedido:,.0f}€")
        logger.info(f"   Score: {score.score_total:.1f}/10")
        logger.info(f"   Classification: {score.classificacao}")

        if listing.valuations:
            val = listing.valuations[0]
            logger.info(f"   Discount: {val.discount * 100:.1f}%")
            logger.info(f"   Fair Value: {val.valor_justo:,.0f}€")

        return best
    else:
        logger.warning("❌ No opportunity selected")
        pytest.skip("No opportunity available in database for testing")


def test_selection(best_opportunity):
    """Test selection logic with existing database data."""
    assert best_opportunity is not None
    assert best_opportunity["listing"] is not None
    assert best_opportunity["score"] is not None


def test_message_formatting(best_opportunity):
    """Test message formatting with full details."""
    logger.info("=" * 60)
    logger.info("TEST 2: Message Formatting")
    logger.info("=" * 60)

    assert best_opportunity is not None

    formatter = MessageFormatter()

    # Format message
    message = formatter.format_single_best_opportunity(best_opportunity)

    logger.info(f"✅ Message generated")
    logger.info(f"   Length: {len(message)} characters")

    assert message is not None
    assert len(message) > 0

    return message


def test_telegram_sending(best_opportunity):
    """Test Telegram message sending."""
    logger.info("=" * 60)
    logger.info("TEST 3: Telegram Sending")
    logger.info("=" * 60)

    assert best_opportunity is not None

    formatter = MessageFormatter()
    message = formatter.format_single_best_opportunity(best_opportunity)

    bot = TelegramBot(token="", chat_id="")

    # Se não há configuração, deve retornar None sem erro
    result = asyncio.run(bot.send_message(message))
    assert result is None


def main():
    """Run all tests."""
    logger.info("Starting Single Best Opportunity Selector Tests")
    logger.info("")

    # Test 1: Selection
    best_opportunity = test_selection()
    if not best_opportunity:
        logger.error("Selection test failed, aborting")
        return

    logger.info("")

    # Test 2: Message Formatting
    message = test_message_formatting(best_opportunity)
    if not message:
        logger.error("Message formatting test failed, aborting")
        return

    logger.info("")

    # Test 3: Telegram Sending
    test_telegram_sending(message)

    logger.info("")
    logger.info("=" * 60)
    logger.info("ALL TESTS COMPLETED")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
