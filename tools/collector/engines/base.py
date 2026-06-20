"""Engine ABC — browser/HTTP lifecycle contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Engine(ABC):
    """Minimal interface every collection engine must satisfy."""

    @abstractmethod
    async def start(self) -> None:
        """Launch browser or open HTTP session."""

    @abstractmethod
    async def navigate(self, url: str) -> Any:
        """Navigate to *url* and return a page/response handle."""

    @abstractmethod
    async def evaluate(self, page: Any, expression: str) -> Any:
        """Run *expression* in the page context and return parsed JSON."""

    @abstractmethod
    async def stop(self) -> None:
        """Tear down browser or HTTP session."""
