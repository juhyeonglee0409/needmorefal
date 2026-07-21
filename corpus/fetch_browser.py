from __future__ import annotations

import asyncio
import inspect
from typing import Any


_browser: Any | None = None
_loop: asyncio.AbstractEventLoop | None = None


def fetch_rendered_html(url: str, *, delay_sec: float = 2.0, timeout_sec: float = 20.0) -> str:
    """Fetch rendered DOM HTML through nodriver without persisting browser state."""
    return _run(_fetch_rendered_html_async(url, delay_sec=delay_sec, timeout_sec=timeout_sec))


def close_browser() -> None:
    global _loop
    loop = _loop
    if loop is None or loop.is_closed():
        return
    if loop.is_running():
        raise RuntimeError("fetch_browser.close_browser() cannot run inside an active event loop")
    loop.run_until_complete(_close_browser_async())
    loop.close()
    _loop = None


async def _fetch_rendered_html_async(url: str, *, delay_sec: float, timeout_sec: float = 20.0) -> str:
    browser = await _ensure_browser()
    try:
        page = await asyncio.wait_for(browser.get(url), timeout=timeout_sec)
    except asyncio.TimeoutError:
        raise RuntimeError(f"nodriver page load timed out after {timeout_sec}s: {url}")
    if delay_sec > 0:
        await asyncio.sleep(delay_sec)
    try:
        html = await asyncio.wait_for(page.get_content(), timeout=10.0)
    except asyncio.TimeoutError:
        raise RuntimeError(f"nodriver get_content timed out: {url}")
    return str(html)


def fetch_profile_posts(url: str, *, max_scrolls: int = 15, scroll_pause: float = 2.0) -> str:
    """Fetch profile page with scroll to load more posts."""
    return _run(_fetch_profile_posts_async(url, max_scrolls=max_scrolls, scroll_pause=scroll_pause))


async def _fetch_profile_posts_async(url: str, *, max_scrolls: int, scroll_pause: float) -> str:
    browser = await _ensure_browser()
    page = await asyncio.wait_for(browser.get(url), timeout=20.0)
    await asyncio.sleep(3.0)
    prev_height = 0
    for _ in range(max_scrolls):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(scroll_pause)
        cur_height = await page.evaluate("document.body.scrollHeight")
        if cur_height == prev_height:
            break
        prev_height = cur_height
    html = await asyncio.wait_for(page.get_content(), timeout=10.0)
    return str(html)


async def _ensure_browser() -> Any:
    global _browser
    if _browser is not None:
        return _browser
    try:
        import nodriver as uc  # type: ignore
    except ImportError as exc:
        raise RuntimeError("nodriver not installed: pip install nodriver") from exc
    _browser = await uc.start(headless=False, lang="ko-KR")
    return _browser


async def _close_browser_async() -> None:
    global _browser
    browser = _browser
    _browser = None
    if browser is None:
        return
    stop = getattr(browser, "stop", None)
    if stop is None:
        return
    result = stop()
    if inspect.isawaitable(result):
        await result


def _run(coro: Any) -> Any:
    loop = _get_loop()
    if loop.is_running():
        raise RuntimeError("fetch_browser cannot run inside an active event loop")
    return loop.run_until_complete(coro)


def _get_loop() -> asyncio.AbstractEventLoop:
    global _loop
    if _loop is None or _loop.is_closed():
        _loop = asyncio.new_event_loop()
    return _loop
