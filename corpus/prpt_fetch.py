from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path
from typing import Any

try:
    from .config import ERRORS_PATH, PROGRESS_PATH
    from .io_utils import append_error, append_ndjson, append_progress, load_progress_keys, utc_now
    from .schemas import ExtractedRecord, Occurrence, content_id_for, normalize_body, record_to_dict
except ImportError:  # pragma: no cover - direct script execution fallback.
    from config import ERRORS_PATH, PROGRESS_PATH
    from io_utils import append_error, append_ndjson, append_progress, load_progress_keys, utc_now
    from schemas import ExtractedRecord, Occurrence, content_id_for, normalize_body, record_to_dict

API_BASE = "https://api.prpt.ai"
PAGE_SIZE = 100
SOURCE_ID = "K7"

MODEL_MAP = {
    "ChatGPT": "chatgpt",
    "Claude": "claude",
    "Gemini": "gemini",
    "Copilot": "copilot",
    "Midjourney": "midjourney",
    "DALL-E": "sd",
}


def fetch_prpt_prompts(
    output_path: Path,
    *,
    progress_path: Path = PROGRESS_PATH,
    errors_path: Path = ERRORS_PATH,
    limit: int | None = None,
    sleep_sec: float = 1.0,
) -> int:
    progress = load_progress_keys(progress_path)
    known_ids = _load_known_ids(output_path.parent.parent / "known_ids.txt")
    written = 0
    start_row = 1

    while True:
        if limit is not None and written >= limit:
            break
        try:
            items = _fetch_page(start_row, PAGE_SIZE)
        except Exception as exc:
            append_error(errors_path, "L0-prpt", SOURCE_ID, type(exc).__name__, detail=str(exc))
            break

        if not items:
            break

        for item in items:
            post_id = item.get("POST_ID")
            prompt = str(item.get("PROMPT") or "").strip()
            if not prompt or not post_id:
                continue

            url = f"https://www.prpt.ai/prompt/textDetail/{post_id}"
            progress_key = ("L1", SOURCE_ID, url)
            if progress_key in progress:
                continue

            cid = content_id_for(normalize_body(prompt))
            if cid in known_ids:
                continue

            title = str(item.get("TITLE") or "")
            model_name = str(item.get("MODEL_NAME") or "")
            lang = _detect_lang(prompt, title)
            target_model = MODEL_MAP.get(model_name, "generic")

            occurrence = Occurrence(
                source_id=SOURCE_ID,
                source_url=url,
                collected_at=utc_now(),
                published_at=_parse_date(item.get("FRDT")),
            )
            record = ExtractedRecord.from_body(
                body=prompt,
                context=title or f"prpt.ai #{post_id}",
                lang=lang,
                occurrence=occurrence,
            )
            append_ndjson(output_path, record_to_dict(record))
            append_progress(progress_path, "L1", SOURCE_ID, url)
            progress.add(progress_key)
            written += 1

            if limit is not None and written >= limit:
                break

        total = items[0].get("TOTAL_COUNT", 0) if items else 0
        start_row += PAGE_SIZE
        if start_row > total:
            break
        time.sleep(sleep_sec)

    return written


def _fetch_page(start_row: int, end_row_count: int) -> list[dict[str, Any]]:
    url = f"{API_BASE}/post/prompt/list/load?startRow={start_row}&endRow={start_row + end_row_count - 1}&sortOrder=FRDT+DESC"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="replace"))
    if data.get("code") != "response.ok":
        raise RuntimeError(f"prpt.ai API error: {data.get('message')}")
    return data.get("data") or []


def _detect_lang(prompt: str, title: str) -> str:
    text = prompt + " " + title
    ko_chars = sum(1 for c in text if "가" <= c <= "힣" or "ㄱ" <= c <= "ㆎ")
    en_chars = sum(1 for c in text if "a" <= c.lower() <= "z")
    if ko_chars > en_chars * 2:
        return "ko"
    if en_chars > ko_chars * 2:
        return "en"
    return "mixed"


def _load_known_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return set(line.strip() for line in path.read_text("utf-8").splitlines() if line.strip())


def _parse_date(value: Any) -> str | None:
    if not value:
        return None
    s = str(value)
    if len(s) >= 10:
        return s[:10]
    return s
