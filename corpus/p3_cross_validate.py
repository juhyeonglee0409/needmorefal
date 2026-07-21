"""P3: LLM 교차검증 — 100건 샘플 TILLER 태깅 + Cohen's κ 산출.

사용법:
  cd "Contextwins Project/tools/corpus"
  python3 p3_cross_validate.py

필요: pip install openai
.env에 OPENAI_API_KEY 필요.
"""
from __future__ import annotations

import json
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

# ── .env 로드 ──
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

from openai import OpenAI  # noqa: E402

DATA = Path(__file__).parent / "data"
SAMPLE_PATH = DATA / "analysis" / "p3_sample.ndjson"
RESULT_PATH = DATA / "analysis" / "p3_llm_results.ndjson"
REPORT_PATH = DATA / "analysis" / "p3_kappa_report.txt"


def load_corpus():
    records = []
    with open(DATA / "corpus_tagged.ndjson", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line.strip()))
    return records


def stratified_sample(records, n=100, seed=42):
    random.seed(seed)
    strata = defaultdict(list)
    for r in records:
        strata[(r["domain"], r["lang"])].append(r)
    sample = []
    total = len(records)
    for key, group in sorted(strata.items()):
        k = max(1, round(len(group) / total * n))
        sample.extend(random.sample(group, min(k, len(group))))
    if len(sample) > n:
        random.shuffle(sample)
        sample = sample[:n]
    return sample


def tiller_prompt(body: str) -> str:
    return f"""TILLER v0.6.3: Classify this prompt on 6 axes.
CHANNEL(1-4): 1=single path, 2=binary compare, 3=multi-branch, 4=divergent
SOUNDING(1-4): 1=single verb, 2=two verbs/chain, 3=3+ verbs or 2+ chains, 4=metacognitive
HEADING(null/Frame/Role/Both): role or context declaration in opening
BERTH(null/Category/Method/Both): exclusion or methodology instruction
BEARING(null/Experience/Output/Failure): reference to prior output/experience/failure
SLACK(null/Include/Raw): include-all or verbatim instruction

Return ONLY a JSON object:
{{"channel":int,"sounding":int,"heading":"value or null","berth":"value or null","bearing":"value or null","slack":"value or null"}}

Prompt:
{body[:2000]}"""


def llm_tag(client: OpenAI, body: str) -> dict | None:
    try:
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0,
            max_tokens=300,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": tiller_prompt(body)}],
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        print(f"  ❌ {e}")
        return None


def cohens_kappa(labels_a: list, labels_b: list) -> float:
    """Cohen's κ for two raters."""
    assert len(labels_a) == len(labels_b)
    n = len(labels_a)
    if n == 0:
        return 0.0
    cats = sorted(set(labels_a) | set(labels_b))
    cat_idx = {c: i for i, c in enumerate(cats)}
    k = len(cats)
    matrix = [[0] * k for _ in range(k)]
    for a, b in zip(labels_a, labels_b):
        matrix[cat_idx[a]][cat_idx[b]] += 1
    po = sum(matrix[i][i] for i in range(k)) / n
    row_sums = [sum(matrix[i]) for i in range(k)]
    col_sums = [sum(matrix[i][j] for i in range(k)) for j in range(k)]
    pe = sum(row_sums[i] * col_sums[i] for i in range(k)) / (n * n)
    if pe == 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


def exact_agreement(a: list, b: list) -> float:
    return sum(1 for x, y in zip(a, b) if x == y) / len(a) * 100


def main():
    print("=" * 50)
    print("P3: LLM 교차검증 (Cohen's κ)")
    print("=" * 50)

    # 1. 샘플링
    if SAMPLE_PATH.exists():
        sample = [json.loads(l) for l in SAMPLE_PATH.read_text().splitlines() if l.strip()]
        print(f"\n기존 샘플 로드: {len(sample)}건")
    else:
        records = load_corpus()
        sample = stratified_sample(records)
        with open(SAMPLE_PATH, "w", encoding="utf-8") as f:
            for r in sample:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"\n새 샘플 생성: {len(sample)}건")

    # 2. LLM 태깅 (이미 결과 있으면 스킵)
    if RESULT_PATH.exists():
        results = [json.loads(l) for l in RESULT_PATH.read_text().splitlines() if l.strip()]
        ok = sum(1 for r in results if r.get("llm"))
        print(f"기존 결과 로드: {ok}/{len(results)} 성공")
    else:
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        results = []
        for i, r in enumerate(sample):
            llm = llm_tag(client, r["body"])
            results.append({"content_id": r["content_id"], "heuristic": r["tiller"], "llm": llm})
            if (i + 1) % 10 == 0:
                ok = sum(1 for x in results if x.get("llm"))
                print(f"  {i+1}/100 ({ok} 성공)")
        with open(RESULT_PATH, "w", encoding="utf-8") as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        ok = sum(1 for r in results if r.get("llm"))
        print(f"\n태깅 완료: {ok}/{len(results)} 성공")

    # 3. κ 계산
    valid = [r for r in results if r.get("llm")]
    print(f"\n유효 비교: {len(valid)}건")

    axes = {
        "channel": lambda t: t.get("channel"),
        "sounding": lambda t: t.get("sounding"),
        "heading": lambda t: t.get("heading"),
        "berth": lambda t: t.get("berth"),
        "bearing": lambda t: t.get("bearing"),
        "slack": lambda t: t.get("slack"),
    }

    report_lines = ["P3: LLM 교차검증 결과", "=" * 40, f"유효 샘플: {len(valid)}건", ""]

    for axis_name, getter in axes.items():
        h_labels = []
        l_labels = []
        for r in valid:
            h = getter(r["heuristic"])
            l = getter(r["llm"])
            # null → "null" 문자열로 통일
            h_labels.append(str(h) if h is not None else "null")
            l_labels.append(str(l) if l is not None else "null")

        kappa = cohens_kappa(h_labels, l_labels)
        agree = exact_agreement(h_labels, l_labels)
        line = f"  {axis_name:10s}: κ={kappa:.3f}  일치율={agree:.1f}%"
        print(line)
        report_lines.append(line)

    # κ 해석 가이드
    report_lines.extend([
        "",
        "κ 해석 기준:",
        "  <0.20: 거의 일치 없음 (poor)",
        "  0.21-0.40: 약한 일치 (fair)",
        "  0.41-0.60: 보통 (moderate)",
        "  0.61-0.80: 상당한 일치 (substantial)",
        "  0.81-1.00: 거의 완벽 (almost perfect)",
    ])

    # 불일치 사례 분석
    report_lines.extend(["", "불일치 주요 사례:"])
    for r in valid:
        h_ch = r["heuristic"].get("channel")
        l_ch = r["llm"].get("channel")
        h_so = r["heuristic"].get("sounding")
        l_so = r["llm"].get("sounding")
        if abs(int(h_ch or 1) - int(l_ch or 1)) >= 2 or abs(int(h_so or 1) - int(l_so or 1)) >= 2:
            report_lines.append(
                f"  {r['content_id'][:8]}: H[Ch{h_ch},So{h_so}] vs L[Ch{l_ch},So{l_so}]"
            )

    REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"\n✅ {REPORT_PATH} 저장")


if __name__ == "__main__":
    main()
