"""Heuristic classification for CHZZK outreach candidates."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .email_extract import email_domain, extract_public_email


VTUBER_TERMS = (
    "버튜버",
    "버츄얼",
    "버추얼",
    "브이튜버",
    "vtuber",
    "v튜버",
    "v-tuber",
    "버미육",
    "virtual streamer",
)


@dataclass(frozen=True)
class AgencyRules:
    agency_terms: tuple[str, ...] = ()
    email_domains: tuple[str, ...] = ()

    @classmethod
    def empty(cls) -> "AgencyRules":
        return cls()

    def match(self, *, text: str, email: str | None = None) -> str | None:
        lowered = text.lower()
        for term in self.agency_terms:
            needle = term.lower().strip()
            if needle and needle in lowered:
                return term

        domain = email_domain(email)
        for rule_domain in self.email_domains:
            needle = rule_domain.lower().strip()
            if not needle:
                continue
            if domain and domain.endswith(needle):
                return rule_domain
            if needle in lowered:
                return rule_domain
        return None


def load_agency_rules(path: str | Path | None = None) -> AgencyRules:
    if path is None:
        path = Path(__file__).with_name("agencies.yaml")
    path = Path(path)
    if not path.exists():
        return AgencyRules.empty()

    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        raw = json.loads(text)
    else:
        raw = _load_simple_yaml_lists(text)

    return AgencyRules(
        agency_terms=tuple(raw.get("agency_terms") or raw.get("agency_names") or ()),
        email_domains=tuple(raw.get("email_domains") or ()),
    )


def _load_simple_yaml_lists(text: str) -> dict[str, list[str]]:
    data: dict[str, list[str]] = {}
    current: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if line.endswith(":"):
            current = line[:-1].strip()
            data.setdefault(current, [])
            continue
        if line.startswith("- ") and current:
            value = line[2:].strip().strip("\"'")
            if value:
                data.setdefault(current, []).append(value)
    return data


def classify_vtuber(raw: dict[str, Any]) -> dict[str, bool | str]:
    text = _combined_text(raw)
    lowered = text.lower()

    matched = [term for term in VTUBER_TERMS if term.lower() in lowered]
    if raw.get("vtuber_signal") is True:
        return {"value": True, "method": "heuristic", "confidence": "high"}
    if matched:
        return {"value": True, "method": "heuristic", "confidence": "high"}
    return {"value": False, "method": "heuristic", "confidence": "low"}


def follower_segment(follower_count: int | None) -> str:
    if follower_count is None:
        return "unknown"
    if follower_count < 150:
        return "rookie"
    if follower_count <= 10000:
        return "growth"
    return "large"


def build_channel_record(
    raw: dict[str, Any],
    *,
    agency_rules: AgencyRules | None = None,
    seen_at: str | None = None,
) -> dict[str, Any]:
    """Build the canonical append-only channel-pool record."""

    agency_rules = agency_rules or AgencyRules.empty()
    seen_at = seen_at or _now()

    channel_id = _first(raw, "channel_id", "channelId")
    channel_name = _first(raw, "channel_name", "channelName", "name") or ""
    description = _first(raw, "description", "channelDescription") or ""
    follower_count = _to_int(_first(raw, "follower_count", "followerCount"))
    open_live = bool(_first(raw, "open_live", "openLive", default=False))
    if not open_live and (raw.get("live_title") or raw.get("liveTitle")):
        open_live = True
    if not open_live and raw.get("concurrent_viewers") is not None:
        open_live = True

    email = extract_public_email(description)
    text = _combined_text(raw)
    matched_agency = agency_rules.match(text=text, email=email)
    vtuber = classify_vtuber(raw)
    solo_value = matched_agency is None
    segment = follower_segment(follower_count)

    status = "candidate"
    if not vtuber["value"] or not solo_value:
        status = "excluded"
    elif email:
        status = "qualified"

    return {
        "channel_id": str(channel_id or ""),
        "channel_name": str(channel_name),
        "follower_count": follower_count,
        "description": str(description),
        "segment": segment,
        "vtuber": vtuber,
        "solo": {"value": solo_value, "matched_agency": matched_agency},
        "email": {
            "value": email,
            "source": "bio" if email else None,
            "seen_at": seen_at if email else None,
        },
        "activity": {
            "open_live_seen": open_live,
            "last_broadcast": None,
            "source": "api",
        },
        "metrics": {
            "avg_viewers_30d": None,
            "cohort_percentile": None,
            "bottleneck": None,
        },
        "outreach": {
            "status": status,
            "sent_at": None,
            "followup_at": None,
            "opted_out_at": None,
        },
    }


def _combined_text(raw: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in (
        "channel_name",
        "channelName",
        "name",
        "description",
        "channelDescription",
        "live_title",
        "liveTitle",
        "category",
    ):
        value = raw.get(key)
        if value:
            parts.append(str(value))

    tags = raw.get("tags") or raw.get("liveTags") or ()
    if isinstance(tags, str):
        parts.append(tags)
    else:
        parts.extend(str(tag) for tag in tags if tag)
    return "\n".join(parts)


def _first(raw: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in raw and raw[key] is not None:
            return raw[key]
    return default


def _to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")
