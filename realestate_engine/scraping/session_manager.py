"""Session management for persisting cookies and trust score."""
import json
import os
from typing import Dict, Optional
from loguru import logger

class SessionManager:
    """Saves and restores browser session state (cookies, localStorage)."""
    
    def __init__(self, session_dir: str = "data/sessions"):
        self.session_dir = session_dir
        os.makedirs(session_dir, exist_ok=True)
        
    def _get_path(self, portal_name: str) -> str:
        return os.path.join(self.session_dir, f"{portal_name}_session.json")
        
    async def save_session(self, tab, portal_name: str):
        """Extract and save current session state."""
        try:
            # Nodriver doesn't have direct cookie access in high-level API yet? 
            # We use CDP directly via evaluate
            cookies = await tab.evaluate("document.cookie")
            storage = await tab.evaluate("JSON.stringify(localStorage)")
            
            state = {
                "cookies": cookies,
                "localStorage": storage
            }
            
            with open(self._get_path(portal_name), "w") as f:
                json.dump(state, f)
            logger.debug(f"[{portal_name}] Session state saved")
        except Exception as e:
            logger.warning(f"Failed to save session for {portal_name}: {e}")

    async def restore_session(self, tab, portal_name: str):
        """Inject saved session state into tab."""
        path = self._get_path(portal_name)
        if not os.path.exists(path):
            return
            
        try:
            with open(path, "r") as f:
                state = json.load(f)
                
            if state.get("cookies"):
                # Basic cookie restoration via JS (limited to current domain)
                for cookie in state["cookies"].split("; "):
                    # Escape single quotes to prevent XSS injection
                    safe_cookie = cookie.replace("'", "\\'")
                    await tab.evaluate(f"document.cookie = '{safe_cookie}'")
            
            if state.get("localStorage"):
                safe_storage = json.dumps(state["localStorage"]).replace("'", "\\'")
                await tab.evaluate(f"const data = JSON.parse('{safe_storage}'); Object.keys(data).forEach(k => localStorage.setItem(k, data[k]));")
                
            logger.info(f"[{portal_name}] Session state restored")
        except Exception as e:
            logger.warning(f"Failed to restore session for {portal_name}: {e}")
