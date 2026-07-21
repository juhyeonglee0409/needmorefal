from __future__ import annotations

import glob
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

try:
    from .io_utils import read_ndjson, write_ndjson
    from .schemas import ExtractedRecord, NormalizedRecord, extracted_from_dict, merge_occurrences, record_to_dict
except ImportError:  # pragma: no cover - direct script execution fallback.
    from io_utils import read_ndjson, write_ndjson
    from schemas import ExtractedRecord, NormalizedRecord, extracted_from_dict, merge_occurrences, record_to_dict


DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "coding": ["코드", "함수", "버그", "code", "debug", "refactor", "api"],
    "writing": ["글", "블로그", "번역", "seo", "write", "translate", "essay"],
    "analysis": ["분석", "데이터", "리서치", "analyze", "data", "research"],
    "business": ["마케팅", "기획", "보고서", "kpi", "marketing", "strategy"],
    "education": ["설명", "학습", "튜터", "explain", "teach", "tutor"],
    "creative": ["이미지", "스토리", "아이디어", "image", "story", "creative"],
    "roleplay": ["역할극", "페르소나", "roleplay", "character", "act as"],
    "system": ["시스템 프롬프트", "system prompt", "custom instructions"],
}
MODEL_PATTERNS: dict[str, re.Pattern[str]] = {
    "chatgpt": re.compile(r"ChatGPT|GPT-[34]|GPT4|openai", re.I),
    "claude": re.compile(r"Claude|Anthropic", re.I),
    "gemini": re.compile(r"Gemini|Bard|Google AI", re.I),
    "copilot": re.compile(r"Copilot|Bing Chat", re.I),
    "midjourney": re.compile(r"Midjourney|MJ", re.I),
    "sd": re.compile(r"Stable Diffusion|SD|SDXL", re.I),
}
SOURCE_MODEL_FALLBACK: dict[str, list[str]] = {
    "E1": ["chatgpt"],
    "E10": ["chatgpt"],
    "E12": ["claude"],
    "K2": ["chatgpt"],
}
PLACEHOLDER_RE = re.compile(r"\[.{1,30}\]|\{.{1,30}\}|<.{1,30}>")
SYSTEM_PROMPT_RE = re.compile(r"시스템\s*프롬프트|system\s*prompt|custom\s*instructions", re.I)
URL_ONLY_RE = re.compile(r"^\s*https?://\S+\s*$", re.I)
CODE_LINE_RE = re.compile(r"^\s*(def |class |function |const |let |var |import |from |#include|public |private )")


def normalize_files(input_patterns: list[str], output_path: Path) -> dict[str, int]:
    grouped: dict[str, list[ExtractedRecord]] = defaultdict(list)
    input_records = 0
    for path in expand_inputs(input_patterns):
        for row in read_ndjson(path):
            record = extracted_from_dict(row)
            grouped[record.content_id].append(record)
            input_records += 1

    exact_records: list[ExtractedRecord] = []
    for records in grouped.values():
        base = records[0]
        base.occurrences = merge_occurrences(records)
        exact_records.append(base)

    deduped_records = near_dedup_records(exact_records)
    exact_dupes_removed = input_records - len(exact_records)
    near_dupes_removed = len(exact_records) - len(deduped_records)

    normalized: list[dict[str, object]] = []
    quality_filtered = 0
    for base in deduped_records:
        content_id = base.content_id
        body_tokens = count_tokens(base.body)
        if not passes_quality_filter(base.body, body_tokens):
            quality_filtered += 1
            continue
        normalized_record = NormalizedRecord(
            content_id=content_id,
            body=base.body,
            context=base.context,
            lang=detect_lang(base.body),
            occurrences=base.occurrences,
            body_tokens=body_tokens,
            domain=detect_domain(base.body, base.context),
            has_placeholders=bool(PLACEHOLDER_RE.search(base.body)),
            is_system_prompt=bool(SYSTEM_PROMPT_RE.search(base.body + "\n" + base.context)),
            target_models=detect_models(base.body, base.context, base.occurrences[0].source_id if base.occurrences else ""),
            tiller=None,
        )
        normalized.append(record_to_dict(normalized_record))
    normalized.sort(key=lambda row: str(row["content_id"]))
    records = write_ndjson(output_path, normalized)
    _update_known_ids(output_path.parent / "known_ids.txt", [row["content_id"] for row in normalized])
    return {
        "input_records": input_records,
        "after_exact_dedup": len(exact_records),
        "after_near_dedup": len(deduped_records),
        "records": records,
        "exact_dupes_removed": exact_dupes_removed,
        "near_dupes_removed": near_dupes_removed,
        "quality_filtered": quality_filtered,
    }


def _update_known_ids(path: Path, new_ids: list[str]) -> None:
    existing: set[str] = set()
    if path.exists():
        existing = set(line.strip() for line in path.read_text("utf-8").splitlines() if line.strip())
    merged = sorted(existing | set(new_ids))
    path.write_text("\n".join(merged) + "\n", encoding="utf-8")


def near_dedup_records(records: list[ExtractedRecord], *, threshold: float = 0.8, num_perm: int = 128) -> list[ExtractedRecord]:
    if len(records) < 2:
        return records
    try:
        from datasketch import MinHash, MinHashLSH  # type: ignore
    except ImportError:
        print("warning: datasketch not installed; skipping MinHash near-dedup", file=sys.stderr)
        return records

    minhashes: dict[int, object] = {}
    lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
    parent = list(range(len(records)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for index, record in enumerate(records):
        mh = MinHash(num_perm=num_perm)
        tokens = body_shingles(record.body)
        if not tokens:
            minhashes[index] = mh
            continue
        for token in tokens:
            mh.update(token.encode("utf-8"))
        minhashes[index] = mh

    for index, mh in minhashes.items():
        matches = lsh.query(mh)
        for match in matches:
            union(index, int(match))
        lsh.insert(str(index), mh)

    clusters: dict[int, list[int]] = defaultdict(list)
    for index in range(len(records)):
        clusters[find(index)].append(index)

    merged: list[ExtractedRecord] = []
    for members in clusters.values():
        if len(members) == 1:
            merged.append(records[members[0]])
            continue
        representative_index = max(members, key=lambda item: count_tokens(records[item].body))
        representative = records[representative_index]
        representative.occurrences = merge_occurrences([records[item] for item in members])
        merged.append(representative)
    return merged


def body_shingles(body: str, *, width: int = 5) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9가-힣_]+", body.lower())
    if len(tokens) <= width:
        return tokens
    return [" ".join(tokens[index : index + width]) for index in range(len(tokens) - width + 1)]


def expand_inputs(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        matched = glob.glob(pattern)
        if matched:
            paths.extend(Path(p) for p in matched)
        else:
            paths.append(Path(pattern))
    return sorted(set(paths))


def count_tokens(text: str) -> int:
    try:
        import tiktoken  # type: ignore

        return len(tiktoken.encoding_for_model("gpt-4").encode(text))
    except Exception:  # noqa: BLE001 - optional dependency fallback.
        return len(re.findall(r"\w+|[^\s\w]", text, re.UNICODE))


def passes_quality_filter(body: str, body_tokens: int) -> bool:
    if body_tokens < 10 or body_tokens > 3000:
        return False
    if URL_ONLY_RE.match(body):
        return False
    lines = [line for line in body.splitlines() if line.strip()]
    if lines:
        code_like = sum(1 for line in lines if CODE_LINE_RE.match(line))
        if code_like / len(lines) > 0.8:
            return False
    return True


def detect_lang(text: str) -> str:
    hangul = len(re.findall(r"[가-힣]", text))
    ascii_letters = len(re.findall(r"[A-Za-z]", text))
    if hangul and ascii_letters:
        return "mixed"
    if hangul:
        return "ko"
    return "en"


def detect_domain(body: str, context: str) -> str:
    text = (body + "\n" + context).lower()
    scores = {
        domain: sum(1 for keyword in keywords if keyword.lower() in text)
        for domain, keywords in DOMAIN_KEYWORDS.items()
    }
    best = max(scores.items(), key=lambda item: item[1])
    return best[0] if best[1] > 0 else "other"


def detect_models(body: str, context: str, source_id: str) -> list[str]:
    text = body + "\n" + context
    models = [name for name, pattern in MODEL_PATTERNS.items() if pattern.search(text)]
    if models:
        return models
    return SOURCE_MODEL_FALLBACK.get(source_id, ["generic"])
