from __future__ import annotations

import ast
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

try:
    from .config import ERRORS_PATH, PROGRESS_PATH, google_cse_credentials, naver_credentials, serper_api_key
    from .io_utils import append_error, append_ndjson, append_progress, load_progress_keys, utc_now
    from .schemas import UrlRecord, record_to_dict
except ImportError:  # pragma: no cover - direct script execution fallback.
    from config import ERRORS_PATH, PROGRESS_PATH, google_cse_credentials, naver_credentials, serper_api_key
    from io_utils import append_error, append_ndjson, append_progress, load_progress_keys, utc_now
    from schemas import UrlRecord, record_to_dict


DEFAULT_SERP_QUERIES_PATH = Path(__file__).resolve().parent / "configs" / "serp_queries.yaml"


def search_google_cse(
    queries: list[str],
    output_path: Path,
    *,
    progress_path: Path = PROGRESS_PATH,
    errors_path: Path = ERRORS_PATH,
    limit: int | None = None,
    sleep_sec: float = 2.0,
    source_id: str = "SERP",
) -> int:
    key, cx = google_cse_credentials()
    progress = load_progress_keys(progress_path)
    written = 0
    seen_urls: set[str] = set()
    for query in queries:
        start = 1
        while start <= 91:
            if limit is not None and written >= limit:
                return written
            try:
                payload = google_cse_request(key=key, cx=cx, query=query, start=start)
            except Exception as exc:  # noqa: BLE001 - preserve in errors ledger.
                append_error(errors_path, "L0", source_id, type(exc).__name__, query=query, detail=str(exc))
                break
            items = payload.get("items") or []
            if not items:
                break
            for item in items:
                url = str(item.get("link") or "").strip()
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                progress_key = ("L0", source_id, url)
                if progress_key in progress:
                    continue
                record = UrlRecord(url=url, source_id=source_id, title=item.get("title"), collected_at=utc_now())
                append_ndjson(output_path, record_to_dict(record))
                append_progress(progress_path, "L0", source_id, url)
                progress.add(progress_key)
                written += 1
                if limit is not None and written >= limit:
                    return written
            start += 10
            time.sleep(sleep_sec)
    return written


def search_sources(
    source_ids: list[str],
    output_dir: Path,
    *,
    query_config_path: Path = DEFAULT_SERP_QUERIES_PATH,
    progress_path: Path = PROGRESS_PATH,
    errors_path: Path = ERRORS_PATH,
    limit: int | None = None,
    sleep_sec: float = 2.0,
) -> int:
    config = load_serp_queries(query_config_path)
    total = 0
    for source_id in source_ids:
        source = config.get(source_id)
        if not source:
            append_error(errors_path, "L0", source_id, "missing_serp_query_config")
            continue
        engine = source.get("engine")
        if engine == "google_cse":
            output_path = output_dir / f"urls_{source_id}.ndjson"
            total += search_google_cse(
                list(source.get("queries") or []),
                output_path,
                progress_path=progress_path,
                errors_path=errors_path,
                limit=limit,
                sleep_sec=sleep_sec,
                source_id=source_id,
            )
            continue
        if engine == "serper":
            output_path = output_dir / f"urls_{source_id}.ndjson"
            total += search_serper(
                list(source.get("queries") or []),
                output_path,
                progress_path=progress_path,
                errors_path=errors_path,
                limit=limit,
                sleep_sec=sleep_sec,
                source_id=source_id,
            )
            continue
        if engine == "naver":
            output_path = output_dir / f"urls_{source_id}.ndjson"
            total += search_naver(
                list(source.get("queries") or []),
                output_path,
                source_id=source_id,
                progress_path=progress_path,
                errors_path=errors_path,
                limit=limit,
                sleep_sec=sleep_sec,
            )
            continue
        else:
            append_error(errors_path, "L0", source_id, "unsupported_search_engine", engine=source.get("engine"))
            continue
    return total


def google_cse_request(*, key: str, cx: str, query: str, start: int) -> dict[str, Any]:
    params = {"key": key, "cx": cx, "q": query, "start": start, "num": 10}
    url = "https://www.googleapis.com/customsearch/v1?" + urllib.parse.urlencode(params)
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            return http_json_get(url, headers={"User-Agent": "contextwins-prompt-corpus-pipeline"})
        except Exception as exc:  # noqa: BLE001 - retry then raise.
            last_error = exc
            if attempt < 2:
                time.sleep(30 if "HTTP 429" in str(exc) else 2)
    raise RuntimeError(f"Google CSE request failed: {last_error}")


def search_serper(
    queries: list[str],
    output_path: Path,
    *,
    progress_path: Path = PROGRESS_PATH,
    errors_path: Path = ERRORS_PATH,
    limit: int | None = None,
    sleep_sec: float = 2.0,
    source_id: str = "SERP",
) -> int:
    api_key = serper_api_key()
    if not api_key:
        raise RuntimeError("SERPER_API_KEY is missing")
    progress = load_progress_keys(progress_path)
    written = 0
    seen_urls: set[str] = set()
    for query in queries:
        page = 1
        while page <= 10:
            if limit is not None and written >= limit:
                return written
            try:
                payload = serper_request(api_key=api_key, query=query, page=page)
            except Exception as exc:  # noqa: BLE001 - preserve in errors ledger.
                append_error(errors_path, "L0", source_id, type(exc).__name__, query=query, detail=str(exc))
                break
            items = payload.get("organic") or []
            if not items:
                break
            for item in items:
                url = str(item.get("link") or "").strip()
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                progress_key = ("L0", source_id, url)
                if progress_key in progress:
                    continue
                record = UrlRecord(url=url, source_id=source_id, title=item.get("title"), collected_at=utc_now(), snippet=item.get("snippet"))
                append_ndjson(output_path, record_to_dict(record))
                append_progress(progress_path, "L0", source_id, url)
                progress.add(progress_key)
                written += 1
                if limit is not None and written >= limit:
                    return written
            page += 1
            time.sleep(sleep_sec)
    return written


def serper_request(*, api_key: str, query: str, page: int = 1, num: int = 10) -> dict[str, Any]:
    url = "https://google.serper.dev/search"
    body = json.dumps({"q": query, "num": num, "page": page}).encode("utf-8")
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=15) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return json.loads(response.read().decode(charset, errors="replace"))
        except Exception as exc:  # noqa: BLE001 - retry then raise.
            last_error = exc
            if attempt < 2:
                time.sleep(30 if "429" in str(exc) else 2)
    raise RuntimeError(f"Serper request failed: {last_error}")


def search_naver(
    queries: list[str],
    output_path: Path,
    *,
    source_id: str,
    progress_path: Path = PROGRESS_PATH,
    errors_path: Path = ERRORS_PATH,
    limit: int | None = None,
    sleep_sec: float = 1.0,
) -> int:
    client_id, client_secret = naver_credentials()
    progress = load_progress_keys(progress_path)
    written = 0
    seen_urls: set[str] = set()
    for query in queries:
        start = 1
        while start <= 1000:
            if limit is not None and written >= limit:
                return written
            try:
                payload = naver_blog_request(
                    client_id=client_id,
                    client_secret=client_secret,
                    query=query,
                    start=start,
                )
            except Exception as exc:  # noqa: BLE001 - preserve in errors ledger.
                append_error(errors_path, "L0", source_id, type(exc).__name__, query=query, detail=str(exc))
                break
            items = payload.get("items") or []
            if not items:
                break
            for item in items:
                url = str(item.get("link") or "").strip()
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                progress_key = ("L0", source_id, url)
                if progress_key in progress:
                    continue
                record = UrlRecord(
                    url=url,
                    source_id=source_id,
                    title=strip_html(str(item.get("title") or "")),
                    collected_at=utc_now(),
                )
                append_ndjson(output_path, record_to_dict(record))
                append_progress(progress_path, "L0", source_id, url)
                progress.add(progress_key)
                written += 1
                if limit is not None and written >= limit:
                    return written
            start += 100
            time.sleep(sleep_sec)
    return written


def naver_blog_request(*, client_id: str, client_secret: str, query: str, start: int) -> dict[str, Any]:
    params = {"query": query, "display": 100, "start": start, "sort": "sim"}
    headers = {
        "User-Agent": "contextwins-prompt-corpus-pipeline",
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    url = "https://openapi.naver.com/v1/search/blog?" + urllib.parse.urlencode(params)
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            return http_json_get(url, headers=headers)
        except Exception as exc:  # noqa: BLE001 - retry then raise.
            last_error = exc
            if attempt < 2:
                time.sleep(30 if "HTTP 429" in str(exc) else 2)
    raise RuntimeError(f"Naver search request failed: {last_error}")


def http_json_get(url: str, *, headers: dict[str, str]) -> dict[str, Any]:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as response:
        status = getattr(response, "status", 200)
        if status == 429:
            raise RuntimeError("HTTP 429")
        if status >= 400:
            raise RuntimeError(f"HTTP {status}")
        charset = response.headers.get_content_charset() or "utf-8"
        return json.loads(response.read().decode(charset, errors="replace"))


def strip_html(text: str) -> str:
    import re

    return re.sub(r"<[^>]+>", "", text).replace("&quot;", '"').replace("&amp;", "&").strip()


def load_serp_queries(path: Path) -> dict[str, dict[str, Any]]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        return parse_yaml_subset(path.read_text(encoding="utf-8"))
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"invalid SERP query config: {path}")
    return data


def parse_yaml_subset(text: str) -> dict[str, dict[str, Any]]:
    lines = [line.rstrip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]
    for index, line in enumerate(lines):
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if stripped.startswith("- "):
            if not isinstance(parent, list):
                raise ValueError(f"YAML subset parse error near list item: {line}")
            parent.append(parse_scalar(stripped[2:].strip()))
            continue
        if ":" not in stripped:
            raise ValueError(f"YAML subset parse error near line: {line}")
        key, raw_value = stripped.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if not isinstance(parent, dict):
            raise ValueError(f"YAML subset parse error near mapping item: {line}")
        if raw_value:
            parent[key] = parse_scalar(raw_value)
            continue
        next_line = next((candidate for candidate in lines[index + 1 :] if candidate.strip()), "")
        next_stripped = next_line.strip()
        child: Any = [] if next_stripped.startswith("- ") else {}
        parent[key] = child
        stack.append((indent, child))
    return root


def parse_scalar(value: str) -> Any:
    if value in {"null", "Null", "NULL", "~"}:
        return None
    if value in {"true", "True", "TRUE"}:
        return True
    if value in {"false", "False", "FALSE"}:
        return False
    if value.startswith("[") and value.endswith("]"):
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return value
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1].replace('\\"', '"')
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    if value.isdigit():
        return int(value)
    try:
        return float(value)
    except ValueError:
        return value
