"""Regression tests for Onda 4 (24h robustness + Telegram hardening).

These pin the production hardening so a refactor cannot silently undo:

- A: APScheduler hardening (max_instances, coalesce, misfire_grace_time,
     event listener) — without these, a slow pipeline either piles up
     overlapping runs or silently drops triggers.
- B: ``notify_ai_analysis`` must respect ``OLLAMA_MODEL`` (regression of B3
     in a different file). Hardcoding mistral:7b here meant the
     dashboard's ``.env`` change never reached scheduled Telegram sends.
- D: ``_already_notified_today`` must fail-closed, not fail-open. A flaky
     DB used to spam users; now we suppress.
- E: ``TelegramBot.send_message`` must distinguish auth/network/rate-limit
     errors so terminal failures stop retrying immediately.
"""
from __future__ import annotations

import inspect
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ORCHESTRATOR = REPO_ROOT / "realestate_engine" / "scheduler" / "orchestrator.py"
NOTIFICATION_ENGINE = REPO_ROOT / "realestate_engine" / "notification" / "notification_engine.py"
TELEGRAM_BOT = REPO_ROOT / "realestate_engine" / "notification" / "telegram_bot.py"


# ── A: orchestrator hardening ────────────────────────────────────────────


def _orchestrator_source() -> str:
    return ORCHESTRATOR.read_text(encoding="utf-8")


def _add_job_block_for(src: str, job_id: str) -> str:
    """Return the ~500-char window surrounding the add_job() call for ``job_id``.

    Naive ``[^)]*`` regex fails because inner ``CronTrigger(...)`` contains
    its own parentheses; instead we grab a context window which is good
    enough for asserting kwargs are present.
    """
    needle = f'id="{job_id}"'
    idx = src.find(needle)
    assert idx != -1, f"Missing id={needle!r} in orchestrator source."
    return src[max(0, idx - 400):idx + 400]


def test_orchestrator_full_pipeline_uses_max_instances_one():
    body = _add_job_block_for(_orchestrator_source(), "full_pipeline")
    assert "max_instances=1" in body, (
        "full_pipeline must set max_instances=1 to prevent overlap when a run "
        "exceeds the trigger interval."
    )
    assert "coalesce=True" in body, (
        "full_pipeline must coalesce missed triggers into a single catch-up run."
    )
    assert "misfire_grace_time" in body, (
        "full_pipeline must tolerate clock drift / suspend via misfire_grace_time."
    )


def test_orchestrator_daily_summary_uses_max_instances_one():
    body = _add_job_block_for(_orchestrator_source(), "daily_summary")
    assert "max_instances=1" in body
    assert "coalesce=True" in body


def test_orchestrator_wires_apscheduler_event_listener():
    """Without an event listener, missed/dropped jobs are invisible."""
    src = _orchestrator_source()
    assert "EVENT_JOB_MISSED" in src
    assert "EVENT_JOB_MAX_INSTANCES" in src
    assert "EVENT_JOB_ERROR" in src
    assert "add_listener" in src, (
        "Orchestrator must register at least one APScheduler event listener "
        "so 24h health is observable from logs alone."
    )
    assert "apscheduler.event=" in src, (
        "Listener must emit grep-friendly structured logs prefixed with "
        "'apscheduler.event=' for production troubleshooting."
    )


# ── B: env-driven Ollama in notification path ────────────────────────────


def test_notify_ai_analysis_does_not_hardcode_model():
    """Scheduled Telegram AI sends must inherit OLLAMA_MODEL from env."""
    src = NOTIFICATION_ENGINE.read_text(encoding="utf-8")
    func_match = re.search(
        r"async def notify_ai_analysis\b.*?(?=\n    async def|\n    def |\Z)",
        src,
        re.DOTALL,
    )
    assert func_match, "notify_ai_analysis function not found"
    body = func_match.group(0)
    assert 'model="mistral:7b"' not in body, (
        "notify_ai_analysis must NOT hardcode model='mistral:7b'. "
        "The OpportunityAnalyzer reads OLLAMA_MODEL from env (Onda 1 fix B3); "
        "passing model= here defeats that single-source-of-truth contract."
    )
    assert 'model=' not in body or 'os.environ' in body, (
        "If a model kwarg is passed, it must come from the environment, "
        "not from a hardcoded literal."
    )


# ── D: fail-closed dedup ────────────────────────────────────────────────


def test_already_notified_today_fails_closed_on_db_error(monkeypatch):
    """If the DB lookup raises, treat the listing as already-notified.

    Verifies the actual runtime behaviour (not just source inspection) by
    monkey-patching the repo to raise.
    """
    from realestate_engine.notification import notification_engine as ne

    # Build an instance without touching the real DB constructor — the
    # constructor only stores attrs; we can swap repo straight away.
    eng = ne.NotificationEngine.__new__(ne.NotificationEngine)
    class _BoomRepo:
        def get_notifications_for_listing(self, _id):
            raise RuntimeError("simulated DB outage")
    eng.repo = _BoomRepo()

    result = eng._already_notified_today("listing-123")
    assert result is True, (
        "When the dedup lookup fails, _already_notified_today must return "
        "True (fail-closed) so we don't spam the user. "
        "See notification_engine.py docstring."
    )


# ── E: TelegramBot rate-limit + auth handling ───────────────────────────


def test_telegram_bot_imports_specific_error_classes():
    """The bot must distinguish RetryAfter / Forbidden / etc. from generic errors."""
    src = TELEGRAM_BOT.read_text(encoding="utf-8")
    for cls in ("RetryAfter", "Forbidden", "InvalidToken", "TimedOut", "NetworkError", "BadRequest"):
        assert cls in src, (
            f"telegram_bot.py must handle {cls!r} explicitly; without it the "
            "send loop cannot distinguish transient from permanent failures."
        )


def test_telegram_bot_honours_retry_after_with_cap():
    """Rate-limit handling must wait the server-provided window but bounded."""
    src = TELEGRAM_BOT.read_text(encoding="utf-8")
    assert "MAX_RETRY_AFTER_S" in src, (
        "There must be a cap on how long we honour Retry-After. "
        "Otherwise a malicious or misconfigured server could pin the engine."
    )
    assert "retry_after" in src
    assert "asyncio.sleep" in src
