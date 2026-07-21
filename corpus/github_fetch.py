from __future__ import annotations

import csv
import io
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterable

try:
    from .config import ERRORS_PATH, GITHUB_SOURCES, PROGRESS_PATH, github_token
    from .io_utils import append_error, append_ndjson, append_progress, load_progress_keys, utc_now
    from .schemas import ExtractedRecord, Occurrence, record_to_dict
except ImportError:  # pragma: no cover - direct script execution fallback.
    from config import ERRORS_PATH, GITHUB_SOURCES, PROGRESS_PATH, github_token
    from io_utils import append_error, append_ndjson, append_progress, load_progress_keys, utc_now
    from schemas import ExtractedRecord, Occurrence, record_to_dict


PROMPT_HINT_RE = re.compile(
    r"\b(act as|you are|i want you to|ignore previous|system prompt|custom instructions|"
    r"write|create|generate|analyze|explain|summarize|translate|prompt)\b",
    re.IGNORECASE,
)
FENCE_RE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
HEADING_RE = re.compile(r"^(#{2,3})\s+(.+?)\s*$\n(.*?)(?=^#{2,3}\s+|\Z)", re.MULTILINE | re.DOTALL)


class GitHubError(RuntimeError):
    pass


def fetch_sources(
    source_ids: list[str],
    output_path: Path,
    *,
    progress_path: Path = PROGRESS_PATH,
    errors_path: Path = ERRORS_PATH,
    limit: int | None = None,
    sleep_sec: float = 0.2,
) -> int:
    token = github_token()
    progress = load_progress_keys(progress_path)
    written = 0
    for source_id in source_ids:
        source = GITHUB_SOURCES.get(source_id)
        if not source:
            append_error(errors_path, "L0", source_id, "unknown_source")
            continue
        try:
            for record in iter_source_records(source_id, source, token=token, sleep_sec=sleep_sec):
                source_url = record.occurrences[0].source_url
                key = ("L0", source_id, source_url)
                if key in progress:
                    continue
                append_ndjson(output_path, record_to_dict(record))
                append_progress(progress_path, "L0", source_id, source_url)
                progress.add(key)
                written += 1
                if limit is not None and written >= limit:
                    return written
        except Exception as exc:  # noqa: BLE001 - errors are preserved in ledger.
            append_error(errors_path, "L0", source_id, type(exc).__name__, detail=str(exc))
    return written


def iter_source_records(
    source_id: str,
    source: dict[str, Any],
    *,
    token: str | None,
    sleep_sec: float,
) -> Iterable[ExtractedRecord]:
    owner = str(source["owner"])
    repo = str(source["repo"])
    parser = str(source["parser"])
    repo_info = github_api_json(f"https://api.github.com/repos/{owner}/{repo}", token=token)
    branch = str(repo_info.get("default_branch") or "main")
    tree = github_api_json(
        f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1",
        token=token,
    )
    paths = [item["path"] for item in tree.get("tree", []) if item.get("type") == "blob"]
    if parser == "e1_act_sections":
        yield from parse_e1(owner, repo, branch, paths, source_id, token, sleep_sec)
    elif parser == "file_per_prompt":
        yield from parse_file_per_prompt(owner, repo, branch, paths, source_id, token, sleep_sec)
    else:
        yield from parse_markdown_prompt_blocks(owner, repo, branch, paths, source_id, token, sleep_sec)


def parse_e1(
    owner: str,
    repo: str,
    branch: str,
    paths: list[str],
    source_id: str,
    token: str | None,
    sleep_sec: float,
) -> Iterable[ExtractedRecord]:
    if "prompts.csv" in paths:
        text = fetch_raw(owner, repo, branch, "prompts.csv", token)
        reader = csv.DictReader(io.StringIO(text))
        for index, row in enumerate(reader, 1):
            act = (row.get("act") or "").strip()
            prompt = (row.get("prompt") or "").strip()
            if not prompt:
                continue
            body = f"Act as {act}\n\n{prompt}" if act else prompt
            yield make_record(source_id, blob_url(owner, repo, branch, "prompts.csv", index), body, f"{repo}/prompts.csv:{index}")
        return
    readme = first_readme(paths)
    if readme:
        text = fetch_raw(owner, repo, branch, readme, token)
        yield from records_from_act_headings(source_id, owner, repo, branch, readme, text)
        time.sleep(sleep_sec)


def parse_file_per_prompt(
    owner: str,
    repo: str,
    branch: str,
    paths: list[str],
    source_id: str,
    token: str | None,
    sleep_sec: float,
) -> Iterable[ExtractedRecord]:
    markdown_paths = sorted(p for p in paths if p.lower().endswith((".md", ".txt")) and not is_index_doc(p))
    if not markdown_paths:
        markdown_paths = [p for p in paths if p.lower().endswith(".md")]
    for path in markdown_paths:
        text = fetch_raw(owner, repo, branch, path, token)
        body = strip_markdown_boilerplate(text)
        if promptish(body):
            yield make_record(source_id, blob_url(owner, repo, branch, path), body, f"{repo}/{path}")
        time.sleep(sleep_sec)


def parse_markdown_prompt_blocks(
    owner: str,
    repo: str,
    branch: str,
    paths: list[str],
    source_id: str,
    token: str | None,
    sleep_sec: float,
) -> Iterable[ExtractedRecord]:
    markdown_paths = sorted(p for p in paths if p.lower().endswith((".md", ".txt")))
    for path in markdown_paths:
        text = fetch_raw(owner, repo, branch, path, token)
        emitted = False
        for idx, block in enumerate(FENCE_RE.findall(text), 1):
            if promptish(block):
                emitted = True
                yield make_record(source_id, blob_url(owner, repo, branch, path, idx), block, f"{repo}/{path}:codeblock:{idx}")
        for idx, body in enumerate(markdown_sections(text), 1):
            if promptish(body) and len(body) >= 120:
                emitted = True
                yield make_record(source_id, blob_url(owner, repo, branch, path, idx + 1000), body, f"{repo}/{path}:section:{idx}")
        if not emitted and not is_index_doc(path):
            body = strip_markdown_boilerplate(text)
            if promptish(body) and len(body) >= 120:
                yield make_record(source_id, blob_url(owner, repo, branch, path), body, f"{repo}/{path}")
        time.sleep(sleep_sec)


def records_from_act_headings(
    source_id: str,
    owner: str,
    repo: str,
    branch: str,
    path: str,
    text: str,
) -> Iterable[ExtractedRecord]:
    for idx, match in enumerate(HEADING_RE.finditer(text), 1):
        heading = match.group(2).strip()
        body = match.group(3).strip()
        if not heading.lower().startswith("act as") and not promptish(heading):
            continue
        combined = f"{heading}\n\n{body}"
        if promptish(combined):
            yield make_record(source_id, blob_url(owner, repo, branch, path, idx), combined, f"{repo}/{path}:act:{idx}")


def markdown_sections(text: str) -> list[str]:
    sections: list[str] = []
    for match in HEADING_RE.finditer(text):
        heading = match.group(2).strip()
        body = match.group(3).strip()
        sections.append(f"{heading}\n\n{body}")
    return sections


def make_record(source_id: str, source_url: str, body: str, context: str) -> ExtractedRecord:
    return ExtractedRecord.from_body(
        body=body,
        context=context,
        lang="en",
        occurrence=Occurrence(
            source_id=source_id,
            source_url=source_url,
            collected_at=utc_now(),
            published_at=None,
        ),
    )


def github_api_json(url: str, *, token: str | None) -> dict[str, Any]:
    raw = http_get(url, token=token)
    return json.loads(raw)


def fetch_raw(owner: str, repo: str, branch: str, path: str, token: str | None) -> str:
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{quote_path(path)}"
    return http_get(url, token=token)


def http_get(url: str, *, token: str | None) -> str:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "contextwins-prompt-corpus-pipeline",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            charset = resp.headers.get_content_charset() or "utf-8"
            return data.decode(charset, errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise GitHubError(f"HTTP {exc.code} for {url}: {body[:300]}") from exc
    except urllib.error.URLError as exc:
        raise GitHubError(f"URL error for {url}: {exc}") from exc


def first_readme(paths: list[str]) -> str | None:
    for candidate in ("README.md", "readme.md", "Readme.md"):
        if candidate in paths:
            return candidate
    return next((p for p in paths if Path(p).name.lower() == "readme.md"), None)


def is_index_doc(path: str) -> bool:
    name = Path(path).name.lower()
    return name in {"readme.md", "contributing.md", "license.md", "code_of_conduct.md"} or "readme" in name


def promptish(text: str) -> bool:
    text = text.strip()
    if len(text) < 40:
        return False
    return bool(PROMPT_HINT_RE.search(text))


def strip_markdown_boilerplate(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if line.strip().startswith(("![", "[![", "# ")):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def quote_path(path: str) -> str:
    return urllib.parse.quote(path, safe="/")


def blob_url(owner: str, repo: str, branch: str, path: str, anchor_index: int | None = None) -> str:
    suffix = f"#item-{anchor_index}" if anchor_index is not None else ""
    return f"https://github.com/{owner}/{repo}/blob/{branch}/{quote_path(path)}{suffix}"
