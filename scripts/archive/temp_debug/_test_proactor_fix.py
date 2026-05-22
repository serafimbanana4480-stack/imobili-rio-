"""Test ProactorEventLoop fix for Windows asyncio subprocess support.

This test simulates what nodriver does (asyncio.create_subprocess_exec) to verify
the ProactorEventLoop policy fix works on Windows.

Run: ``venv312\\Scripts\\python.exe scripts\\debug\\_test_proactor_fix.py``
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from realestate_engine.dashboard.views.scraping_results import _run_async


async def test_subprocess_echo():
    """Test async subprocess with a simple echo command."""
    if sys.platform == "win32":
        # Windows: use cmd /c echo
        proc = await asyncio.create_subprocess_exec(
            "cmd", "/c", "echo", "ProactorEventLoop works!",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    else:
        # Unix: use echo
        proc = await asyncio.create_subprocess_exec(
            "echo", "ProactorEventLoop works!",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    
    stdout, stderr = await proc.communicate()
    return stdout.decode().strip(), proc.returncode


def main() -> int:
    print(f"Platform: {sys.platform}")
    print("Testing _run_async with subprocess...")
    
    try:
        output, returncode = _run_async(test_subprocess_echo())
        print(f"✅ Success! Output: {output!r}")
        print(f"   Return code: {returncode}")
        return 0
    except NotImplementedError as e:
        print(f"❌ NotImplementedError (ProactorEventLoop not working): {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
