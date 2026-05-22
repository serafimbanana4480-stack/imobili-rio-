"""Session management for persisting cookies and trust score.

Enhanced with distributed session persistence using Redis for horizontal scalability.
"""
import json
import os
from typing import Dict, Optional
from loguru import logger

from realestate_engine.infrastructure.redis_client import get_redis

class SessionManager:
    """Saves and restores browser session state (cookies, localStorage).

    Supports both local file storage and distributed Redis storage.
    Redis is used when available, falling back to file storage for compatibility.
    """

    SESSION_TTL = 3600  # 1 hour

    def __init__(self, session_dir: str = "data/sessions", use_redis: bool = True):
        self.session_dir = session_dir
        os.makedirs(session_dir, exist_ok=True)
        self.use_redis = use_redis
        self.redis = get_redis() if use_redis else None
        
    def _get_path(self, portal_name: str) -> str:
        return os.path.join(self.session_dir, f"{portal_name}_session.json")
        
    async def save_session(self, tab, portal_name: str):
        """Extract and save current session state to Redis or file."""
        try:
            # Nodriver doesn't have direct cookie access in high-level API yet?
            # We use CDP directly via evaluate
            cookies = await tab.evaluate("document.cookie")
            storage = await tab.evaluate("JSON.stringify(localStorage)")

            state = {
                "cookies": cookies,
                "localStorage": storage,
                "timestamp": json.dumps({"value": None})  # Placeholder for timestamp
            }

            # Try Redis first if enabled
            if self.redis:
                try:
                    key = f"session:{portal_name}"
                    await self.redis.setex(key, self.SESSION_TTL, json.dumps(state))
                    logger.debug(f"[{portal_name}] Session state saved to Redis")
                    return
                except Exception as e:
                    logger.warning(f"Redis save failed, falling back to file: {e}")

            # Fallback to file storage
            with open(self._get_path(portal_name), "w") as f:
                json.dump(state, f)
            logger.debug(f"[{portal_name}] Session state saved to file")
        except Exception as e:
            logger.warning(f"Failed to save session for {portal_name}: {e}")

    async def restore_session(self, tab, portal_name: str):
        """Inject saved session state into tab from Redis or file."""
        state = None

        # Try Redis first if enabled
        if self.redis:
            try:
                key = f"session:{portal_name}"
                data = await self.redis.get(key)
                if data:
                    state = json.loads(data)
                    logger.debug(f"[{portal_name}] Session state loaded from Redis")
            except Exception as e:
                logger.warning(f"Redis load failed, falling back to file: {e}")

        # Fallback to file storage
        if state is None:
            path = self._get_path(portal_name)
            if not os.path.exists(path):
                logger.debug(f"[{portal_name}] No session found")
                return

            try:
                with open(path, "r") as f:
                    state = json.load(f)
                logger.debug(f"[{portal_name}] Session state loaded from file")
            except Exception as e:
                logger.warning(f"Failed to load session file for {portal_name}: {e}")
                return

        # Restore session state
        try:
            if state.get("cookies"):
                # Basic cookie restoration via JS (limited to current domain)
                cookies = state["cookies"]
                if cookies:
                    for cookie in cookies.split("; "):
                        if cookie.strip():
                            await tab.evaluate(f"document.cookie = '{cookie}'")

            if state.get("localStorage"):
                storage = state["localStorage"]
                if storage:
                    await tab.evaluate(f"const data = JSON.parse('{storage}'); Object.keys(data).forEach(k => localStorage.setItem(k, data[k]));")

            logger.info(f"[{portal_name}] Session state restored")
        except Exception as e:
            logger.warning(f"Failed to restore session for {portal_name}: {e}")

    async def delete_session(self, portal_name: str):
        """Delete session from both Redis and file storage."""
        # Delete from Redis
        if self.redis:
            try:
                key = f"session:{portal_name}"
                await self.redis.delete(key)
                logger.debug(f"[{portal_name}] Session deleted from Redis")
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}")

        # Delete from file
        path = self._get_path(portal_name)
        if os.path.exists(path):
            try:
                os.remove(path)
                logger.debug(f"[{portal_name}] Session file deleted")
            except Exception as e:
                logger.warning(f"Failed to delete session file: {e}")
