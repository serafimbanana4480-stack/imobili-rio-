"""Runtime compatibility shims for the project.

This module is imported automatically by Python when present on `sys.path`.
It backfills newer stdlib symbols that the codebase expects so the launcher can
run on Python 3.9 without rewriting every import site.
"""

import datetime as _datetime

if not hasattr(_datetime, "UTC"):
    _datetime.UTC = _datetime.timezone.utc
