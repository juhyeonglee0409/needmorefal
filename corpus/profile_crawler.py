from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

try:
    from .fetch_browser import fetch_profile_posts
    from .io_utils import append_ndjson, load_progress_keys, utc_now
except ImportError:
    from fetch_browser import fetch_profile_posts
    from io_utils import append_ndjson, load_progress_keys, utc_now

POST_URL_RE = re.compile(r'/@([^/]+)/post/([A-Za-z0-9_-]+)')


def extract_post_urls_from_html(html: str, author: str) -> list[str]:
    matches = POST_URL_RE.findall(html)
    seen = set()
    urls = []
    for match_author, post_id in matches:
        if match_author != author:
            continue
        url = f"https://www.threads.net/@{author}/post/{post_id}"
        if url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def crawl_profiles(
    authors: list[dict[str, Any]],
    output_path: Path,
    *,
    progress_path: Path | None = None,
    max_scrolls: int = 15,
    scroll_pause: float = 2.0,
    sleep_between: float = 2.0,
) -> dict[str, Any]:
    if progress_path is None:
        progress_path = output_path.parent / "progress.ndjson"
    existing_urls = load_progress_keys(progress_path)

    total_authors = len(authors)
    total_new = 0
    total_skipped = 0
    errors = 0

    for i, entry in enumerate(authors, 1):
        author = entry["author"]
        profile_url = f"https://www.threads.net/@{author}"

        try:
            html = fetch_profile_posts(
                profile_url,
                max_scrolls=max_scrolls,
                scroll_pause=scroll_pause,
            )
        except Exception as e:
            print(f"  [{i}/{total_authors}] @{author} ERROR: {e}")
            errors += 1
            time.sleep(sleep_between)
            continue

        post_urls = extract_post_urls_from_html(html, author)
        new_urls = [u for u in post_urls if u not in existing_urls]

        for url in new_urls:
            append_ndjson(output_path, {
                "url": url,
                "source_id": entry.get("source_id", "P1"),
                "collected_at": utc_now(),
                "origin": "profile_crawl",
                "author": author,
            })

        total_new += len(new_urls)
        total_skipped += len(post_urls) - len(new_urls)
        existing_urls.update(new_urls)

        print(
            f"  [{i}/{total_authors}] @{author}: "
            f"{len(post_urls)} posts, {len(new_urls)} new, "
            f"{len(post_urls) - len(new_urls)} already seen"
        )

        if i < total_authors:
            time.sleep(sleep_between)

    return {
        "authors_crawled": total_authors,
        "new_urls": total_new,
        "skipped_existing": total_skipped,
        "errors": errors,
    }


def build_author_list(progress_path: Path, min_pass: int = 1) -> list[dict[str, Any]]:
    from collections import defaultdict

    stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"pass": 0, "total": 0, "source_ids": set()}
    )

    for line in open(progress_path, encoding="utf-8"):
        try:
            r = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        url = r.get("url", "")
        if "threads.net" not in url:
            continue
        m = re.search(r'threads\.net/@([^/]+)/', url)
        if not m:
            continue
        author = m.group(1)
        stats[author]["total"] += 1
        if r.get("source_id"):
            stats[author]["source_ids"].add(r["source_id"])
        if r.get("status") == "done":
            stats[author]["pass"] += 1

    authors = []
    for author, s in stats.items():
        if s["pass"] >= min_pass:
            authors.append({
                "author": author,
                "pass_count": s["pass"],
                "total_seen": s["total"],
                "rate": s["pass"] / max(s["total"], 1),
                "source_id": sorted(s["source_ids"])[0] if s["source_ids"] else "P1",
            })

    authors.sort(key=lambda x: -x["pass_count"])
    return authors
