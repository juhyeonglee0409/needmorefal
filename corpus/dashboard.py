#!/usr/bin/env python3
"""Prompt corpus pipeline — static HTML monitoring dashboard.

Usage:
    python dashboard.py              # generate & open in browser
    python dashboard.py --no-open    # generate only
"""
from __future__ import annotations

import json
import sys
import webbrowser
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parent
DATA_DIR = TOOL_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
OUT_PATH = DATA_DIR / "dashboard.html"


def read_ndjson(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def fmt_size(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024 * 1024):.1f} MB"


def fmt_num(n: int) -> str:
    return f"{n:,}"


def collect_stats() -> dict:
    s: dict = {}

    # --- raw ---
    raw_files = sorted(RAW_DIR.glob("*.ndjson")) if RAW_DIR.exists() else []
    raw_per_file: dict[str, int] = {}
    raw_all: list[dict] = []
    for f in raw_files:
        rows = read_ndjson(f)
        raw_per_file[f.stem] = len(rows)
        raw_all.extend(rows)
    s["raw_per_file"] = raw_per_file
    s["raw_total"] = sum(raw_per_file.values())

    source_counts: Counter = Counter()
    for r in raw_all:
        for occ in r.get("occurrences", []):
            source_counts[occ.get("source_id", "?")] += 1
    if not source_counts and raw_all:
        source_counts = Counter(raw_per_file)
    s["source_counts"] = dict(source_counts)

    # --- corpus ---
    corpus = read_ndjson(DATA_DIR / "corpus.ndjson")
    s["corpus_count"] = len(corpus)
    s["lang"] = dict(Counter(r.get("lang", "?") for r in corpus))
    s["domain"] = dict(Counter(r.get("domain", "?") for r in corpus))
    s["models"] = dict(Counter(m for r in corpus for m in r.get("target_models", ["?"])))

    tokens = [r.get("body_tokens", 0) for r in corpus]
    if tokens:
        s["tok_min"] = min(tokens)
        s["tok_max"] = max(tokens)
        s["tok_avg"] = sum(tokens) // len(tokens)
    else:
        s["tok_min"] = s["tok_max"] = s["tok_avg"] = 0

    # --- tagged ---
    tagged = read_ndjson(DATA_DIR / "corpus_tagged.ndjson")
    s["tagged_count"] = len(tagged)
    s["tiller_null"] = sum(1 for r in tagged if r.get("tiller") is None)
    s["tiller_done"] = s["tagged_count"] - s["tiller_null"]

    heatmap: dict[str, int] = {}
    helm_axes: dict[str, Counter] = {
        "heading": Counter(), "berth": Counter(),
        "bearing": Counter(), "slack": Counter(),
    }
    for r in tagged:
        t = r.get("tiller")
        if not t:
            continue
        c = t.get("channel", "?")
        so = t.get("sounding", "?")
        heatmap[f"{c},{so}"] = heatmap.get(f"{c},{so}", 0) + 1
        for ax in helm_axes:
            helm_axes[ax][str(t.get(ax) or "null")] += 1
    s["heatmap"] = heatmap
    s["helm"] = {k: dict(v) for k, v in helm_axes.items()}

    # --- progress ---
    progress = read_ndjson(DATA_DIR / "progress.ndjson")
    s["progress"] = dict(Counter(r.get("layer", "?") for r in progress))
    s["progress_total"] = len(progress)

    # --- errors ---
    errors = read_ndjson(DATA_DIR / "errors.ndjson")
    s["errors"] = errors[-30:]
    s["err_by_layer"] = dict(Counter(r.get("layer", "?") for r in errors))
    s["err_total"] = len(errors)

    # --- file sizes ---
    files = {}
    for name, path in [
        ("raw/", RAW_DIR),
        ("corpus.ndjson", DATA_DIR / "corpus.ndjson"),
        ("corpus_tagged.ndjson", DATA_DIR / "corpus_tagged.ndjson"),
        ("progress.ndjson", DATA_DIR / "progress.ndjson"),
        ("errors.ndjson", DATA_DIR / "errors.ndjson"),
    ]:
        if path.exists():
            if path.is_dir():
                files[name] = sum(f.stat().st_size for f in path.glob("*") if f.is_file())
            else:
                files[name] = path.stat().st_size
        else:
            files[name] = 0
    s["files"] = files
    return s


def bars_html(items: dict, color: str) -> str:
    if not items:
        return '<div class="empty-msg">no data</div>'
    total = sum(items.values())
    if total == 0:
        return '<div class="empty-msg">no data</div>'
    mx = max(items.values())
    rows = []
    for label, cnt in sorted(items.items(), key=lambda x: -x[1]):
        w = cnt / mx * 100 if mx else 0
        p = cnt / total * 100
        rows.append(
            f'<div class="br"><span class="bl">{label}</span>'
            f'<div class="bt"><div class="bf" style="width:{w:.0f}%;background:{color}"></div></div>'
            f'<span class="bv">{fmt_num(cnt)} <small>({p:.0f}%)</small></span></div>'
        )
    return "\n".join(rows)


def heatmap_html(data: dict, tiller_done: int) -> str:
    if tiller_done == 0:
        return '<div class="empty-msg">TILLER 태깅 데이터 없음</div>'
    mx = max(data.values()) if data else 1
    cells = []
    for c in range(1, 5):
        row = []
        for so in range(1, 5):
            v = data.get(f"{c},{so}", 0)
            opacity = v / mx * 0.9 + 0.1 if v > 0 else 0
            row.append(
                f'<td class="hc" style="background:rgba(0,180,216,{opacity:.2f})">'
                f'{v if v else ""}</td>'
            )
        cells.append(f'<tr><th class="hl">C{c}</th>{"".join(row)}</tr>')
    return (
        '<table class="hm"><tr><th></th>'
        '<th class="hs">S1</th><th class="hs">S2</th><th class="hs">S3</th><th class="hs">S4</th>'
        f'</tr>{"".join(cells)}</table>'
    )


def errors_html(errors: list[dict]) -> str:
    if not errors:
        return '<div class="empty-msg">no errors</div>'
    rows = []
    for e in reversed(errors):
        layer = e.get("layer", "?")
        src = e.get("source_id", "")
        err = e.get("error", "?")
        at = e.get("at", "")[:19]
        cid = e.get("content_id", "")
        detail = e.get("detail", "")[:80]
        ident = cid or src
        rows.append(
            f'<tr><td class="el">{layer}</td><td>{ident}</td>'
            f'<td class="ee">{err}</td><td class="ed">{detail}</td>'
            f'<td class="et">{at}</td></tr>'
        )
    return (
        '<table class="errtbl"><tr><th>Layer</th><th>ID</th>'
        '<th>Error</th><th>Detail</th><th>Time</th></tr>'
        + "\n".join(rows)
        + "</table>"
    )


def files_html(files: dict) -> str:
    parts = []
    for name, size in files.items():
        cls = "factive" if size > 0 else "fempty"
        parts.append(f'<span class="fi {cls}">{name} <b>{fmt_size(size)}</b></span>')
    return " ".join(parts)


def layer_card(tag: str, title: str, count: int, errs: int, cost: str, model: str, tag_class: str) -> str:
    err_badge = f'<span class="layer-err">{errs} err</span>' if errs else ""
    status = "active" if count > 0 else "idle"
    return (
        f'<div class="lcard">'
        f'<div class="lc-tag {tag_class}">{tag}</div>'
        f'<div class="lc-title">{title}</div>'
        f'<div class="lc-count">{fmt_num(count)}</div>'
        f'<div class="lc-meta"><span class="lc-model">{model}</span>'
        f'<span class="lc-cost">{cost}</span>{err_badge}</div>'
        f'<div class="lc-dot {status}"></div>'
        f'</div>'
    )


def generate_html(s: dict) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    p1 = "done" if s["raw_total"] > 0 else "idle"
    p2 = "current"
    p3 = "idle" if s["tiller_done"] == 0 else ("done" if s["tiller_null"] == 0 else "current")
    p4 = "idle"

    l0_count = s["progress"].get("L0", 0)
    l1_count = s["progress"].get("L1", 0)
    l3_count = s["progress"].get("L3", 0)
    l0_err = s["err_by_layer"].get("L0", 0)
    l1_err = s["err_by_layer"].get("L1", 0)
    l3_err = s["err_by_layer"].get("L3", 0)

    tiller_pct = (
        f'{s["tiller_done"] / s["tagged_count"] * 100:.0f}%'
        if s["tagged_count"] > 0 else "—"
    )

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Prompt Corpus Pipeline Dashboard</title>
<style>
:root {{
  --bg:#1a1a2e; --sf:#16213e; --sf2:#0f3460;
  --ac:#e94560; --ac2:#00b4d8; --gn:#06d6a0; --yl:#ffd166;
  --tx:#edf2f4; --txd:#8d99ae; --bd:#2b2d42;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'SF Mono','Cascadia Code','Fira Code',monospace;
  background:var(--bg); color:var(--tx); padding:20px; line-height:1.5; }}
.wrap {{ max-width:960px; margin:0 auto; }}

/* header */
.hdr {{ display:flex; justify-content:space-between; align-items:center;
  padding:14px 20px; background:var(--sf); border:1px solid var(--bd);
  border-radius:10px; margin-bottom:14px; flex-wrap:wrap; gap:8px; }}
.hdr h1 {{ font-size:16px; font-weight:700; }}
.hdr h1 span {{ color:var(--ac2); }}
.hdr-meta {{ font-size:11px; color:var(--txd); }}

/* phases */
.phases {{ display:flex; gap:8px; margin-bottom:16px; flex-wrap:wrap; }}
.ph {{ font-size:12px; padding:5px 14px; border-radius:6px; }}
.ph.done {{ background:rgba(6,214,160,.12); color:var(--gn); border:1px solid rgba(6,214,160,.25); }}
.ph.current {{ background:rgba(0,180,216,.12); color:var(--ac2); border:1px solid rgba(0,180,216,.25); }}
.ph.idle {{ background:rgba(255,255,255,.03); color:var(--txd); border:1px solid var(--bd); }}

/* layer cards */
.lcards {{ display:grid; grid-template-columns:repeat(5,1fr); gap:10px; margin-bottom:16px; }}
@media(max-width:700px) {{ .lcards {{ grid-template-columns:repeat(2,1fr); }} }}
.lcard {{ background:var(--sf); border:1px solid var(--bd); border-radius:8px;
  padding:14px; position:relative; overflow:hidden; }}
.lc-tag {{ font-size:10px; font-weight:700; padding:2px 7px; border-radius:4px;
  display:inline-block; margin-bottom:6px; }}
.t-l0 {{ background:#264653; color:#a8dadc; }}
.t-l05 {{ background:#2a3d45; color:#e9c46a; }}
.t-l1 {{ background:#3d2645; color:#d4a5ff; }}
.t-l2 {{ background:#1b4332; color:#95d5b2; }}
.t-l3 {{ background:#462620; color:#ffb4a2; }}
.lc-title {{ font-size:12px; color:var(--txd); margin-bottom:4px; }}
.lc-count {{ font-size:22px; font-weight:700; color:var(--tx); }}
.lc-meta {{ display:flex; gap:6px; margin-top:6px; flex-wrap:wrap; align-items:center; }}
.lc-model {{ font-size:10px; background:rgba(255,255,255,.05); padding:1px 6px; border-radius:3px; color:var(--txd); }}
.lc-cost {{ font-size:10px; color:var(--gn); font-weight:600; }}
.layer-err {{ font-size:10px; color:var(--ac); }}
.lc-dot {{ width:6px; height:6px; border-radius:50%; position:absolute; top:12px; right:12px; }}
.lc-dot.active {{ background:var(--gn); box-shadow:0 0 6px var(--gn); }}
.lc-dot.idle {{ background:var(--bd); }}

/* summary strip */
.sumstrip {{ display:flex; gap:16px; padding:12px 18px; background:var(--sf);
  border:1px solid var(--bd); border-radius:8px; margin-bottom:16px;
  justify-content:space-around; flex-wrap:wrap; }}
.ss {{ text-align:center; }}
.ss-val {{ font-size:20px; font-weight:700; }}
.ss-lbl {{ font-size:10px; color:var(--txd); }}
.c-gn {{ color:var(--gn); }}
.c-ac2 {{ color:var(--ac2); }}
.c-yl {{ color:var(--yl); }}
.c-ac {{ color:var(--ac); }}

/* panels */
.panels {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-bottom:16px; }}
@media(max-width:700px) {{ .panels {{ grid-template-columns:1fr; }} }}
.panel {{ background:var(--sf); border:1px solid var(--bd); border-radius:8px; padding:14px 16px; }}
.panel h3 {{ font-size:12px; color:var(--txd); margin-bottom:10px; text-transform:uppercase; letter-spacing:1px; }}
.full {{ grid-column:1/-1; }}

/* bars */
.br {{ display:flex; align-items:center; gap:8px; margin-bottom:4px; }}
.bl {{ font-size:11px; width:70px; text-align:right; color:var(--txd); flex-shrink:0; }}
.bt {{ flex:1; height:14px; background:rgba(255,255,255,.04); border-radius:3px; overflow:hidden; }}
.bf {{ height:100%; border-radius:3px; transition:width .3s; }}
.bv {{ font-size:10px; color:var(--txd); width:90px; flex-shrink:0; }}
.bv small {{ opacity:.6; }}

/* heatmap */
.hm {{ border-collapse:collapse; margin:0 auto; }}
.hm th {{ font-size:10px; color:var(--txd); padding:4px 8px; }}
.hs {{ text-align:center; }}
.hl {{ text-align:right; }}
.hc {{ width:48px; height:36px; text-align:center; font-size:12px; font-weight:600;
  border:1px solid var(--bd); color:var(--tx); }}

/* errors table */
.errtbl {{ width:100%; border-collapse:collapse; font-size:11px; }}
.errtbl th {{ text-align:left; color:var(--txd); padding:4px 6px; border-bottom:1px solid var(--bd); font-weight:600; }}
.errtbl td {{ padding:4px 6px; border-bottom:1px solid rgba(43,45,66,.4); }}
.el {{ color:var(--yl); font-weight:600; }}
.ee {{ color:var(--ac); }}
.ed {{ color:var(--txd); font-size:10px; max-width:200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
.et {{ color:var(--txd); font-size:10px; }}

/* files */
.fbar {{ display:flex; gap:12px; flex-wrap:wrap; }}
.fi {{ font-size:11px; color:var(--txd); }}
.fi b {{ font-weight:600; }}
.fi.factive b {{ color:var(--ac2); }}
.fi.fempty b {{ color:var(--bd); }}

.empty-msg {{ font-size:12px; color:var(--txd); font-style:italic; padding:8px 0; }}

/* helm mini */
.helm-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }}
.helm-ax h4 {{ font-size:10px; color:var(--txd); margin-bottom:4px; text-transform:uppercase; }}
</style>
</head>
<body>
<div class="wrap">

<div class="hdr">
  <h1>Prompt Corpus Pipeline <span>Dashboard</span></h1>
  <div class="hdr-meta">v1.4 &middot; {now}</div>
</div>

<div class="phases">
  <span class="ph {p1}">Phase 1 — GitHub {"&#10003;" if p1 == "done" else ""}</span>
  <span class="ph {p2}">Phase 2 — Web/KR</span>
  <span class="ph {p3}">Phase 3 — Validation</span>
  <span class="ph {p4}">Phase 4 — Analysis</span>
</div>

<div class="lcards">
  {layer_card("L0", "Seed Collection", l0_count, l0_err, "$0", "no LLM", "t-l0")}
  {layer_card("L0.5", "Pre-filter", s["progress"].get("L0.5", 0),
              s["err_by_layer"].get("L0.5", 0), "$0.72", "Nano", "t-l05")}
  {layer_card("L1", "Extract", l1_count, l1_err, "$1.36", "Nano", "t-l1")}
  {layer_card("L2", "Normalize", s["corpus_count"], 0, "$0", "local", "t-l2")}
  {layer_card("L3", "TILLER Tag", l3_count, l3_err, "$2.10", "Nano", "t-l3")}
</div>

<div class="sumstrip">
  <div class="ss"><div class="ss-val c-ac2">{fmt_num(s["raw_total"])}</div><div class="ss-lbl">Raw Records</div></div>
  <div class="ss"><div class="ss-val c-gn">{fmt_num(s["corpus_count"])}</div><div class="ss-lbl">Normalized</div></div>
  <div class="ss"><div class="ss-val c-yl">{fmt_num(s["tagged_count"])}</div><div class="ss-lbl">Tagged</div></div>
  <div class="ss"><div class="ss-val c-ac2">{tiller_pct}</div><div class="ss-lbl">TILLER Coverage</div></div>
  <div class="ss"><div class="ss-val {"c-ac" if s["err_total"] > 0 else "c-gn"}">{s["err_total"]}</div><div class="ss-lbl">Errors</div></div>
</div>

<div class="panels">

  <div class="panel">
    <h3>Sources</h3>
    {bars_html(s["source_counts"], "#00b4d8")}
  </div>

  <div class="panel">
    <h3>Language</h3>
    {bars_html(s["lang"], "#06d6a0")}
  </div>

  <div class="panel">
    <h3>Domain</h3>
    {bars_html(s["domain"], "#e9c46a")}
  </div>

  <div class="panel">
    <h3>Target Models</h3>
    {bars_html(s["models"], "#e94560")}
  </div>

  <div class="panel">
    <h3>TRIM Heatmap (Channel &times; Sounding)</h3>
    {heatmap_html(s["heatmap"], s["tiller_done"])}
  </div>

  <div class="panel">
    <h3>HELM Axes</h3>
    <div class="helm-grid">
      <div class="helm-ax"><h4>Heading</h4>{bars_html(s["helm"].get("heading", {}), "#a8dadc")}</div>
      <div class="helm-ax"><h4>Berth</h4>{bars_html(s["helm"].get("berth", {}), "#e9c46a")}</div>
      <div class="helm-ax"><h4>Bearing</h4>{bars_html(s["helm"].get("bearing", {}), "#d4a5ff")}</div>
      <div class="helm-ax"><h4>Slack</h4>{bars_html(s["helm"].get("slack", {}), "#ffb4a2")}</div>
    </div>
  </div>

  <div class="panel full">
    <h3>Token Stats</h3>
    <div style="font-size:12px;color:var(--txd)">
      min <b style="color:var(--tx)">{s["tok_min"]}</b> &middot;
      avg <b style="color:var(--tx)">{s["tok_avg"]}</b> &middot;
      max <b style="color:var(--tx)">{s["tok_max"]}</b> &middot;
      records <b style="color:var(--tx)">{fmt_num(s["corpus_count"])}</b>
    </div>
  </div>

  <div class="panel full">
    <h3>Recent Errors ({s["err_total"]} total)</h3>
    {errors_html(s["errors"])}
  </div>

  <div class="panel full">
    <h3>Data Files</h3>
    <div class="fbar">{files_html(s["files"])}</div>
  </div>

</div>
</div>
</body>
</html>"""


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    stats = collect_stats()
    html = generate_html(stats)
    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"Dashboard -> {OUT_PATH}")
    if "--no-open" not in sys.argv:
        webbrowser.open(OUT_PATH.as_uri())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
