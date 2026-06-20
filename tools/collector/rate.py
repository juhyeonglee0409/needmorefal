"""Rate control — delay, jitter, and boundary signal detection."""

from __future__ import annotations

import asyncio
import random
import re
from dataclasses import dataclass, field
from typing import Any

from .config import Signal


@dataclass
class RateController:
    """Per-run rate limiter with boundary detection."""

    delay_ms: int = 10000
    jitter_ms: int = 5000
    seed: int = 42
    signals: dict[str, Signal] = field(default_factory=dict)
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    async def wait(self) -> None:
        """Sleep for delay + jitter between requests."""
        ms = self.delay_ms + self._rng.randint(0, max(0, self.jitter_ms))
        await asyncio.sleep(ms / 1000)

    def check_signals(self, state: dict[str, Any]) -> str | None:
        """Check page state for boundary signals.

        Returns the signal name if detected and action is 'abort',
        or None if no abort-worthy signal found.
        Raises SignalSkip for 'skip' actions.
        """
        for name, signal in self.signals.items():
            if not signal.pattern:
                continue
            # check boolean flags from extraction result
            flag_key = _signal_flag_key(name)
            if state.get(flag_key):
                if signal.action == "skip":
                    raise SignalSkip(name)
                return name
            # check body text pattern
            body = str(state.get("body_text", ""))
            if body and re.search(signal.pattern, body, re.IGNORECASE):
                if signal.action == "skip":
                    raise SignalSkip(name)
                return name
        return None


class SignalSkip(Exception):
    """Raised when a signal's action is 'skip' — continue to next target."""

    def __init__(self, signal_name: str) -> None:
        self.signal_name = signal_name
        super().__init__(signal_name)


def _signal_flag_key(name: str) -> str:
    """Map signal name to the boolean key in extraction state.

    checkpoint -> checkpoint
    rate_limit -> rateLimited
    not_found  -> notFound
    """
    mapping = {
        "checkpoint": "checkpoint",
        "rate_limit": "rateLimited",
        "rate_limited": "rateLimited",
        "not_found": "notFound",
    }
    return mapping.get(name, name)
