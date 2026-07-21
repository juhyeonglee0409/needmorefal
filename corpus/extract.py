from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from .config import ERRORS_PATH, LLM_EXTRACT_MODEL, PROGRESS_PATH
    from .gate import truncate_tokens
    from .io_utils import append_error, append_ndjson, append_progress, load_progress_keys, read_ndjson
    from .llm_client import llm_json_array
    from .schemas import ExtractedRecord, Occurrence, content_id_for, normalize_body, record_to_dict
except ImportError:  # pragma: no cover - direct script execution fallback.
    from config import ERRORS_PATH, LLM_EXTRACT_MODEL, PROGRESS_PATH
    from gate import truncate_tokens
    from io_utils import append_error, append_ndjson, append_progress, load_progress_keys, read_ndjson
    from llm_client import llm_json_array
    from schemas import ExtractedRecord, Occurrence, content_id_for, normalize_body, record_to_dict


EXTRACT_SYSTEM_PROMPT = """이 페이지에서 LLM에게 보내는 프롬프트 텍스트만 추출한다.

저자의 설명, 해설, 사용법 안내, UI 텍스트는 프롬프트가 아니다.
"이렇게 쓰면 좋습니다"는 설명이고, "너는 전문 분석가야. 다음을 분석해줘"가 프롬프트다.
프롬프트 본문과 주변 텍스트의 경계를 정확히 잘라야 한다.

각 프롬프트를 식별하고, 본문만 추출하라.

JSON 배열로만 응답하라:
[{"body": "프롬프트 전문", "context": "페이지 내 위치 한 줄", "lang": "ko | en | mixed", "published_at": "YYYY-MM-DD 또는 null"}]

프롬프트가 없으면 빈 배열 []을 반환한다."""

COMMUNITY_BERTH = "다른 사용자의 댓글, 반응, 감상은 프롬프트가 아니다"
PLATFORM_BERTH = "카테고리명, 태그, 평점, 사용 횟수는 메타데이터이지 본문이 아니다"


def extract_prompts(
    input_path: Path,
    output_path: Path,
    *,
    progress_path: Path = PROGRESS_PATH,
    errors_path: Path = ERRORS_PATH,
) -> int:
    progress = load_progress_keys(progress_path)
    known_ids = _load_known_ids(output_path.parent.parent / "known_ids.txt")
    dedup_skipped = 0
    rows = list(read_ndjson(input_path))
    total = len(rows)
    skipped = 0
    processed = 0
    written = 0
    errors = 0
    for row in rows:
        source_id = str(row.get("source_id") or "")
        url = str(row.get("url") or "")
        if not source_id or not url:
            append_error(errors_path, "L1", source_id, "invalid_filtered_record", raw=row)
            continue
        progress_key = ("L1", source_id, url)
        if progress_key in progress:
            skipped += 1
            continue
        processed += 1
        try:
            page_text = select_extraction_text(row)
            if not page_text:
                append_progress(progress_path, "L1", source_id, url, status="skip_empty_page_text")
                progress.add(progress_key)
                if processed % 10 == 0:
                    _log_extract_progress(source_id, processed, skipped, total, written, errors, dedup_skipped)
                continue
            items = extract_items_with_llm(source_id, page_text)
            for item in items:
                body = str(item.get("body") or "").strip()
                if not body:
                    continue
                cid = content_id_for(normalize_body(body))
                if cid in known_ids:
                    dedup_skipped += 1
                    continue
                occurrence = Occurrence(
                    source_id=source_id,
                    source_url=url,
                    collected_at=str(row.get("collected_at") or ""),
                    published_at=item.get("published_at"),
                )
                record = ExtractedRecord.from_body(
                    body=body,
                    context=str(item.get("context") or row.get("title") or url),
                    lang=coerce_lang(item.get("lang")),
                    occurrence=occurrence,
                )
                append_ndjson(output_path, record_to_dict(record))
                written += 1
            append_progress(progress_path, "L1", source_id, url)
            progress.add(progress_key)
        except Exception as exc:  # noqa: BLE001 - preserve in errors ledger.
            errors += 1
            append_error(errors_path, "L1", source_id, type(exc).__name__, url=url, detail=str(exc))
            append_progress(progress_path, "L1", source_id, url, status="error")
            progress.add(progress_key)
        if processed % 10 == 0:
            _log_extract_progress(source_id, processed, skipped, total, written, errors)
    if processed > 0:
        _log_extract_progress(source_id, processed, skipped, total, written, errors, dedup_skipped)
    return written


def _load_known_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return set(line.strip() for line in path.read_text("utf-8").splitlines() if line.strip())


def _log_extract_progress(source_id: str, processed: int, skipped: int, total: int, written: int, errors: int, dedup_skipped: int = 0) -> None:
    remaining = total - skipped - processed
    dedup_part = f" dedup_skip {dedup_skipped}" if dedup_skipped else ""
    print(f"  [extract {source_id}] {processed}/{total - skipped} done ({skipped} skip) | prompts {written} err {errors}{dedup_part} | {remaining} left", flush=True)


def select_extraction_text(row: dict[str, Any]) -> str:
    blocks = [str(block).strip() for block in row.get("structured_blocks") or [] if str(block).strip()]
    if blocks:
        return truncate_tokens("\n\n---\n\n".join(blocks), 6000)
    return truncate_tokens(str(row.get("page_text") or ""), 6000)


def extract_items_with_llm(source_id: str, page_text: str) -> list[dict[str, Any]]:
    system_prompt = EXTRACT_SYSTEM_PROMPT
    berth = source_berth(source_id)
    if berth:
        system_prompt = f"{system_prompt}\n\n추가 BERTH: {berth}"
    items = llm_json_array(
        system_prompt=system_prompt,
        user_prompt=f"<page_text>\n{page_text}\n</page_text>",
        max_tokens=2400,
        model_override=LLM_EXTRACT_MODEL,
    )
    normalized_items: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, dict):
            normalized_items.append(item)
    return normalized_items


def source_berth(source_id: str) -> str | None:
    if source_id in {"K1", "K2"}:
        return COMMUNITY_BERTH
    if source_id in {"K6", "K7"}:
        return PLATFORM_BERTH
    return None


def coerce_lang(value: Any) -> str:
    if value in {"ko", "en", "mixed"}:
        return value
    return "mixed"

