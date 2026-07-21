from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any, Literal


Lang = Literal["ko", "en", "mixed"]
Domain = Literal[
    "coding",
    "writing",
    "analysis",
    "business",
    "education",
    "creative",
    "roleplay",
    "system",
    "other",
]
ModelName = Literal["chatgpt", "claude", "gemini", "copilot", "midjourney", "sd", "generic"]


def content_id_for(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


@dataclass(slots=True)
class Occurrence:
    source_id: str
    source_url: str
    collected_at: str
    published_at: str | None = None


@dataclass(slots=True)
class UrlRecord:
    url: str
    source_id: str
    title: str | None
    collected_at: str
    snippet: str | None = None


@dataclass(slots=True)
class ExtractedRecord:
    content_id: str
    body: str
    context: str
    lang: Lang
    occurrences: list[Occurrence]

    @classmethod
    def from_body(
        cls,
        *,
        body: str,
        context: str,
        lang: Lang,
        occurrence: Occurrence,
    ) -> "ExtractedRecord":
        clean_body = normalize_body(body)
        return cls(
            content_id=content_id_for(clean_body),
            body=clean_body,
            context=context.strip(),
            lang=lang,
            occurrences=[occurrence],
        )


@dataclass(slots=True)
class NormalizedRecord:
    content_id: str
    body: str
    context: str
    lang: Lang
    occurrences: list[Occurrence]
    body_tokens: int
    domain: Domain
    has_placeholders: bool
    is_system_prompt: bool
    target_models: list[ModelName]
    tiller: dict[str, Any] | None = None


def normalize_body(body: str) -> str:
    lines = [line.rstrip() for line in body.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    return "\n".join(lines).strip()


def record_to_dict(record: UrlRecord | ExtractedRecord | NormalizedRecord) -> dict[str, Any]:
    return asdict(record)


def url_record_from_dict(data: dict[str, Any]) -> UrlRecord:
    return UrlRecord(
        url=str(data["url"]),
        source_id=str(data["source_id"]),
        title=data.get("title"),
        collected_at=str(data.get("collected_at") or ""),
    )


def occurrence_from_dict(data: dict[str, Any]) -> Occurrence:
    return Occurrence(
        source_id=str(data["source_id"]),
        source_url=str(data["source_url"]),
        collected_at=str(data["collected_at"]),
        published_at=data.get("published_at"),
    )


def extracted_from_dict(data: dict[str, Any]) -> ExtractedRecord:
    body = normalize_body(str(data["body"]))
    content_id = content_id_for(body)
    return ExtractedRecord(
        content_id=content_id,
        body=body,
        context=str(data.get("context") or ""),
        lang=_coerce_lang(data.get("lang")),
        occurrences=[occurrence_from_dict(o) for o in data.get("occurrences", [])],
    )


def normalized_from_dict(data: dict[str, Any]) -> NormalizedRecord:
    return NormalizedRecord(
        content_id=str(data["content_id"]),
        body=str(data["body"]),
        context=str(data.get("context") or ""),
        lang=_coerce_lang(data.get("lang")),
        occurrences=[occurrence_from_dict(o) for o in data.get("occurrences", [])],
        body_tokens=int(data["body_tokens"]),
        domain=_coerce_domain(data.get("domain")),
        has_placeholders=bool(data["has_placeholders"]),
        is_system_prompt=bool(data["is_system_prompt"]),
        target_models=[_coerce_model(m) for m in data.get("target_models", [])],
        tiller=data.get("tiller"),
    )


def _coerce_lang(value: Any) -> Lang:
    if value in {"ko", "en", "mixed"}:
        return value
    return "mixed"


def _coerce_domain(value: Any) -> Domain:
    allowed = {"coding", "writing", "analysis", "business", "education", "creative", "roleplay", "system", "other"}
    return value if value in allowed else "other"


def _coerce_model(value: Any) -> ModelName:
    allowed = {"chatgpt", "claude", "gemini", "copilot", "midjourney", "sd", "generic"}
    return value if value in allowed else "generic"


def merge_occurrences(records: list[ExtractedRecord]) -> list[Occurrence]:
    seen: set[tuple[str, str, str | None]] = set()
    merged: list[Occurrence] = []
    for record in records:
        for occurrence in record.occurrences:
            key = (occurrence.source_id, occurrence.source_url, occurrence.published_at)
            if key in seen:
                continue
            seen.add(key)
            merged.append(occurrence)
    return merged
