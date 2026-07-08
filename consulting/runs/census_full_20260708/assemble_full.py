"""전수 시계열 조립: parts/*.ndjson + 기존 수집분 → census_full_weekly.ndjson.

- 입력 라인: {"channel_id": str, "weeks": [[date,avg,max,air,fol,cnt,chat,view], ...]}
  또는 기존 조립본 {"channel_id","channel_name","segment","follower_count","weeks":[dict...]}
- 주간 리샘플(assemble.resample_weekly) 적용 (소형 채널 일간 rows 대비)
- 세그먼트는 시계열 마지막 관측 maxFollowerCount로 산출 (rookie<150 / growth<10000 / large)
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
CONS = HERE.parent.parent  # consulting/
sys.path.insert(0, str(CONS / "runs" / "backtest_20260708"))
from assemble import resample_weekly, WEEK_KEYS  # noqa: E402

WEEKLY_EXISTING = CONS / "runs" / "backtest_20260708" / "weekly_series.ndjson"
CARDS = CONS / "runs" / "vtuber_outreach_pilot_20260704" / "cards_series_20260708.ndjson"
GUBIVA = CONS / "구비바_케이스" / "gubiba_series_20260708.ndjson"
OUT = HERE / "census_full_weekly.ndjson"


def seg_of(follower):
    if follower is None:
        return "unknown"
    if follower < 150:
        return "rookie"
    if follower < 10000:
        return "growth"
    return "large"


def norm_weeks(row):
    """compact list weeks 또는 dict weeks → resampled dict weeks."""
    w = row["weeks"]
    if w and isinstance(w[0], list):
        w = [dict(zip(WEEK_KEYS, x)) for x in w]
    return resample_weekly(w)


def last_follower(weeks):
    fols = [x["maxFollowerCount"] for x in weeks if x.get("maxFollowerCount")]
    return fols[-1] if fols else None


def main():
    seen = {}
    def ingest(path, is_compact):
        n = 0
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            cid = row["channel_id"]
            if cid in seen:
                continue
            weeks = norm_weeks(row)
            if not weeks:
                continue
            fol = last_follower(weeks)
            seen[cid] = {
                "channel_id": cid,
                "channel_name": row.get("channel_name", ""),
                "segment": seg_of(fol),
                "follower_count": fol,
                "weeks": weeks,
            }
            n += 1
        return n

    # 우선순위: 기존 조립본(이름 보유) 먼저, 그다음 parts
    print("existing weekly:", ingest(WEEKLY_EXISTING, False))
    if CARDS.exists():
        print("cards:", ingest(CARDS, True))
    if GUBIVA.exists():
        print("gubiva:", ingest(GUBIVA, True))
    for p in sorted((HERE / "parts").glob("*.ndjson")):
        print(p.name, ":", ingest(p, True))

    with OUT.open("w", encoding="utf-8") as f:
        for rec in seen.values():
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    from collections import Counter
    segs = Counter(r["segment"] for r in seen.values())
    wk = [len(r["weeks"]) for r in seen.values()]
    print(f"\n총 {len(seen)}채널 -> {OUT.name}")
    print("세그먼트:", dict(segs))
    print(f"주 범위: {min(wk)}~{max(wk)}, 평균 {sum(wk)/len(wk):.1f}")


if __name__ == "__main__":
    main()
