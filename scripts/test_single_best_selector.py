"""Test script for single best opportunity selector.

Tests:
1. Selection logic with existing database data
2. Message formatting with full details
3. Telegram message sending
"""
import sys
import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realestate_engine.notification.best_opportunity_selector import BestOpportunitySelector
from realestate_engine.notification.message_formatter import MessageFormatter
from realestate_engine.notification.telegram_bot import TelegramBot
from loguru import logger


def test_selection():
    """Test selection logic with existing database data."""
    logger.info("=" * 60)
    logger.info("TEST 1: Selection Logic")
    logger.info("=" * 60)

    selector = BestOpportunitySelector()

    # Select single best opportunity
    best = selector.select_single_best(min_score=6.0)  # Lower threshold for testing

    if best:
        listing = best["listing"]
        score = best["score"]

        logger.info(f"✅ Selected opportunity:")
        logger.info(f"   ID: {listing.id}")
        logger.info(f"   Title: {listing.titulo}")
        logger.info(f"   Price: {listing.preco_pedido:,.0f}€")
        logger.info(f"   Score: {score.score_total:.1f}/10")
        logger.info(f"   Classification: {score.classificacao}")
        logger.info(f"   Composite Score: {best.get('composite_score', 'N/A')}")

        if listing.valuations:
            val = listing.valuations[0]
            logger.info(f"   Discount: {val.discount * 100:.1f}%")
            logger.info(f"   Fair Value: {val.valor_justo:,.0f}€")

        return best
    else:
        logger.warning("❌ No opportunity selected")
        return None


def test_message_formatting(best_opportunity):
    """Test message formatting with full details."""
    logger.info("=" * 60)
    logger.info("TEST 2: Message Formatting")
    logger.info("=" * 60)

    if not best_opportunity:
        logger.error("❌ No opportunity to format")
        return None

    formatter = MessageFormatter()

    # Format message
    message = formatter.format_single_best_opportunity(best_opportunity)

    logger.info(f"✅ Message generated")
    logger.info(f"   Length: {len(message)} characters")
    logger.info(f"   Lines: {len(message.split(chr(10)))}")

    # Print message preview
    logger.info("\n--- MESSAGE PREVIEW ---")
    print(message)
    logger.info("--- END PREVIEW ---\n")

    return message


def test_telegram_sending(message):
    """Test Telegram message sending."""
    logger.info("=" * 60)
    logger.info("TEST 3: Telegram Sending")
    logger.info("=" * 60)

    if not message:
        logger.error("❌ No message to send")
        return False

    bot = TelegramBot()

    logger.info(f"Token configured: {'✅' if bot.token else '❌'}")
    logger.info(f"Chat ID configured: {'✅' if bot.chat_id else '❌'}")

    if not bot.chat_id:
        logger.error("❌ Chat ID not configured, skipping Telegram test")
        return False

    logger.info("Sending message to Telegram...")
    msg_id = None

    async def send():
        nonlocal msg_id
        msg_id = await bot.send_message(message)

    import asyncio
    asyncio.run(send())

    if msg_id:
        logger.info(f"✅ Message sent successfully (ID: {msg_id})")
        return True
    else:
        logger.error("❌ Failed to send message")
        return False


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
