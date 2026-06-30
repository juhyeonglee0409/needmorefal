"""api_json extractor — HTTP request, parse JSON response."""

from __future__ import annotations

from typing import Any

from ..engines.base import Engine
from ..targets import Target


async def extract_one(
    engine: Engine,
    target: Target,
    url: str,
) -> dict[str, Any]:
    """Fetch URL via HTTP engine and return the JSON payload.

    The HTTP engine's navigate() already returns parsed JSON,
    so this is a thin wrapper that normalizes the output shape.
    """
    data = await engine.navigate(url)
    if isinstance(data, list):
        return {"rows": data, "rowCount": len(data)}
    if isinstance(data, dict):
        rows = data.get("items") or data.get("rows") or data.get("data") or []
        return {**data, "rows": rows, "rowCount": len(rows)}
    return {"rows": [], "rowCount": 0}
