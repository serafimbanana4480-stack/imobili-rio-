"""Spider configuration dataclass - fixes LSP violation in SpiderManager."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SpiderConfig:
    """Configuration for spider execution.

    Replaces ad-hoc kwargs in SpiderManager.run_all_cycle().
    Browser-based spiders use headless; direct-fetch spiders ignore it.
    """

    max_pages: int = 5
    headless: bool = True
    proxy: Optional[str] = None
    timeout: int = 30
    user_agent: Optional[str] = None
