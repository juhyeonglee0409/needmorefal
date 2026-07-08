"""주간 시계열에서 진단 규칙 후보를 역추출한다 (탐색적 패턴 마이닝).

설계 원칙 (다중비교·과적합 방지):
- 시간 분할: 발굴 창(전반부 주)에서 패턴 후보를 찾고, 검증 창(후반부, 채널당
  단일 스냅샷 = 독립 표본)에서 같은 방향·강도가 재현되는지 확인한다.
- 성과 정의는 백테스트와 동일: 전방 12주 상대 성장(주당 %)의 세그먼트 중앙값
  대비 초과(α). 팔로워 기준.
- 지표는 채널-주 시점 t까지의 정보만 사용 (lookahead 금지).
- 검증 p-value는 permutation (seed 고정).

사용: consulting/에서 python runs/pattern_mining_20260708/mine.py
"""
import json
import math
import random
import statistics
from bisect import bisect_left, bisect_right
from pathlib import Path

HERE = Path(__file__).parent
INPUT = HERE.parent / "backtest_20260708" / "weekly_series.ndjson"
FORWARD = 12          # 전방 창 (주)
MOMENTUM = 4          # 과거 모멘텀 창 (주)
DISCOVERY_WEEKS = range(MOMENTUM, 21)   # 발굴: t=4..20
VALIDATION_WEEK = 30                     # 검증: 채널당 단일 스냅샷 (독립 표본)
SEED = 20260708
PERM_ROUNDS = 2000


def load():
    channels = []
    all_dates = set()
    for line in INPUT.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        all_dates.update(w["date"] for w in row["weeks"])
        channels.append(row)
    grid = {d: i for i, d in enumerate(sorted(all_dates))}
    for ch in channels:
        ch["by_week"] = {grid[w["date"]]: w for w in ch["weeks"]}
    return channels, len(grid)


def metric(ch, t, key):
    row = ch["by_week"].get(t)
    if row is None:
        return None
    return row.get(key)


def rel_slope(ch, t0, t1, key):
    a, b = metric(ch, t0, key), metric(ch, t1, key)
    if a is None or b is None or a <= 0:
        return None
    return ((b / a) - 1.0) / (t1 - t0)


def features_at(ch, t):
    """t 시점까지의 정보만 사용하는 지표들."""
    avg = metric(ch, t, "avgLiveViews")
    mx = metric(ch, t, "maxLiveViews")
    air = metric(ch, t, "airTime")
    fol = metric(ch, t, "maxFollowerCount")
    chat = metric(ch, t, "avgChatCount")
    feats = {}
    feats["retention"] = (avg / mx) if avg and mx and mx > 0 else None
    feats["airtime"] = air
    feats["efficiency"] = (avg / fol) if avg and fol and fol > 0 else None
    feats["chat_rate"] = (chat / avg) if chat is not None and avg and avg > 0 else None
    feats["follower_log"] = math.log10(fol) if fol and fol > 0 else None
    feats["momentum_avg"] = rel_slope(ch, t - MOMENTUM, t, "avgLiveViews")
    feats["momentum_fol"] = rel_slope(ch, t - MOMENTUM, t, "maxFollowerCount")
    weeks_on = sum(
        1 for k in range(t - MOMENTUM + 1, t + 1)
        if (metric(ch, k, "airTime") or 0) > 0
    )
    feats["consistency"] = weeks_on / MOMENTUM
    # 방송 규칙성: 최근 4주 방송시간의 변동계수 (일정할수록 낮음)
    airs = [metric(ch, k, "airTime") for k in range(t - MOMENTUM + 1, t + 1)]
    airs = [a for a in airs if a is not None and a > 0]
    if len(airs) >= 3 and statistics.mean(airs) > 0:
        feats["air_cv"] = statistics.pstdev(airs) / statistics.mean(airs)
    else:
        feats["air_cv"] = None
    return feats


def outcome_alpha(channels, t):
    """t→t+12 팔로워 상대 성장의 세그먼트 중앙값 대비 초과. 이탈(관측 소멸)=None 별도 반환."""
    slopes = {}
    by_seg = {}
    for ch in channels:
        s = rel_slope(ch, t, t + FORWARD, "maxFollowerCount")
        slopes[ch["channel_id"]] = s
        if s is not None:
            by_seg.setdefault(ch["segment"], []).append(s)
    med = {seg: statistics.median(v) for seg, v in by_seg.items()}
    out = {}
    for ch in channels:
        s = slopes[ch["channel_id"]]
        out[ch["channel_id"]] = None if s is None else s - med[ch["segment"]]
    return out


def pct_rank(value, population):
    ordered = sorted(population)
    if len(ordered) <= 1:
        return 0.5
    lo = bisect_left(ordered, value)
    hi = bisect_right(ordered, value)
    return (lo + hi - 1) / (2.0 * (len(ordered) - 1))


def collect(channels, weeks):
    """(feature명 -> [(feature pct, alpha)]) — 세그먼트-주 내 percentile로 정규화."""
    data = {}
    for t in weeks:
        alpha = outcome_alpha(channels, t)
        # 세그먼트별 feature 모집단
        seg_pop = {}
        feat_cache = {}
        for ch in channels:
            f = features_at(ch, t)
            feat_cache[ch["channel_id"]] = (ch["segment"], f)
            for name, v in f.items():
                if v is not None:
                    seg_pop.setdefault((ch["segment"], name), []).append(v)
        for ch in channels:
            seg, f = feat_cache[ch["channel_id"]]
            a = alpha[ch["channel_id"]]
            if a is None:
                continue
            for name, v in f.items():
                if v is None:
                    continue
                pop = seg_pop.get((seg, name), [])
                if len(pop) < 10:
                    continue
                data.setdefault(name, []).append((pct_rank(v, pop), a))
    return data


def spearman(pairs):
    if len(pairs) < 10:
        return None
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    rx = _ranks(xs)
    ry = _ranks(ys)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    dy = math.sqrt(sum((b - my) ** 2 for b in ry))
    return num / (dx * dy) if dx and dy else 0.0


def _ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def quintile_spread(pairs):
    """상위 20% 평균 α − 하위 20% 평균 α (주당 %p), + 각 quintile 평균."""
    ordered = sorted(pairs, key=lambda p: p[0])
    n = len(ordered)
    if n < 25:
        return None, []
    q = n // 5
    means = []
    for i in range(5):
        chunk = ordered[i * q: (i + 1) * q if i < 4 else n]
        means.append(statistics.mean(p[1] for p in chunk))
    return means[4] - means[0], means


def perm_pvalue(pairs, observed_rho, seed=SEED):
    rng = random.Random(seed)
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    exceed = 1
    for _ in range(PERM_ROUNDS):
        perm = ys.copy()
        rng.shuffle(perm)
        r = spearman(list(zip(xs, perm)))
        if r is not None and abs(r) >= abs(observed_rho):
            exceed += 1
    return exceed / (PERM_ROUNDS + 1)


def main():
    channels, week_count = load()
    print(f"channels={len(channels)} weeks={week_count}")
    print(f"발굴 창: t={DISCOVERY_WEEKS.start}..{DISCOVERY_WEEKS.stop - 1} (채널-주 풀링)")
    print(f"검증 창: t={VALIDATION_WEEK} (채널당 단일 스냅샷, 독립 표본)\n")

    disc = collect(channels, DISCOVERY_WEEKS)
    val = collect(channels, [VALIDATION_WEEK])

    print(f"{'지표':<14}{'발굴ρ':>8}{'발굴spread':>12}{'검증ρ':>8}{'검증p':>8}{'검증spread':>12}{'검증n':>7}  판정")
    results = []
    for name in sorted(disc):
        d_pairs = disc[name]
        d_rho = spearman(d_pairs)
        d_spread, d_means = quintile_spread(d_pairs)
        v_pairs = val.get(name, [])
        v_rho = spearman(v_pairs)
        v_spread, v_means = quintile_spread(v_pairs)
        if d_rho is None or v_rho is None:
            continue
        v_p = perm_pvalue(v_pairs, v_rho)
        # 재현 판정: 발굴에서 |ρ|>=0.05, 검증에서 같은 부호 + p<=0.05
        replicated = abs(d_rho) >= 0.05 and (d_rho * v_rho > 0) and v_p <= 0.05
        results.append({
            "feature": name,
            "discovery": {"rho": d_rho, "spread_ppw": d_spread, "n": len(d_pairs), "quintile_means": d_means},
            "validation": {"rho": v_rho, "pvalue": v_p, "spread_ppw": v_spread, "n": len(v_pairs), "quintile_means": v_means},
            "replicated": replicated,
        })
        print(f"{name:<14}{d_rho:>8.3f}{(d_spread or 0)*100:>11.3f}%{v_rho:>8.3f}{v_p:>8.3f}{(v_spread or 0)*100:>11.3f}%{len(v_pairs):>7}  {'재현' if replicated else '-'}")

    out = HERE / "mining_results.json"
    out.write_text(json.dumps({
        "input": str(INPUT), "forward_weeks": FORWARD, "momentum_weeks": MOMENTUM,
        "discovery_weeks": [DISCOVERY_WEEKS.start, DISCOVERY_WEEKS.stop - 1],
        "validation_week": VALIDATION_WEEK, "seed": SEED,
        "outcome": "alpha_follower (전방 12주 상대 성장, 세그먼트 중앙값 대비)",
        "results": results,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()
