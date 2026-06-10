"""Cross-platform Chrome/Chromium auto-detection for Nodriver spiders.

Resolution order:
1. Env var ``REE_CHROME_PATH`` (explicit override)
2. Common install locations per OS (Windows / macOS / Linux)
3. ``shutil.which`` fallback for typical binaries

Raises a clear ``BrowserNotFoundError`` with install hints when nothing is found.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import List, Optional


class BrowserNotFoundError(RuntimeError):
    """Raised when no Chrome/Chromium binary can be located for Nodriver."""


_WINDOWS_CANDIDATES: List[str] = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Chromium\Application\chrome.exe",
    r"%LOCALAPPDATA%\Chromium\Application\chrome.exe",
]

_MACOS_CANDIDATES: List[str] = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    str(Path.home() / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
]

_LINUX_CANDIDATES: List[str] = [
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/snap/bin/chromium",
    "/opt/google/chrome/chrome",
]

_WHICH_NAMES: List[str] = [
    "chrome",
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "msedge",
]

_INSTALL_HINT = (
    "Nenhum Chrome/Chromium encontrado. Instala uma das opções:\n"
    "  • Windows: https://www.google.com/chrome/ ou winget install Google.Chrome\n"
    "  • macOS:   brew install --cask google-chrome\n"
    "  • Linux:   apt install chromium-browser  (ou google-chrome-stable)\n"
    "Ou define a variável de ambiente REE_CHROME_PATH com o caminho absoluto."
)


def _expand(path: str) -> str:
    return os.path.expandvars(os.path.expanduser(path))


def _platform_candidates() -> List[str]:
    if sys.platform.startswith("win"):
        return _WINDOWS_CANDIDATES
    if sys.platform == "darwin":
        return _MACOS_CANDIDATES
    return _LINUX_CANDIDATES


def find_browser() -> Optional[str]:
    """Return a usable browser path or ``None`` if nothing is found."""
    override = os.environ.get("REE_CHROME_PATH")
    if override:
        expanded = _expand(override)
        if Path(expanded).is_file():
            return expanded
        return None

    for candidate in _platform_candidates():
        expanded = _expand(candidate)
        if Path(expanded).is_file():
            return expanded

    for name in _WHICH_NAMES:
        path = shutil.which(name)
        if path:
            return path

    return None


def require_browser() -> str:
    """Return a browser path or raise ``BrowserNotFoundError`` with install hints."""
    path = find_browser()
    if not path:
        override = os.environ.get("REE_CHROME_PATH")
        if override:
            raise BrowserNotFoundError(
                f"REE_CHROME_PATH aponta para um caminho inválido: {override!r}\n{_INSTALL_HINT}"
            )
        raise BrowserNotFoundError(_INSTALL_HINT)
    return path
