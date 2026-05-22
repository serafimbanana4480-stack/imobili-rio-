"""Tests for cross-platform Chrome auto-detection used by Nodriver spiders."""
import os
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from realestate_engine.scraping import browser_resolver as br


def test_env_override_used_when_valid(tmp_path, monkeypatch):
    fake = tmp_path / "chrome.exe"
    fake.write_text("")
    monkeypatch.setenv("REE_CHROME_PATH", str(fake))
    assert br.find_browser() == str(fake)


def test_env_override_invalid_returns_none(monkeypatch, tmp_path):
    monkeypatch.setenv("REE_CHROME_PATH", str(tmp_path / "does-not-exist.exe"))
    monkeypatch.setattr(br, "_platform_candidates", lambda: [])
    monkeypatch.setattr(br.shutil, "which", lambda *_: None)
    assert br.find_browser() is None


def test_require_browser_raises_with_hint(monkeypatch):
    monkeypatch.delenv("REE_CHROME_PATH", raising=False)
    monkeypatch.setattr(br, "_platform_candidates", lambda: [])
    monkeypatch.setattr(br.shutil, "which", lambda *_: None)
    with pytest.raises(br.BrowserNotFoundError) as exc:
        br.require_browser()
    assert "REE_CHROME_PATH" in str(exc.value)


def test_require_browser_raises_when_override_invalid(monkeypatch, tmp_path):
    monkeypatch.setenv("REE_CHROME_PATH", str(tmp_path / "missing.exe"))
    monkeypatch.setattr(br, "_platform_candidates", lambda: [])
    monkeypatch.setattr(br.shutil, "which", lambda *_: None)
    with pytest.raises(br.BrowserNotFoundError) as exc:
        br.require_browser()
    assert "inválido" in str(exc.value)


def test_candidate_lookup_finds_existing_file(tmp_path, monkeypatch):
    monkeypatch.delenv("REE_CHROME_PATH", raising=False)
    fake = tmp_path / "chromium"
    fake.write_text("")
    monkeypatch.setattr(br, "_platform_candidates", lambda: [str(fake)])
    monkeypatch.setattr(br.shutil, "which", lambda *_: None)
    assert br.find_browser() == str(fake)


def test_which_fallback(tmp_path, monkeypatch):
    monkeypatch.delenv("REE_CHROME_PATH", raising=False)
    fake = tmp_path / "google-chrome"
    fake.write_text("")
    monkeypatch.setattr(br, "_platform_candidates", lambda: [])
    monkeypatch.setattr(br.shutil, "which", lambda name: str(fake) if name == "google-chrome" else None)
    assert br.find_browser() == str(fake)
