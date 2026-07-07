"""weekly_series_part*.ndjson (브라우저 수확분) + sample_channels.json -> weekly_series.ndjson.

파트 라인 포맷: {"channel_id": str, "weeks": [[date, avgLiveViews, maxLiveViews, airTime,
maxFollowerCount, sumCount, avgChatCount, viewership], ...]}
출력 라인 포맷: 백테스트 엔진 입력 스키마 (부록 I/M 계열).

사용: python assemble.py <part1.ndjson> [part2.ndjson ...]
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
WEEK_KEYS = ["date", "avgLiveViews", "maxLiveViews", "airTime",
             "maxFollowerCount", "sumCount", "avgChatCount", "viewership"]


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
                    "weeks": [dict(zip(WEEK_KEYS, w)) for w in row["weeks"]],
                }
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
    print(f"{n} channels -> {out_path}")


if __name__ == "__main__":
    main(sys.argv[1:])
