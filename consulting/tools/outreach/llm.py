"""Interface stub for future S3 boundary classification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class BoundaryDecision:
    value: bool
    confidence: str
    rationale: str


class BoundaryClassifier(Protocol):
    def classify(self, candidate: dict[str, Any]) -> BoundaryDecision:
        """Classify a boundary case.

        Implementations are intentionally not wired in this package.
        """


class StubBoundaryClassifier:
    def classify(self, candidate: dict[str, Any]) -> BoundaryDecision:
        raise NotImplementedError(
            "LLM boundary classification is an interface stub only in tools.outreach."
        )
