"""weekly_series_part*.ndjson (브라우저 수확분) + sample_channels.json -> weekly_series.ndjson.

파트 라인 포맷: {"channel_id": str, "weeks": [[date, avgLiveViews, maxLiveViews, airTime,
maxFollowerCount, sumCount, avgChatCount, viewership], ...]}
출력 라인 포맷: 백테스트 엔진 입력 스키마 (부록 I/M 계열).

소프트콘은 채널 규모에 따라 rows를 일간 또는 주간 집계로 내려주므로,
전 rows를 ISO 주(월요일 앵커)로 그룹핑해 주간으로 재집계한다.
(주간 단일 row에는 재집계가 항등이므로 일괄 적용해도 안전)

사용: python assemble.py <part1.ndjson> [part2.ndjson ...]
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).parent
WEEK_KEYS = ["date", "avgLiveViews", "maxLiveViews", "airTime",
             "maxFollowerCount", "sumCount", "avgChatCount", "viewership"]


def resample_weekly(rows):
    """rows(dict 리스트, 일간/주간 혼합) -> ISO 주 재집계 rows."""
    buckets = {}
    for r in rows:
        d = date.fromisoformat(r["date"])
        monday = d - timedelta(days=d.weekday())
        buckets.setdefault(monday, []).append(r)
    out = []
    for monday in sorted(buckets):
        grp = buckets[monday]
        sum_count = sum(r["sumCount"] or 0 for r in grp)
        weighted_avg = None
        if sum_count:
            num = sum((r["avgLiveViews"] or 0) * (r["sumCount"] or 0) for r in grp)
            weighted_avg = round(num / sum_count)
        chat_num = sum((r["avgChatCount"] or 0) * (r["sumCount"] or 0) for r in grp)
        max_of = lambda k: max((r[k] for r in grp if r[k] is not None), default=None)
        out.append({
            "date": monday.isoformat(),
            "avgLiveViews": weighted_avg,
            "maxLiveViews": max_of("maxLiveViews"),
            "airTime": round(sum(r["airTime"] or 0 for r in grp), 1),
            "maxFollowerCount": max_of("maxFollowerCount"),
            "sumCount": sum_count,
            "avgChatCount": round(chat_num / sum_count) if sum_count else None,
            "viewership": sum(r["viewership"] or 0 for r in grp),
        })
    return out


def main(part_paths):
    meta = {c["channel_id"]: c for c in json.loads(
        (HERE / "sample_channels.json").read_text(encoding="utf-8"))}
    out_path = HERE / "weekly_series.ndjson"
    seen = set()
    n = 0
    with out_path.open("w", encoding="utf-8") as out:
        for part in part_paths:
            for line in Path(part).read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                cid = row["channel_id"]
                if cid in seen:
                    continue
                seen.add(cid)
                m = meta.get(cid)
                if m is None:
                    print(f"[warn] {cid}: sample_channels에 없음, 건너뜀")
                    continue
                rec = {
                    "channel_id": cid,
                    "channel_name": m["channel_name"],
                    "segment": m["segment"],
                    "follower_count": m["follower_count"],
                    "weeks": resample_weekly(
                        [dict(zip(WEEK_KEYS, w)) for w in row["weeks"]]),
                }
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
    print(f"{n} channels -> {out_path}")


if __name__ == "__main__":
    main(sys.argv[1:])
