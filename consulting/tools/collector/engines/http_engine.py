"""HTTP engine — for API endpoints with no WAF (YouTube Data API, etc.)."""

from __future__ import annotations

import json
from typing import Any
from urllib.request import Request, urlopen


class HttpEngine:
    """Simple HTTP engine for API-only targets (no browser needed)."""

    def __init__(self, *, timeout: int = 30) -> None:
        self.timeout = timeout

    async def start(self) -> None:
        pass  # no setup needed

    async def navigate(self, url: str) -> Any:
        req = Request(url, headers={"User-Agent": "collector/1.0"})
        with urlopen(req, timeout=self.timeout) as resp:
            body = resp.read().decode("utf-8")
        return json.loads(body)

    async def evaluate(self, page: Any, expression: str) -> Any:
        # page is already the parsed JSON response
        return page

    async def stop(self) -> None:
        pass
