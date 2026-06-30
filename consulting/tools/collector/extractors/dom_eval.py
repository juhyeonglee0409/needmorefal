"""dom_eval extractor — run JS expression in browser, parse JSON result."""

from __future__ import annotations

import asyncio
import csv
import json
import time
from pathlib import Path
from typing import Any

from ..config import Config
from ..engines.base import Engine
from ..rate import RateController, SignalSkip
from ..targets import Target


def load_expression(config: Config) -> str:
    """Load JS expression template from file.

    The template should contain {CHANNEL_ID} placeholder
    that will be substituted per target.
    """
    if not config.expression_file:
        raise ValueError("extraction.expression_file is required for dom_eval")
    path = config.resolve(config.expression_file)
    if not path.exists():
        raise FileNotFoundError(f"expression file not found: {path}")
    return path.read_text(encoding="utf-8")


def build_expression(template: str, target: Target) -> str:
    """Substitute target values into the JS expression template."""
    return template.replace("{CHANNEL_ID}", json.dumps(target.channel_id))


async def extract_one(
    engine: Engine,
    target: Target,
    url: str,
    expression: str,
    config: Config,
    rate: RateController,
) -> dict[str, Any]:
    """Navigate to URL, wait for data, extract rows.

    Returns the extraction state dict with keys:
        url, checkpoint, rateLimited, notFound, rowCount, rows
    """
    page = await engine.navigate(url)
    started = time.monotonic()
    deadline = started + (config.wait_timeout_ms / 1000)
    checkpoint_started: float | None = None
    state: dict[str, Any] | None = None

    while time.monotonic() < deadline:
        await asyncio.sleep(config.wait_poll_ms / 1000)
        state = await engine.evaluate(page, expression)

        # check boundary signals
        signal = rate.check_signals(state)
        if signal:
            if signal == "checkpoint" and config.checkpoint_wait_ms > 0:
                if checkpoint_started is None:
                    checkpoint_started = time.monotonic()
                    deadline = max(
                        deadline,
                        checkpoint_started + (config.checkpoint_wait_ms / 1000),
                    )
                if time.monotonic() < checkpoint_started + (config.checkpoint_wait_ms / 1000):
                    continue
            raise RuntimeError(signal)

        checkpoint_started = None

        # check if we have data
        if int(state.get("rowCount") or 0) > 0:
            return state

    # final attempt
    if state is None:
        state = await engine.evaluate(page, expression)
    return state


def write_csv(
    path: Path,
    rows: list[dict[str, Any]],
    columns: list[str],
) -> None:
    """Write extracted rows to CSV with specified column order."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            cleaned = {col: str(row.get(col, "")) for col in columns}
            writer.writerow(cleaned)
