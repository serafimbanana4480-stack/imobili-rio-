"""Async helpers for dashboard views.

Provides a robust way to run async coroutines from Streamlit's synchronous
callback context.  The Windows variant uses ProactorEventLoop so that
subprocess-based spiders (nodriver / asyncio.create_subprocess_exec) work
correctly.
"""
import asyncio
import sys


def _run_async(coro):
    """Run async work from Streamlit without leaking the event loop.

    On Windows, configures ProactorEventLoop to enable subprocess support
    required by nodriver's Chrome launcher (asyncio.create_subprocess_exec).
    """
    if sys.platform == "win32":
        # Windows requires ProactorEventLoop for subprocess support
        original_policy = asyncio.get_event_loop_policy()
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        try:
            return asyncio.run(coro)
        finally:
            asyncio.set_event_loop_policy(original_policy)
    else:
        return asyncio.run(coro)
