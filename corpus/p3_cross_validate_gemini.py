"""P3 Gemini: F층 코드북의 모델 이식성 검증 — Vertex AI gemini-2.5-flash.

동일 100건 샘플에 대해 3자 비교:
  - H  = v0.7 휴리스틱 (재계산)
  - G  = Gemini (Vertex AI, F층 코드북 프롬프트)
  - O  = GPT-4.1-mini (p3_llm_results_v2.ndjson 캐시)

산출: κ(H,G) — 코드북이 Gemini에서도 작동하는가
      κ(O,G) — 두 LLM이 같은 코드북으로 얼마나 수렴하는가 (모델 이식성)

사용법: cd corpus && python p3_cross_validate_gemini.py
필요: pip install google-genai / gcloud ADC 인증 / Vertex AI API 활성화
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from p3_cross_validate import cohens_kappa, exact_agreement
from llm_client import extract_json_object, vertex_complete
from tiller_tag import build_tiller_prompt, heuristic_tiller, normalize_tiller, validate_tiller

# 사용법: python p3_cross_validate_gemini.py [모델명]
# 인수 없음 → gemini-2.5-flash (산출 파일명 하위호환: *_gemini.*)
MODEL = sys.argv[1] if len(sys.argv) > 1 else "gemini-2.5-flash"
_SLUG = "gemini" if len(sys.argv) <= 1 else MODEL.replace(".", "-")
# thinking 토큰이 max_output_tokens를 잠식하므로 전 모델 여유 확보
# (진단: 2.5-flash가 800 중 769를 thinking에 소모 → MAX_TOKENS 잘림 → JSON 파싱 실패)
MAX_TOKENS = 4000

DATA = Path(__file__).parent / "data"
SAMPLE_PATH = DATA / "analysis" / "p3_sample.ndjson"
GPT_RESULT_PATH = DATA / "analysis" / "p3_llm_results_v2.ndjson"
RESULT_PATH = DATA / "analysis" / f"p3_llm_results_{_SLUG}.ndjson"
REPORT_PATH = DATA / "analysis" / f"p3_kappa_report_{_SLUG}.txt"

AXES = ["channel", "sounding", "heading", "berth", "bearing", "slack"]


def gemini_tag(body: str) -> dict | None:
    import time

    for attempt in (1, 2, 3, 4):
        try:
            text = vertex_complete(
                system_prompt="",
                user_prompt=build_tiller_prompt(body[:4000]),
                max_tokens=MAX_TOKENS,
                model_override=MODEL,
            )
            parsed = normalize_tiller(json.loads(extract_json_object(text)))
            validate_tiller(parsed)
            return parsed
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            print(f"  attempt {attempt} failed: {msg[:120]}")
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                time.sleep(12 * attempt)  # 쿼터 백오프
            elif attempt < 4:
                time.sleep(2)
    return None


def labels(rows, key_a, key_b, axis):
    a, b = [], []
    for r in rows:
        va, vb = r[key_a].get(axis), r[key_b].get(axis)
        a.append(str(va) if va is not None else "null")
        b.append(str(vb) if vb is not None else "null")
    return a, b


def main() -> None:
    print("=" * 50)
    print(f"P3 Gemini: 코드북 모델 이식성 검증 (Vertex AI · {MODEL})")
    print("=" * 50)

    sample = [json.loads(l) for l in SAMPLE_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
    gpt = {}
    for l in GPT_RESULT_PATH.read_text(encoding="utf-8").splitlines():
        if l.strip():
            r = json.loads(l)
            if r.get("llm"):
                gpt[r["content_id"]] = r["llm"]
    print(f"샘플 {len(sample)}건 / GPT 캐시 {len(gpt)}건")

    cached: dict[str, dict] = {}
    if RESULT_PATH.exists():
        for l in RESULT_PATH.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                if r.get("gemini"):
                    cached[r["content_id"]] = r["gemini"]
        print(f"Gemini 캐시 {len(cached)}건 — 나머지만 호출")

    rows = []
    calls = 0
    for i, r in enumerate(sample):
        cid = r["content_id"]
        h = normalize_tiller(heuristic_tiller(r["body"]))
        if cid in cached:
            g = normalize_tiller(cached[cid])
        else:
            g = gemini_tag(r["body"])
            calls += 1
            if calls % 10 == 0:
                print(f"  Vertex {calls}건 호출 (진행 {i + 1}/{len(sample)})")
        rows.append({"content_id": cid, "heuristic": h, "gemini": g, "gpt": gpt.get(cid)})
    with open(RESULT_PATH, "w", encoding="utf-8") as out:
        for row in rows:
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Vertex 신규 호출: {calls}건")

    valid = [r for r in rows if r.get("gemini") and r.get("gpt")]
    print(f"\n3자 비교 유효: {len(valid)}건")

    lines = [
        f"P3 Gemini: F층 코드북 모델 이식성 (Vertex AI {MODEL})",
        "=" * 54,
        f"유효 샘플: {len(valid)}건 (v1/v2와 동일 층화 샘플)",
        f"H=v0.7 휴리스틱 / G={MODEL} / O=gpt-4.1-mini — 동일 코드북 프롬프트",
        "",
        f"  {'축':10s}  {'κ(H,G)':>8s} {'κ(H,O)':>8s} {'κ(O,G)':>8s}   {'일치(H,G)':>9s} {'일치(O,G)':>9s}",
    ]
    for axis in AXES:
        hg_a, hg_b = labels(valid, "heuristic", "gemini", axis)
        ho_a, ho_b = labels(valid, "heuristic", "gpt", axis)
        og_a, og_b = labels(valid, "gpt", "gemini", axis)
        k_hg, k_ho, k_og = cohens_kappa(hg_a, hg_b), cohens_kappa(ho_a, ho_b), cohens_kappa(og_a, og_b)
        a_hg, a_og = exact_agreement(hg_a, hg_b), exact_agreement(og_a, og_b)
        line = f"  {axis:10s}  {k_hg:8.3f} {k_ho:8.3f} {k_og:8.3f}   {a_hg:8.1f}% {a_og:8.1f}%"
        print(line)
        lines.append(line)

    lines += [
        "",
        "κ 해석: <0.20 poor / 0.21-0.40 fair / 0.41-0.60 moderate / 0.61-0.80 substantial / 0.81+ almost perfect",
        "",
        "축별 양성 검출 수:",
    ]
    for axis in ["heading", "berth", "bearing", "slack"]:
        counts = {k: sum(1 for r in valid if r[k].get(axis)) for k in ("heuristic", "gemini", "gpt")}
        note = "  ← 전원 0건: κ 공허" if all(v == 0 for v in counts.values()) else ""
        lines.append(f"  {axis:10s}: H={counts['heuristic']} G={counts['gemini']} O={counts['gpt']}{note}")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n저장: {REPORT_PATH}")


if __name__ == "__main__":
    main()
