"""Regression tests for Onda 2 (macOS parity + cleanup).

Pin the launcher parity and the new root .gitignore so they cannot silently
drift. The user's primary value here is being able to onboard a teammate or
reviewer on a non-Windows machine without doing the manual venv dance.
"""
from __future__ import annotations

import pathlib
import re
import stat

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
START_BAT = REPO_ROOT / "start.bat"
START_SH = REPO_ROOT / "start.sh"
ROOT_GITIGNORE = REPO_ROOT / ".gitignore"


# ── Launcher parity ────────────────────────────────────────────────────────


def test_start_sh_exists():
    assert START_SH.exists(), "start.sh must exist for macOS / Linux parity."


def test_start_sh_has_shebang():
    first_line = START_SH.read_text(encoding="utf-8").splitlines()[0]
    assert first_line.startswith("#!"), (
        f"start.sh must begin with a shebang, got: {first_line!r}"
    )
    assert "bash" in first_line.lower()


def test_start_sh_implements_every_start_bat_command():
    """Every dispatcher branch in start.bat must have an equivalent in start.sh."""
    bat_text = START_BAT.read_text(encoding="utf-8", errors="replace")
    # start.bat dispatches via lines like:
    #   if /i "%CMD%"=="install"   goto :install
    bat_commands = set(re.findall(r'"%CMD%"=="(\w+)"', bat_text))
    # Drop "menu" — it's the implicit default; both launchers handle it.
    bat_commands.discard("menu")
    assert bat_commands, "Failed to parse start.bat commands."

    sh_text = START_SH.read_text(encoding="utf-8")
    # start.sh dispatches via a case statement: `install)` etc.
    sh_dispatch_block = re.search(r"case\s+\"\$CMD\"\s+in(.*?)esac", sh_text, re.DOTALL)
    assert sh_dispatch_block, "start.sh missing case dispatcher block"
    # Each arm looks like: "  install)" or "  help|-h|--help)" — extract every
    # alternative so multi-token arms still register as paritary.
    sh_commands: set[str] = set()
    for arm in re.findall(r"^\s*([\w|\-]+)\)", sh_dispatch_block.group(1), re.MULTILINE):
        for token in arm.split("|"):
            token = token.lstrip("-").strip()
            if token:
                sh_commands.add(token)

    missing = bat_commands - sh_commands
    assert not missing, (
        f"start.sh is missing commands present in start.bat: {sorted(missing)}. "
        "Keep the two launchers paritary."
    )


def test_start_launchers_expose_rapid_and_full_modes():
    """The launcher contract must include the new intelligent rapid mode."""
    bat_text = START_BAT.read_text(encoding="utf-8", errors="replace")
    sh_text = START_SH.read_text(encoding="utf-8")

    for token in ["rapid", "full"]:
        assert token in bat_text, f"start.bat must expose {token} mode"
        assert token in sh_text, f"start.sh must expose {token} mode"


def test_rapid_mode_uses_orchestrator_pipeline():
    """Rapid mode should use the orchestrator's rapid pipeline, not legacy entry points."""
    bat_text = START_BAT.read_text(encoding="utf-8", errors="replace")
    sh_text = START_SH.read_text(encoding="utf-8")

    assert "run_rapid_pipeline" in bat_text
    assert "run_rapid_pipeline" in sh_text
    assert "single_best_scheduler" not in bat_text
    assert "single_best_scheduler" not in sh_text


def test_start_sh_uses_canonical_test_path():
    """Both launchers must invoke pytest against tests/ (the curated suite)."""
    sh_text = START_SH.read_text(encoding="utf-8")
    bat_text = START_BAT.read_text(encoding="utf-8", errors="replace")
    assert "pytest tests/" in sh_text
    assert "pytest tests/" in bat_text


# ── .gitignore at repo root ────────────────────────────────────────────────


def test_root_gitignore_exists():
    assert ROOT_GITIGNORE.exists(), (
        "Repo root must have a .gitignore. Without it, secrets, venvs, and "
        "logs end up committed on first push."
    )


def test_root_gitignore_excludes_critical_paths():
    text = ROOT_GITIGNORE.read_text(encoding="utf-8")
    required = [
        ".env",                # secrets
        "venv312/",            # Windows venv
        "__pycache__/",        # Python bytecode
        "logs/",               # rotation noise
        "data/cache/",         # regenerable
        "scripts/debug/",      # one-off debug probes (Onda 2 cleanup)
        "*.db",                # local SQLite
        ".streamlit/secrets.toml",  # never commit
    ]
    missing = [p for p in required if p not in text]
    assert not missing, (
        f"Root .gitignore missing entries: {missing}. These leak secrets or "
        f"bloat the repo if committed."
    )


def test_root_gitignore_keeps_env_example():
    """`.env` ignored, `.env.example` MUST be tracked (negation)."""
    text = ROOT_GITIGNORE.read_text(encoding="utf-8")
    assert "!.env.example" in text, (
        ".env.example must be force-included so contributors know which "
        "variables to fill."
    )
