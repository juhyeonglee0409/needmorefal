"""P3 v2: F층 코드북 기반 κ 재측정 — TILLER v0.7 성층화의 첫 효과 측정.

v1(p3_cross_validate.py)과의 차이:
  - 휴리스틱: 샘플에 저장된 구 태그가 아니라 v0.7 판정 규칙(tiller_tag.heuristic_tiller)으로 재태깅
  - LLM: 축 이름·값 범위만 주던 최소 프롬프트 → F층 코드북 전체 이식(tiller_tag.build_tiller_prompt)
  - 모드 값 정규화(normalize_tiller) 후 κ 산출 — v1의 대소문자 불일치 제거
  - 넓이↔깊이 스왑(H[Ch3,So1] vs L[Ch1,So3] 류) 카운트 추가
  - 산출물 분리: p3_llm_results_v2.ndjson / p3_kappa_report_v2.txt (v1 산출물 보존)

사용법:
  cd corpus
  python p3_cross_validate_v2.py

필요: pip install openai / .env에 OPENAI_API_KEY
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from p3_cross_validate import cohens_kappa, exact_agreement  # .env 로드 포함
from tiller_tag import build_tiller_prompt, heuristic_tiller, normalize_tiller

from openai import OpenAI

DATA = Path(__file__).parent / "data"
SAMPLE_PATH = DATA / "analysis" / "p3_sample.ndjson"
RESULT_PATH = DATA / "analysis" / "p3_llm_results_v2.ndjson"
REPORT_PATH = DATA / "analysis" / "p3_kappa_report_v2.txt"

MODEL = "gpt-4.1-mini"  # v1과 동일 모델 — 프롬프트 개선 효과만 분리 측정

# v1 결과 (p3_kappa_report.txt, 정규화 전) — 비교 기준선
V1_BASELINE = {
    "channel": (0.178, 76.0),
    "sounding": (0.303, 57.0),
    "heading": (0.255, 47.0),
    "berth": (0.055, 30.0),
    "bearing": (0.179, 77.0),
    "slack": (0.075, 55.0),
}

AXES = ["channel", "sounding", "heading", "berth", "bearing", "slack"]


def llm_tag_v2(client: OpenAI, body: str) -> dict | None:
    for attempt in (1, 2):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                temperature=0,
                max_tokens=800,
                response_format={"type": "json_object"},
                messages=[{"role": "user", "content": build_tiller_prompt(body[:4000])}],
            )
            parsed = json.loads(resp.choices[0].message.content)
            return normalize_tiller(parsed)
        except Exception as e:  # noqa: BLE001
            print(f"  attempt {attempt} failed: {e}")
    return None


def main() -> None:
    print("=" * 50)
    print("P3 v2: F층 코드북 기반 κ 재측정")
    print("=" * 50)

    if not SAMPLE_PATH.exists():
        raise SystemExit(f"샘플 없음: {SAMPLE_PATH} — v1과 동일 샘플이 필요합니다.")
    sample = [json.loads(l) for l in SAMPLE_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"\n동일 샘플 로드: {len(sample)}건 (v1과 동일)")

    # LLM 결과만 캐시 재사용 — 휴리스틱은 규칙이 바뀔 수 있으므로 항상 재계산
    cached_llm: dict[str, dict] = {}
    if RESULT_PATH.exists():
        for l in RESULT_PATH.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                if r.get("llm"):
                    cached_llm[r["content_id"]] = r["llm"]
        print(f"캐시된 LLM 결과: {len(cached_llm)}건 — 휴리스틱은 전건 재계산")

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    results = []
    api_calls = 0
    for i, r in enumerate(sample):
        cid = r["content_id"]
        h = normalize_tiller(heuristic_tiller(r["body"]))
        if cid in cached_llm:
            llm = normalize_tiller(cached_llm[cid])
        else:
            llm = llm_tag_v2(client, r["body"])
            api_calls += 1
            if api_calls % 10 == 0:
                print(f"  API {api_calls}건 호출 (진행 {i + 1}/{len(sample)})")
        results.append({
            "content_id": cid,
            "heuristic_v1": r.get("tiller"),  # 참고용 보존
            "heuristic": h,
            "llm": llm,
        })
    with open(RESULT_PATH, "w", encoding="utf-8") as out:
        for row in results:
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"API 신규 호출: {api_calls}건")

    valid = [r for r in results if r.get("llm")]
    print(f"\n유효 비교: {len(valid)}건")

    lines = [
        "P3 v2: F층 코드북 기반 κ 재측정",
        "=" * 46,
        f"유효 샘플: {len(valid)}건 (v1과 동일 100건 층화 샘플)",
        f"LLM: {MODEL} (v1과 동일) / 프롬프트: TILLER v0.7 F층 코드북",
        "휴리스틱: v0.7 판정 규칙으로 재태깅 (저장 태그 미사용)",
        "모드 값 정규화 적용 (v1 raw 수치와 비교 시 참고)",
        "",
        f"  {'축':10s}  {'v1 κ':>7s} {'v2 κ':>7s} {'Δκ':>7s}   {'v1 일치':>7s} {'v2 일치':>7s}",
    ]

    v2_kappas = {}
    for axis in AXES:
        h_labels, l_labels = [], []
        for r in valid:
            h = r["heuristic"].get(axis)
            l = r["llm"].get(axis)
            h_labels.append(str(h) if h is not None else "null")
            l_labels.append(str(l) if l is not None else "null")
        kappa = cohens_kappa(h_labels, l_labels)
        agree = exact_agreement(h_labels, l_labels)
        v2_kappas[axis] = (kappa, agree)
        v1_k, v1_a = V1_BASELINE[axis]
        line = (
            f"  {axis:10s}  {v1_k:7.3f} {kappa:7.3f} {kappa - v1_k:+7.3f}   "
            f"{v1_a:6.1f}% {agree:6.1f}%"
        )
        print(line)
        lines.append(line)

    lines += [
        "",
        "κ 해석: <0.20 poor / 0.21-0.40 fair / 0.41-0.60 moderate / 0.61-0.80 substantial / 0.81+ almost perfect",
        "",
        "축별 양성 검출 수 (공허한 κ 판별):",
    ]
    for axis in ["heading", "berth", "bearing", "slack"]:
        h_pos = sum(1 for r in valid if r["heuristic"].get(axis))
        l_pos = sum(1 for r in valid if r["llm"].get(axis))
        note = "  ← 양성 0건: κ는 공허(전건 null 일치). 양성 포함 표적 표본으로 재측정 필요" if h_pos == 0 and l_pos == 0 else ""
        lines.append(f"  {axis:10s}: H={h_pos} L={l_pos}{note}")
    for axis in ["channel", "sounding"]:
        h_pos = sum(1 for r in valid if (r["heuristic"].get(axis) or 1) > 1)
        l_pos = sum(1 for r in valid if (r["llm"].get(axis) or 1) > 1)
        lines.append(f"  {axis:10s}: H(>1)={h_pos} L(>1)={l_pos}")

    # 넓이↔깊이 스왑 분석 (E-05 결합의 측정 흔적)
    swaps = []
    disagreements = []
    for r in valid:
        h_ch, l_ch = r["heuristic"].get("channel"), r["llm"].get("channel")
        h_so, l_so = r["heuristic"].get("sounding"), r["llm"].get("sounding")
        big = abs(int(h_ch or 1) - int(l_ch or 1)) >= 2 or abs(int(h_so or 1) - int(l_so or 1)) >= 2
        if big:
            disagreements.append(f"  {r['content_id'][:8]}: H[Ch{h_ch},So{h_so}] vs L[Ch{l_ch},So{l_so}]")
        # 스왑: 한 rater는 분기 높음/깊이 낮음, 다른 rater는 그 반대
        if (int(h_ch or 1) > int(l_ch or 1) and int(h_so or 1) < int(l_so or 1)) or (
            int(h_ch or 1) < int(l_ch or 1) and int(h_so or 1) > int(l_so or 1)
        ):
            swaps.append(r["content_id"][:8])

    lines += [
        "",
        f"넓이-깊이 스왑 (Ch↑So↓ vs Ch↓So↑ 교차): {len(swaps)}건 — {', '.join(swaps) if swaps else '없음'}",
        "",
        f"대형 불일치 (|ΔCh|>=2 또는 |ΔSo|>=2): {len(disagreements)}건",
        *disagreements,
    ]

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n저장: {REPORT_PATH}")


if __name__ == "__main__":
    main()
