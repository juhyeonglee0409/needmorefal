"""Narrow CHZZK public API client for outreach discovery."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ChzzkError(RuntimeError):
    pass


class BoundarySignal(ChzzkError):
    def __init__(self, signal: str, message: str) -> None:
        super().__init__(message)
        self.signal = signal


class ChzzkClient:
    base_url = "https://api.chzzk.naver.com/service/v1"

    def __init__(self, *, timeout_seconds: float = 15.0) -> None:
        self.timeout_seconds = timeout_seconds

    def search_channels(
        self,
        keyword: str,
        *,
        offset: int = 0,
        size: int = 30,
    ) -> list[dict[str, Any]]:
        payload = self._get_json(
            "/search/channels",
            {"keyword": keyword, "offset": offset, "size": size},
        )
        return [
            normalize_channel_item(item, matched_keyword=keyword)
            for item in extract_items(payload)
        ]

    def search_lives(
        self,
        keyword: str,
        *,
        offset: int = 0,
        size: int = 30,
    ) -> list[dict[str, Any]]:
        payload = self._get_json(
            "/search/lives",
            {"keyword": keyword, "offset": offset, "size": size},
        )
        return [
            normalize_live_item(item, matched_keyword=keyword)
            for item in extract_items(payload)
        ]

    def channel_detail(self, channel_id: str) -> dict[str, Any]:
        payload = self._get_json(f"/channels/{channel_id}", {})
        content = payload.get("content", payload)
        if isinstance(content, dict) and isinstance(content.get("data"), dict):
            content = content["data"]
        if not isinstance(content, dict):
            raise ChzzkError(f"unexpected detail payload for {channel_id}")
        return normalize_channel_item(content)

    def _get_json(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        query = urlencode({k: v for k, v in params.items() if v is not None})
        url = f"{self.base_url}{path}"
        if query:
            url = f"{url}?{query}"

        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "needmorefal-outreach/0.1",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            if exc.code == 429:
                raise BoundarySignal("http_429", "CHZZK returned HTTP 429") from exc
            if exc.code in {401, 403}:
                raise BoundarySignal(f"http_{exc.code}", f"CHZZK returned HTTP {exc.code}") from exc
            raise ChzzkError(f"CHZZK HTTP {exc.code}") from exc
        except URLError as exc:
            raise ChzzkError(str(exc.reason)) from exc

        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise ChzzkError("CHZZK response was not JSON") from exc
        if not isinstance(payload, dict):
            raise ChzzkError("CHZZK response JSON was not an object")
        return payload


def extract_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the first list of objects from known CHZZK response shapes."""

    candidates: list[Any] = [
        payload.get("content"),
        payload.get("data"),
    ]
    content = payload.get("content")
    if isinstance(content, dict):
        candidates.extend([
            content.get("data"),
            content.get("content"),
            content.get("items"),
        ])
        data = content.get("data")
        if isinstance(data, dict):
            candidates.extend([
                data.get("content"),
                data.get("items"),
                data.get("data"),
            ])

    for candidate in candidates:
        if isinstance(candidate, list):
            return [item for item in candidate if isinstance(item, dict)]
    return []


def normalize_channel_item(
    item: dict[str, Any],
    *,
    matched_keyword: str | None = None,
) -> dict[str, Any]:
    channel = _nested_channel(item)
    return {
        "channel_id": _first(channel, item, "channelId", "channel_id"),
        "channel_name": _first(channel, item, "channelName", "channel_name", "name"),
        "follower_count": _first(channel, item, "followerCount", "follower_count"),
        "description": _first(channel, item, "channelDescription", "description") or "",
        "verified": bool(_first(channel, item, "verifiedMark", "verified", default=False)),
        "open_live": bool(_first(channel, item, "openLive", "open_live", default=False)),
        "subscription_available": _first(
            channel,
            item,
            "subscriptionAvailability",
            "subscription_available",
        ),
        "ad_monetization_available": _first(
            channel,
            item,
            "adMonetizationAvailability",
            "ad_monetization_available",
        ),
        "paid_product_sale_allowed": _first(
            channel,
            item,
            "paidProductSaleAllowed",
            "paid_product_sale_allowed",
        ),
        "matched_keyword": matched_keyword,
    }


def normalize_live_item(
    item: dict[str, Any],
    *,
    matched_keyword: str | None = None,
) -> dict[str, Any]:
    channel = _nested_channel(item)
    tags = _first(item, channel, "tags", "liveTags", default=[]) or []
    if isinstance(tags, str):
        tags = [tags]

    return {
        "channel_id": _first(channel, item, "channelId", "channel_id"),
        "channel_name": _first(channel, item, "channelName", "channel_name", "name"),
        "live_title": _first(item, "liveTitle", "live_title") or "",
        "tags": tags,
        "concurrent_viewers": _first(
            item,
            "concurrentUserCount",
            "concurrent_viewers",
        ),
        "category": _first(
            item,
            "liveCategoryValue",
            "liveCategory",
            "category",
        ),
        "adult": bool(_first(item, "adult", "adultContent", default=False)),
        "vtuber_signal": _has_vtuber_signal(item, tags),
        "matched_keyword": matched_keyword,
        "open_live": True,
    }


def merge_candidate_detail(
    candidate: dict[str, Any],
    detail: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(candidate)
    for key, value in detail.items():
        if value is not None and value != "":
            merged[key] = value
    if candidate.get("open_live"):
        merged["open_live"] = True
    if candidate.get("vtuber_signal"):
        merged["vtuber_signal"] = True
    return merged


def _nested_channel(item: dict[str, Any]) -> dict[str, Any]:
    for key in ("channel", "channelInfo", "channelData"):
        value = item.get(key)
        if isinstance(value, dict):
            return value
    return item


def _first(*objects_and_keys: Any, default: Any = None) -> Any:
    objects: list[dict[str, Any]] = []
    keys: list[str] = []
    for value in objects_and_keys:
        if isinstance(value, dict):
            objects.append(value)
        elif isinstance(value, (list, tuple)):
            keys.extend(str(item) for item in value)
        else:
            keys.append(str(value))

    for obj in objects:
        if not isinstance(obj, dict):
            continue
        for key in keys:
            if key in obj and obj[key] is not None:
                return obj[key]
    return default


def _has_vtuber_signal(item: dict[str, Any], tags: list[Any]) -> bool:
    text = " ".join(
        str(value)
        for value in [
            item.get("liveTitle"),
            item.get("live_title"),
            item.get("liveCategory"),
            item.get("liveCategoryValue"),
            *tags,
        ]
        if value
    ).lower()
    return any(term in text for term in ("버튜버", "버츄얼", "버추얼", "vtuber", "v튜버", "버미육"))
