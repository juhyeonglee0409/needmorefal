from __future__ import annotations

import re
import time
import urllib.parse
import urllib.robotparser
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

try:
    from .config import ERRORS_PATH, PROGRESS_PATH
    from .io_utils import append_error, append_ndjson, append_progress, load_progress_keys, utc_now
    from .schemas import UrlRecord, record_to_dict
    from .search_serp import load_serp_queries
except ImportError:  # pragma: no cover - direct script execution fallback.
    from config import ERRORS_PATH, PROGRESS_PATH
    from io_utils import append_error, append_ndjson, append_progress, load_progress_keys, utc_now
    from schemas import UrlRecord, record_to_dict
    from search_serp import load_serp_queries


DEFAULT_SOURCES_PATH = Path(__file__).resolve().parent / "configs" / "sources.yaml"
USER_AGENT = "Mozilla/5.0 contextwins-prompt-corpus-pipeline"


def crawl_board(
    source_id: str,
    output_path: Path,
    *,
    config_path: Path = DEFAULT_SOURCES_PATH,
    progress_path: Path = PROGRESS_PATH,
    errors_path: Path = ERRORS_PATH,
    limit: int | None = None,
) -> int:
    sources = load_serp_queries(config_path)
    config = sources.get(source_id)
    if not config:
        append_error(errors_path, "L0", source_id, "missing_board_config")
        return 0
    if config.get("enabled") is False:
        append_error(errors_path, "L0", source_id, "source_disabled", note=config.get("note"))
        return 0
    if config.get("type") not in {"community", "platform"}:
        append_error(errors_path, "L0", source_id, "unsupported_board_source_type", source_type=config.get("type"))
        return 0

    pagination = config.get("pagination") or {}
    if pagination.get("type") != "query":
        append_error(errors_path, "L0", source_id, "unsupported_pagination_type", pagination_type=pagination.get("type"))
        return 0

    progress = load_progress_keys(progress_path)
    written = 0
    max_pages = int(pagination.get("max_pages") or 1)
    start_page = int(pagination.get("start") or 1)
    empty_pages = 0
    for page in range(start_page, start_page + max_pages):
        if limit is not None and written >= limit:
            return written
        list_url = build_list_url(config, page)
        if config.get("respect_robots") is True and not robots_allows(list_url):
            append_error(errors_path, "L0", source_id, "robots_disallow", url=list_url)
            break
        try:
            posts = parse_list_page(fetch_list_html(list_url, config), config, list_url)
        except Exception as exc:  # noqa: BLE001 - preserve in errors ledger.
            append_error(errors_path, "L0", source_id, type(exc).__name__, url=list_url, detail=str(exc))
            if "404" in str(exc) or "410" in str(exc):
                continue
            break
        if not posts:
            empty_pages += 1
            if empty_pages >= int(config.get("stop_after_empty_pages") or 1):
                break
        else:
            empty_pages = 0
        for post in posts:
            url = str(post["url"])
            title = post.get("title")
            progress_key = ("L0", source_id, url)
            if progress_key in progress:
                continue
            record = record_to_dict(UrlRecord(url=url, source_id=source_id, title=title, collected_at=utc_now()))
            if config.get("render") == "browser":
                record["render"] = "browser"
            append_ndjson(output_path, record)
            append_progress(progress_path, "L0", source_id, url)
            progress.add(progress_key)
            written += 1
            if limit is not None and written >= limit:
                return written
        time.sleep(float(config.get("delay_sec") or 2))
    return written


def crawl_sources(
    source_ids: list[str],
    output_dir: Path,
    *,
    config_path: Path = DEFAULT_SOURCES_PATH,
    progress_path: Path = PROGRESS_PATH,
    errors_path: Path = ERRORS_PATH,
    limit: int | None = None,
) -> int:
    total = 0
    for source_id in source_ids:
        total += crawl_board(
            source_id,
            output_dir / f"urls_{source_id}.ndjson",
            config_path=config_path,
            progress_path=progress_path,
            errors_path=errors_path,
            limit=limit,
        )
    return total


def build_list_url(config: dict[str, Any], page: int) -> str:
    base_url = str(config["base_url"]).rstrip("/")
    board_path = str(config.get("board_path") or "/")
    url = urllib.parse.urljoin(base_url + "/", board_path.lstrip("/"))
    pagination = config.get("pagination") or {}
    param = str(pagination.get("param") or "page")
    parsed = urllib.parse.urlparse(url)
    query = dict(urllib.parse.parse_qsl(parsed.query, keep_blank_values=True))
    query[param] = str(page)
    return urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(query)))


def fetch_list_html(url: str, config: dict[str, Any]) -> str:
    if config.get("render") == "browser":
        try:
            from .fetch_browser import fetch_rendered_html
        except ImportError:  # pragma: no cover - direct script execution fallback.
            from fetch_browser import fetch_rendered_html

        return fetch_rendered_html(url, delay_sec=float(config.get("render_delay_sec") or config.get("delay_sec") or 2.0))
    return fetch_html(url)


def fetch_html(url: str) -> str:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            return fetch_html_once(url)
        except Exception as exc:  # noqa: BLE001 - retry then raise.
            last_error = exc
            if attempt < 2 and "HTTP 404" not in str(exc) and "HTTP 410" not in str(exc):
                time.sleep(30 if "429" in str(exc) else 2)
    raise RuntimeError(f"fetch failed: {last_error}")


def fetch_html_once(url: str) -> str:
    try:
        import requests  # type: ignore
    except ImportError:
        return fetch_html_urllib(url)

    response = requests.get(url, timeout=10, headers={"User-Agent": USER_AGENT})
    if response.status_code == 429:
        raise RuntimeError("HTTP 429")
    if response.status_code in {404, 410}:
        raise RuntimeError(f"HTTP {response.status_code}")
    response.raise_for_status()
    response.encoding = response.encoding or "utf-8"
    return response.text


def fetch_html_urllib(url: str) -> str:
    import urllib.request

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=10) as response:
        status = getattr(response, "status", 200)
        if status == 429:
            raise RuntimeError("HTTP 429")
        if status in {404, 410}:
            raise RuntimeError(f"HTTP {status}")
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


_ROBOTS_CACHE: dict[str, urllib.robotparser.RobotFileParser] = {}


def robots_allows(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    parser = _ROBOTS_CACHE.get(base)
    if parser is None:
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(urllib.parse.urljoin(base, "/robots.txt"))
        try:
            parser.read()
        except Exception:  # noqa: BLE001 - robots fetch failure should not imply disallow.
            return True
        _ROBOTS_CACHE[base] = parser
    return parser.can_fetch(USER_AGENT, url)


def parse_list_page(html: str, config: dict[str, Any], list_url: str) -> list[dict[str, str | None]]:
    selectors = config.get("selectors") or {}
    post_link_selector = selectors.get("post_link")
    if not post_link_selector:
        raise ValueError("selectors.post_link is missing")
    title_selector = selectors.get("title")
    title_filter = config.get("title_filter")
    title_re = re.compile(str(title_filter), re.I) if title_filter else None
    base_url = str(config["base_url"]).rstrip("/")
    posts: list[dict[str, str | None]] = []
    seen_urls: set[str] = set()
    for link in select_links(html, str(post_link_selector), title_selector):
        href = link.get("href")
        if not href:
            continue
        url = normalize_url(urllib.parse.urljoin(base_url + "/", href), list_url)
        if not should_keep_url(url, config) or url in seen_urls:
            continue
        title = normalize_space(str(link.get("title") or "")) or None
        if title_re and not title_re.search(title or ""):
            continue
        seen_urls.add(url)
        posts.append({"url": url, "title": title})
    return posts


def select_links(html: str, selector: str, title_selector: str | None) -> list[dict[str, str | None]]:
    try:
        from bs4 import BeautifulSoup  # type: ignore
    except ImportError:
        return select_links_fallback(html, selector)

    soup = BeautifulSoup(html, "html.parser")
    links: list[dict[str, str | None]] = []
    for element in soup.select(selector):
        href = element.get("href")
        if not href:
            continue
        title_element = element.select_one(str(title_selector)) if title_selector else None
        title = title_element.get_text(" ", strip=True) if title_element else element.get_text(" ", strip=True)
        if not title:
            title = element.get("title") or element.get("aria-label")
        links.append({"href": href, "title": normalize_space(title) if title else None})
    return links


def select_links_fallback(html: str, selector: str) -> list[dict[str, str | None]]:
    parser = AnchorFallbackParser()
    parser.feed(html)
    return [
        {"href": anchor["href"], "title": normalize_space(anchor["text"] or anchor["title"] or anchor["aria_label"])}
        for anchor in parser.anchors
        if selector_matches_anchor(selector, anchor)
    ]


class AnchorFallbackParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, dict[str, str]]] = []
        self.current: dict[str, Any] | None = None
        self.anchors: list[dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = {k: v or "" for k, v in attrs}
        if tag.lower() == "a":
            self.current = {
                "href": attr_dict.get("href", ""),
                "class": attr_dict.get("class", ""),
                "title": attr_dict.get("title", ""),
                "aria_label": attr_dict.get("aria-label", ""),
                "ancestors": list(self.stack),
                "text_parts": [],
            }
        self.stack.append((tag.lower(), attr_dict))

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self.current is not None:
            self.current["text"] = normalize_space(" ".join(self.current.pop("text_parts", [])))
            self.anchors.append(self.current)
            self.current = None
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag.lower():
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        if self.current is not None:
            self.current["text_parts"].append(data)


def selector_matches_anchor(selector: str, anchor: dict[str, Any]) -> bool:
    selectors = [item.strip() for item in selector.split(",") if item.strip()]
    return any(single_selector_matches_anchor(item, anchor) for item in selectors)


def single_selector_matches_anchor(selector: str, anchor: dict[str, Any]) -> bool:
    href = str(anchor.get("href") or "")
    anchor_classes = set(str(anchor.get("class") or "").split())
    if selector == "a" or selector.endswith(" a"):
        return True
    class_match = re.fullmatch(r"a\.([A-Za-z0-9_-]+)", selector)
    if class_match:
        return class_match.group(1) in anchor_classes
    href_match = re.fullmatch(r"a\[href\*=['\"]([^'\"]+)['\"]\]", selector)
    if href_match:
        return href_match.group(1) in href
    ancestor_match = re.fullmatch(r"([A-Za-z0-9_-]+)\.([A-Za-z0-9_-]+)\s+a", selector)
    if ancestor_match:
        tag, klass = ancestor_match.groups()
        return any(ancestor_tag == tag and klass in str(attrs.get("class") or "").split() for ancestor_tag, attrs in anchor["ancestors"])
    if selector.startswith("a[") and "href*=" in selector:
        fragments = re.findall(r"href\*=['\"]([^'\"]+)['\"]", selector)
        return any(fragment in href for fragment in fragments)
    return False


def normalize_url(url: str, list_url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    clean_query = [(k, v) for k, v in query if not k.lower().startswith(("utm_", "fbclid", "gclid"))]
    return urllib.parse.urlunparse(parsed._replace(fragment="", query=urllib.parse.urlencode(clean_query)))


def should_keep_url(url: str, config: dict[str, Any]) -> bool:
    include = config.get("include_url_regex")
    exclude = config.get("exclude_url_regex")
    if include and not re.search(str(include), url):
        return False
    if exclude and re.search(str(exclude), url):
        return False
    return True


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
