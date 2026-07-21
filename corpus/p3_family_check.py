"""Gemini 가족 편향 점검 — 제3 가문(Anthropic Claude) rater 추가, 전원 현행 프롬프트.

배경: 5-rater 매트릭스(p3_model_matrix)에서 Gemini 3형제의 상호 κ가 이종 rater 대비
높았음 — 패널 다수결이 Gemini 다수 구성이라 순위가 가족 상관으로 부풀었을 가능성.

Rater (전원 v0.7.1 코드북 프롬프트):
  H    = 휴리스틱
  O2   = gpt-4.1-mini (신규 — 구 캐시는 구 프롬프트라 재태깅)
  C    = claude-sonnet-5 (신규)
  G35n = gemini-3.5-flash  (p3_berth_check_tags 캐시)
  G31n = gemini-3.1-pro-preview (동일 캐시)

판정 지표:
  (a) 가족 내 κ(G35n,G31n) vs 이종 LLM 쌍 평균 κ — 축별
  (b) 균형 패널(4 LLM + H) leave-one-out 다수결 일치율 순위

사용법: cd corpus && python p3_family_check.py
산출: data/analysis/p3_family_check.txt
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import combinations
from pathlib import Path

from p3_cross_validate import cohens_kappa
from llm_client import llm_json_object
from tiller_tag import build_tiller_prompt, heuristic_tiller, normalize_tiller, validate_tiller

DATA = Path(__file__).parent / "data" / "analysis"
SAMPLE_PATH = DATA / "p3_sample.ndjson"
BERTH_CACHE = DATA / "p3_berth_check_tags.ndjson"  # G35n/G31n 현행 프롬프트 태그
CACHE = DATA / "p3_family_check_tags.ndjson"  # O2/C 태그
OUT = DATA / "p3_family_check.txt"

AXES = ["channel", "sounding", "heading", "berth"]
LLMS = ["O2", "C", "G35n", "G31n"]
RATERS = ["H"] + LLMS


def api_tag(rater: str, body: str) -> dict | None:
    provider, model = {"O2": ("openai", "gpt-4.1-mini"), "C": ("anthropic", "claude-sonnet-5")}[rater]
    for attempt in (1, 2, 3):
        try:
            parsed = llm_json_object(
                system_prompt="",
                user_prompt=build_tiller_prompt(body[:4000]),
                max_tokens=800,
                provider=provider,
                model_override=model,
            )
            parsed = normalize_tiller(parsed)
            validate_tiller(parsed)
            return parsed
        except Exception as e:  # noqa: BLE001
            print(f"  {rater} attempt {attempt}: {str(e)[:100]}")
    return None


def main():
    sample = [json.loads(l) for l in SAMPLE_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
    tags: dict[str, dict[str, dict]] = {r["content_id"]: {"H": normalize_tiller(heuristic_tiller(r["body"]))} for r in sample}

    for l in BERTH_CACHE.read_text(encoding="utf-8").splitlines():
        if l.strip():
            row = json.loads(l)
            name = {"G35n": "G35n", "G31n": "G31n"}.get(row["rater"])
            if name and row["content_id"] in tags:
                tags[row["content_id"]][name] = row["tiller"]

    cached = set()
    if CACHE.exists():
        for l in CACHE.read_text(encoding="utf-8").splitlines():
            if l.strip():
                row = json.loads(l)
                if row["content_id"] in tags:
                    tags[row["content_id"]][row["rater"]] = row["tiller"]
                    cached.add((row["rater"], row["content_id"]))

    jobs = [(rater, r) for rater in ("O2", "C") for r in sample if (rater, r["content_id"]) not in cached]
    print(f"신규 API 호출 {len(jobs)}건 (O2/C)")
    if jobs:
        with open(CACHE, "a", encoding="utf-8") as out, ThreadPoolExecutor(max_workers=8) as pool:
            futs = {pool.submit(api_tag, rater, r["body"] or ""): (rater, r["content_id"]) for rater, r in jobs}
            done = 0
            for fut in as_completed(futs):
                rater, cid = futs[fut]
                t = fut.result()
                if t:
                    out.write(json.dumps({"rater": rater, "content_id": cid, "tiller": t}, ensure_ascii=False) + "\n")
                    out.flush()
                    tags[cid][rater] = t
                done += 1
                if done % 40 == 0:
                    print(f"  {done}/{len(jobs)}")

    rows = [t for t in tags.values() if all(r in t for r in RATERS)]
    lab = lambda v: str(v) if v is not None else "null"  # noqa: E731
    lines = [
        "Gemini 가족 편향 점검 — 균형 패널 (전원 v0.7.1 프롬프트)",
        "=" * 52,
        f"공통 유효 {len(rows)}건 / rater: H, O2(gpt-4.1-mini), C(claude-sonnet-5), G35n, G31n",
        "",
    ]

    # (a) 가족 내 vs 이종 κ
    lines.append("(a) 축별 κ — 가족 내(G↔G) vs 이종 LLM 쌍:")
    fam_flags = []
    for axis in AXES:
        def k(a, b):
            return cohens_kappa([lab(t[a].get(axis)) for t in rows], [lab(t[b].get(axis)) for t in rows])
        within = k("G35n", "G31n")
        cross_pairs = [(a, b) for a, b in combinations(LLMS, 2) if not (a.startswith("G") and b.startswith("G"))]
        crosses = {f"{a}-{b}": k(a, b) for a, b in cross_pairs}
        cross_mean = sum(crosses.values()) / len(crosses)
        flag = within - cross_mean
        fam_flags.append(flag)
        lines.append(f"  {axis:10s}: G내부 {within:.3f} vs 이종평균 {cross_mean:.3f} (격차 {flag:+.3f})  이종: " +
                     " ".join(f"{p}={v:.2f}" for p, v in crosses.items()))
    lines.append(f"  → 평균 격차 {sum(fam_flags)/len(fam_flags):+.3f} (양수 크면 가족 상관 존재)")

    # (b) 균형 패널 leave-one-out
    from collections import Counter
    lines += ["", "(b) 균형 패널 leave-one-out 다수결 일치율:"]
    scores = {r: [] for r in RATERS}
    for axis in AXES:
        for r in RATERS:
            others = [x for x in RATERS if x != r]
            agree = total = 0
            for t in rows:
                votes = Counter(lab(t[o].get(axis)) for o in others)
                top, top_n = votes.most_common(1)[0]
                if list(votes.values()).count(top_n) > 1:
                    continue
                total += 1
                agree += lab(t[r].get(axis)) == top
            scores[r].append(agree / total * 100 if total else 0.0)
    lines.append("        " + "".join(f"{a:>10s}" for a in AXES) + f"{'평균':>10s}")
    ranking = sorted(((sum(v) / len(v), r) for r, v in scores.items()), reverse=True)
    for r in RATERS:
        avg = sum(scores[r]) / len(scores[r])
        lines.append(f"  {r:5s} " + "".join(f"{v:9.1f}%" for v in scores[r]) + f"{avg:9.1f}%")
    lines.append("순위: " + " > ".join(f"{r}({v:.1f}%)" for v, r in ranking))
    lines.append("(참고: 구 Gemini-다수 패널 순위 — G31 92.9 > G35 92.1 > G25 90.7 > O 88.0 > H 84.4)")

    report = "\n".join(lines)
    OUT.write_text(report, encoding="utf-8")
    print(report)
    print(f"\n저장: {OUT}")


if __name__ == "__main__":
    main()
