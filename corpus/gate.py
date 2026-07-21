from __future__ import annotations

import json as _json
import re
import time
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

try:
    from .config import ERRORS_PATH, LLM_GATE_MODEL, PROGRESS_PATH
    from .io_utils import append_error, append_ndjson, append_progress, load_progress_keys, read_ndjson, utc_now
    from .llm_client import llm_json_object
    from .normalize import count_tokens
except ImportError:  # pragma: no cover - direct script execution fallback.
    from config import ERRORS_PATH, LLM_GATE_MODEL, PROGRESS_PATH
    from io_utils import append_error, append_ndjson, append_progress, load_progress_keys, read_ndjson, utc_now
    from llm_client import llm_json_object
    from normalize import count_tokens


PROMPT_KEYWORDS = re.compile(r"프롬프트|prompt|GPT|ChatGPT|Claude|시스템\s*메시지|system\s*prompt", re.IGNORECASE)

GATE_SYSTEM_PROMPT = """이 텍스트에 LLM에게 보낼 수 있는 실제 프롬프트 표본이 포함되어 있는지 판정한다.

프롬프트에 '관한' 설명만 있는 글은 프롬프트가 '있는' 글이 아니다.
"역할을 지정하면 좋습니다"는 설명이고, "너는 데이터 분석가야"가 표본이다.

판정: 복사해서 LLM에 붙여넣을 수 있는 프롬프트 텍스트가 하나라도 있는가?

JSON으로만 응답하라: {"pass": true/false, "reason": "한 줄"}"""


def regex_gate(text: str) -> str:
    hits = len(PROMPT_KEYWORDS.findall(text))
    if hits < 2:
        return "reject"
    return "uncertain"


def gate_urls(
    input_path: Path,
    output_path: Path,
    *,
    progress_path: Path = PROGRESS_PATH,
    errors_path: Path = ERRORS_PATH,
    sleep_sec: float = 2.0,
    llm_gate: bool = True,
) -> int:
    progress = load_progress_keys(progress_path)
    rows = list(read_ndjson(input_path))
    total = len(rows)
    skipped = 0
    processed = 0
    written = 0
    errors = 0
    rejected = 0
    discovered_refs: list[dict[str, Any]] = []
    existing_urls = {str(r.get("url")) for r in rows}
    for row in rows:
        source_id = str(row.get("source_id") or "")
        url = str(row.get("url") or "")
        if not source_id or not url:
            append_error(errors_path, "L0.5", source_id, "invalid_url_record", raw=row)
            continue
        progress_key = ("L0.5", source_id, url)
        if progress_key in progress:
            skipped += 1
            continue
        processed += 1
        try:
            page = page_from_record_or_fetch(row)
            page_text = page["page_text"]
            for ref_url in page.get("referenced_urls") or []:
                if ref_url not in existing_urls:
                    discovered_refs.append({"url": ref_url, "source_id": source_id, "title": f"[ref]", "collected_at": utc_now()})
                    existing_urls.add(ref_url)
            regex_result = regex_gate(page_text)
            if regex_result == "reject":
                append_progress(progress_path, "L0.5", source_id, url, status="reject_regex")
                progress.add(progress_key)
                rejected += 1
                if processed % 20 == 0:
                    _log_gate_progress(source_id, processed, skipped, total, written, rejected, errors)
                continue
            image_urls = page.get("image_urls") or []
            if image_urls:
                try:
                    from .vision_ocr import ocr_threads_images
                except ImportError:
                    from vision_ocr import ocr_threads_images
                ocr_texts = ocr_threads_images(image_urls)
                if ocr_texts:
                    page_text = page_text + "\n\n[OCR]\n" + "\n---\n".join(ocr_texts)
                    page["page_text"] = page_text
            if llm_gate:
                decision = llm_gate_page(page_text)
                passed = bool(decision.get("pass"))
                reason = str(decision.get("reason") or "")
            else:
                passed = True
                reason = "regex_only_uncertain"
            if passed:
                output = {
                    "url": url,
                    "source_id": source_id,
                    "title": row.get("title"),
                    "collected_at": row.get("collected_at") or utc_now(),
                    "page_text": page_text,
                    "structured_blocks": page.get("structured_blocks") or [],
                    "gate": {"regex": regex_result, "llm": llm_gate, "pass": True, "reason": reason},
                }
                append_ndjson(output_path, output)
                written += 1
                append_progress(progress_path, "L0.5", source_id, url)
            else:
                rejected += 1
                append_progress(progress_path, "L0.5", source_id, url, status="reject_llm")
            progress.add(progress_key)
        except Exception as exc:  # noqa: BLE001 - preserve in errors ledger.
            errors += 1
            append_error(errors_path, "L0.5", source_id, type(exc).__name__, url=url, detail=str(exc))
            append_progress(progress_path, "L0.5", source_id, url, status="error")
            progress.add(progress_key)
        if processed % 20 == 0:
            _log_gate_progress(source_id, processed, skipped, total, written, rejected, errors)
        needed_fetch = not (isinstance(row.get("page_text"), str) and row["page_text"].strip())
        time.sleep(sleep_sec if needed_fetch else 0.3)
    if discovered_refs:
        for ref in discovered_refs:
            append_ndjson(input_path, ref)
        print(f"  [gate] discovered {len(discovered_refs)} referenced thread URLs", flush=True)
    if processed > 0:
        _log_gate_progress(source_id, processed, skipped, total, written, rejected, errors)
    return written


def _log_gate_progress(source_id: str, processed: int, skipped: int, total: int, passed: int, rejected: int, errors: int) -> None:
    remaining = total - skipped - processed
    print(f"  [gate {source_id}] {processed}/{total - skipped} done ({skipped} skip) | pass {passed} reject {rejected} err {errors} | {remaining} left", flush=True)


def page_from_record_or_fetch(row: dict[str, Any]) -> dict[str, Any]:
    page_text = row.get("page_text")
    if isinstance(page_text, str) and page_text.strip():
        return {"page_text": normalize_text(page_text), "structured_blocks": row.get("structured_blocks") or []}
    try:
        return fetch_page_text(str(row["url"]), render=row.get("render"))
    except Exception:
        snippet = row.get("snippet")
        if isinstance(snippet, str) and snippet.strip():
            combined = f"{row.get('title', '')}\n\n{snippet}"
            return {"page_text": normalize_text(combined), "structured_blocks": []}
        raise


def fetch_page_text(url: str, *, render: Any = None) -> dict[str, Any]:
    if _is_threads_post(url):
        return _fetch_threads_post(url)
    if _is_reddit_thread(url):
        return _fetch_reddit_json(url)
    for attempt in range(2):
        try:
            if render == "browser":
                return html_to_text(fetch_rendered_html(url))
            return html_to_text(fetch_html(url))
        except RuntimeError as exc:
            if "HTTP 429" in str(exc) and attempt == 0:
                time.sleep(30)
                continue
            raise
    raise RuntimeError("unreachable fetch retry state")


_THREADS_POST_RE = re.compile(r"https?://(?:www\.)?threads\.net/@[\w.]+/post/\w+")
_REDDIT_THREAD_RE = re.compile(r"https?://(?:www\.)?reddit\.com/r/\w+/comments/\w+")


def _is_threads_post(url: str) -> bool:
    return bool(_THREADS_POST_RE.match(url))


def _fetch_threads_post(url: str) -> dict[str, Any]:
    html = fetch_rendered_html(url)
    try:
        from bs4 import BeautifulSoup  # type: ignore
    except ImportError:
        return html_to_text(html)

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["script", "style", "noscript"]):
        tag.decompose()

    body_text = soup.get_text("\n", strip=True)
    lines = body_text.split("\n")

    segments: list[list[str]] = []
    current: list[str] = []
    capturing = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped == "더 보기":
            capturing = True
            current = []
            continue
        if capturing:
            if stripped == "좋아요":
                if current:
                    segments.append(current)
                capturing = False
                continue
            current.append(stripped)

    seen: set[str] = set()
    unique: list[list[str]] = []
    for seg in segments:
        text = "\n".join(seg)
        if len(text) < 20:
            continue
        key = seg[0]
        if key not in seen:
            seen.add(key)
            unique.append(seg)

    if not unique:
        result = html_to_text(html)
        result["referenced_urls"] = _extract_threads_refs(soup, url)
        result["image_urls"] = _extract_threads_images(soup)
        return result

    all_lines: list[str] = []
    blocks: list[str] = []
    for seg in unique:
        all_lines.extend(seg)
        for line in seg:
            if len(line) > 80:
                blocks.append(normalize_text(line))

    page_text = normalize_text("\n".join(all_lines))
    return {
        "page_text": page_text,
        "structured_blocks": blocks,
        "referenced_urls": _extract_threads_refs(soup, url),
        "image_urls": _extract_threads_images(soup),
    }


def _extract_threads_refs(soup: Any, current_url: str) -> list[str]:
    from urllib.parse import urlparse
    current_path = urlparse(current_url).path.rstrip("/")
    refs: list[str] = []
    seen: set[str] = set()
    for a in soup.find_all("a", attrs={"role": "link"}, href=True):
        href = str(a["href"])
        if "/@" in href and "/post/" in href and "/media" not in href and href not in seen:
            normalized = href.rstrip("/")
            if normalized == current_path:
                continue
            full = f"https://www.threads.net{normalized}" if normalized.startswith("/") else normalized
            seen.add(href)
            refs.append(full)
    return refs


def _extract_threads_images(soup: Any) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for img in soup.find_all("img", src=True):
        src = str(img.get("src", ""))
        alt = str(img.get("alt", ""))
        if "프로필" in alt or "profile" in alt.lower():
            continue
        if "scontent" not in src and "cdninstagram" not in src and "fbcdn" not in src:
            continue
        if src not in seen:
            seen.add(src)
            urls.append(src)
    return urls


def _is_reddit_thread(url: str) -> bool:
    return bool(_REDDIT_THREAD_RE.match(url))


def _fetch_reddit_json(url: str) -> dict[str, Any]:
    json_url = url.replace("www.reddit.com", "old.reddit.com").rstrip("/") + ".json"
    req = urllib.request.Request(json_url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = _json.loads(resp.read().decode("utf-8", errors="replace"))

    parts: list[str] = []
    blocks: list[str] = []

    post = data[0]["data"]["children"][0]["data"]
    title = post.get("title", "")
    selftext = post.get("selftext", "")
    if title:
        parts.append(f"# {title}")
    if selftext:
        parts.append(selftext)
        blocks.append(normalize_text(selftext))

    def walk_comments(children: list[dict]) -> None:
        for child in children:
            if child.get("kind") != "t1":
                continue
            body = child["data"].get("body", "")
            if body and body != "[deleted]" and body != "[removed]":
                parts.append(body)
                if len(body) > 80:
                    blocks.append(normalize_text(body))
            replies = child["data"].get("replies")
            if isinstance(replies, dict):
                walk_comments(replies["data"]["children"])

    if len(data) > 1:
        walk_comments(data[1]["data"]["children"])

    return {"page_text": normalize_text("\n\n".join(parts)), "structured_blocks": blocks}


def fetch_rendered_html(url: str) -> str:
    try:
        from .fetch_browser import fetch_rendered_html as _fetch_rendered_html
    except ImportError:  # pragma: no cover - direct script execution fallback.
        from fetch_browser import fetch_rendered_html as _fetch_rendered_html

    return _fetch_rendered_html(url)


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 contextwins-prompt-corpus-pipeline"})
    with urllib.request.urlopen(req, timeout=10) as response:
        status = getattr(response, "status", 200)
        if status == 429:
            raise RuntimeError("HTTP 429")
        if status >= 400:
            raise RuntimeError(f"HTTP {status}")
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def html_to_text(html: str) -> dict[str, Any]:
    try:
        from bs4 import BeautifulSoup  # type: ignore
    except ImportError:
        parser = HTMLTextFallbackParser()
        parser.feed(html)
        return {"page_text": normalize_text(" ".join(parser.text_parts)), "structured_blocks": parser.structured_blocks}

    soup = BeautifulSoup(html, "html.parser")
    structured_blocks = [
        normalize_text(block.get_text("\n", strip=True))
        for block in soup.find_all(["code", "pre", "blockquote"])
        if block.get_text(strip=True)
    ]
    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    page_text = normalize_text(soup.get_text("\n", strip=True))
    return {"page_text": page_text, "structured_blocks": structured_blocks}


class HTMLTextFallbackParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.structured_stack: list[str] = []
        self.current_structured: list[str] = []
        self.structured_blocks: list[str] = []
        self.text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "nav", "footer", "header", "aside"}:
            self.skip_depth += 1
        if tag in {"code", "pre", "blockquote"}:
            self.structured_stack.append(tag)
            self.current_structured = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "nav", "footer", "header", "aside"} and self.skip_depth:
            self.skip_depth -= 1
        if self.structured_stack and tag == self.structured_stack[-1]:
            text = normalize_text(" ".join(self.current_structured))
            if text:
                self.structured_blocks.append(text)
            self.structured_stack.pop()
            self.current_structured = []

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        self.text_parts.append(data)
        if self.structured_stack:
            self.current_structured.append(data)


def llm_gate_page(page_text: str) -> dict[str, Any]:
    truncated = truncate_tokens(page_text, 2000)
    result = llm_json_object(
        system_prompt=GATE_SYSTEM_PROMPT,
        user_prompt=f"<page_text>\n{truncated}\n</page_text>",
        max_tokens=120,
        model_override=LLM_GATE_MODEL,
    )
    if "pass" not in result:
        raise ValueError("gate response missing pass")
    return result


def truncate_tokens(text: str, max_tokens: int) -> str:
    if count_tokens(text) <= max_tokens:
        return text
    tokens = re.findall(r"\w+|[^\s\w]", text, re.UNICODE)
    return " ".join(tokens[:max_tokens])


def normalize_text(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", text)).strip()
