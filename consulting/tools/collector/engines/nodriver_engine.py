"""nodriver engine — real Chrome with automation detection removed."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import Engine


class NodriverEngine(Engine):
    """Collection engine using nodriver (undetected-chromedriver successor).

    nodriver passes Vercel WAF without a pre-approved profile because it
    launches a real Chrome binary with webdriver signals stripped.
    """

    def __init__(
        self,
        *,
        headless: bool = False,
        lang: str = "ko-KR",
        profile_dir: str | None = None,
    ) -> None:
        self.headless = headless
        self.lang = lang
        self.profile_dir = profile_dir
        self._browser: Any = None

    async def start(self) -> None:
        try:
            import nodriver as uc  # type: ignore[import-untyped]
        except ImportError:
            raise RuntimeError(
                "nodriver is not installed. Run: pip install nodriver"
            ) from None

        kwargs: dict[str, Any] = {
            "headless": self.headless,
            "lang": self.lang,
        }
        if self.profile_dir:
            kwargs["user_data_dir"] = Path(self.profile_dir).resolve()

        self._browser = await uc.start(**kwargs)

    async def navigate(self, url: str) -> Any:
        if self._browser is None:
            raise RuntimeError("engine not started")
        page = await self._browser.get(url)
        return page

    async def evaluate(self, page: Any, expression: str) -> Any:
        value = await page.evaluate(expression)
        if isinstance(value, str):
            return json.loads(value)
        if isinstance(value, dict) and value.get("type") == "string" and "value" in value:
            return json.loads(str(value["value"]))
        if isinstance(value, dict):
            return value
        return json.loads(str(value))

    async def stop(self) -> None:
        if self._browser is not None:
            try:
                self._browser.stop()
            except Exception:
                pass
            self._browser = None
