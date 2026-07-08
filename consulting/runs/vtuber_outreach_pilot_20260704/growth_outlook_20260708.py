# -*- coding: utf-8 -*-
"""발송 카드 86채널의 성장 전망 신호(§6.3.2) 산출.

기준: 방법론 §6.3.2 — 효율(평시청/팔로워)·관성(직전 4주 팔로워 상대성장)의
세그먼트 코호트 내 percentile 조합. 참조 모집단 = 백테스트 층화 표본 999 중
growth 세그먼트(550), 기준 주 = 마지막 완결 주.

출력: growth_outlook_20260708.json {channel_id: {signal, eff_pct, mom_pct, week}}
signal: green | near | neutral | red | None(데이터 부족)
"""
import json
from bisect import bisect_left, bisect_right
from pathlib import Path

BASE = Path(__file__).parent
BT = BASE.parent / "backtest_20260708"
MOMENTUM = 4
Q_HIGH, Q_LOW = 0.75, 0.25


def load_series(path):
    out = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        out[r["channel_id"]] = {w["date"]: w for w in r["weeks"]}
    return out


def pct_rank(value, population):
    ordered = sorted(population)
    if len(ordered) <= 1:
        return 0.5
    lo, hi = bisect_left(ordered, value), bisect_right(ordered, value)
    return (lo + hi - 1) / (2.0 * (len(ordered) - 1))


def eff_mom(weeks_by_date, dates, t_idx):
    """t_idx 주의 효율·관성 (데이터 없으면 None)."""
    t = dates[t_idx]
    t0 = dates[t_idx - MOMENTUM]
    row = weeks_by_date.get(t)
    row0 = weeks_by_date.get(t0)
    if not row or not row0:
        return None, None
    avg, fol, fol0 = row.get("avgLiveViews"), row.get("maxFollowerCount"), row0.get("maxFollowerCount")
    eff = (avg / fol) if avg and fol and fol > 0 else None
    mom = (((fol / fol0) - 1.0) / MOMENTUM) if fol and fol0 and fol0 > 0 else None
    return eff, mom


def main():
    ref_rows = [json.loads(l) for l in (BT / "weekly_series.ndjson").read_text(encoding="utf-8").splitlines() if l.strip()]
    ref = {r["channel_id"]: ({w["date"]: w for w in r["weeks"]}, r["segment"]) for r in ref_rows}
    all_dates = sorted({w["date"] for r in ref_rows for w in r["weeks"]})
    # 마지막 주는 수집 시점상 부분 주일 수 있어 직전 완결 주를 기준으로 쓴다
    t_idx = len(all_dates) - 2
    print("기준 주:", all_dates[t_idx])

    pop_eff, pop_mom = [], []
    for wbd, seg in ref.values():
        if seg != "growth":
            continue
        eff, mom = eff_mom(wbd, all_dates, t_idx)
        if eff is not None:
            pop_eff.append(eff)
        if mom is not None:
            pop_mom.append(mom)
    print(f"참조 모집단(growth): eff n={len(pop_eff)}, mom n={len(pop_mom)}")

    cards = load_series(BASE / "cards_series_20260708.ndjson")
    send = [json.loads(l) for l in (BASE / "send_list_20260704.ndjson").read_text(encoding="utf-8").splitlines() if l.strip()]

    out = {}
    counts = {"green": 0, "near": 0, "neutral": 0, "red": 0, "none": 0}
    for r in send:
        cid = r["channel_id"]
        wbd = cards.get(cid) or (ref.get(cid) or (None,))[0]
        signal = None
        eff_pct = mom_pct = None
        if wbd:
            eff, mom = eff_mom(wbd, all_dates, t_idx)
            # 기준 주에 방송이 없으면 최대 4주 전까지 소급
            back = t_idx
            while (eff is None or mom is None) and back > t_idx - 4:
                back -= 1
                eff, mom = eff_mom(wbd, all_dates, back)
            if eff is not None and mom is not None:
                eff_pct = pct_rank(eff, pop_eff)
                mom_pct = pct_rank(mom, pop_mom)
                if eff_pct >= Q_HIGH and mom_pct >= Q_HIGH:
                    signal = "green"
                elif mom_pct >= Q_HIGH:
                    signal = "near"
                elif eff_pct <= Q_LOW and mom_pct <= Q_LOW:
                    signal = "red"
                else:
                    signal = "neutral"
        counts[signal or "none"] += 1
        out[cid] = {
            "signal": signal,
            "eff_pct": round(eff_pct, 3) if eff_pct is not None else None,
            "mom_pct": round(mom_pct, 3) if mom_pct is not None else None,
            "week": all_dates[t_idx],
        }
    (BASE / "growth_outlook_20260708.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("분포:", counts)


if __name__ == "__main__":
    main()
