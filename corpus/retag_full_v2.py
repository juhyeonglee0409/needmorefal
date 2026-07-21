"""전수 재태깅 v2 — corpus 5,836건을 v0.7 F층 코드북 + gemini-3.1-pro-preview로 재태깅.

모델 선정 근거: p3_model_matrix.txt — 5-rater 패널 다수결 일치율 1위 (92.9%).
사전등록: data/analysis/L4v2_preregistration.md (2026-07-08 잠금) — 결과 산출 후 채점.

설계:
  - 입력: data/corpus_tagged.ndjson (구 휴리스틱 태그 포함)
  - 출력: data/corpus_tagged_v2.ndjson — tiller=신규, tiller_v1=구 태그 보존, tiller_model 기록
  - 체크포인트: 성공 행만 append; 재실행 시 완료된 content_id 스킵 → 중단·429 안전
  - 동시성: 워커 6 + 지수 백오프 (프리뷰 쿼터 대응)

사용법: cd corpus && python retag_full_v2.py [--model MODEL] [--workers N]
"""
from __future__ import annotations

import argparse
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from llm_client import extract_json_object, vertex_complete
from tiller_tag import build_tiller_prompt, normalize_tiller, validate_tiller

DATA = Path(__file__).parent / "data"
INPUT_PATH = DATA / "corpus_tagged.ndjson"
OUTPUT_PATH = DATA / "corpus_tagged_v2.ndjson"
ERROR_PATH = DATA / "retag_v2_errors.ndjson"

_write_lock = threading.Lock()


def tag_one(model: str, body: str) -> dict | None:
    for attempt in range(1, 6):
        try:
            text = vertex_complete(
                system_prompt="",
                user_prompt=build_tiller_prompt(body[:4000]),
                max_tokens=4000,
                model_override=model,
            )
            parsed = normalize_tiller(json.loads(extract_json_object(text)))
            validate_tiller(parsed)
            return parsed
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                time.sleep(min(15 * attempt, 60))
            elif attempt < 5:
                time.sleep(3)
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gemini-3.1-pro-preview")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    records = [json.loads(l) for l in INPUT_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
    done: set[str] = set()
    if OUTPUT_PATH.exists():
        for l in OUTPUT_PATH.read_text(encoding="utf-8").splitlines():
            if l.strip():
                done.add(json.loads(l)["content_id"])
    todo = [r for r in records if r["content_id"] not in done]
    print(f"전체 {len(records)}건 / 완료 {len(done)}건 / 잔여 {len(todo)}건 / 모델 {args.model} / 워커 {args.workers}")

    out = open(OUTPUT_PATH, "a", encoding="utf-8")
    err = open(ERROR_PATH, "a", encoding="utf-8")
    ok = fail = 0
    start = time.time()

    def work(rec: dict):
        tags = tag_one(args.model, rec.get("body") or "")
        return rec, tags

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(work, r) for r in todo]
        for i, fut in enumerate(as_completed(futures), 1):
            rec, tags = fut.result()
            with _write_lock:
                if tags:
                    row = dict(rec)
                    row["tiller_v1"] = rec.get("tiller")
                    row["tiller"] = tags
                    row["tiller_model"] = args.model
                    out.write(json.dumps(row, ensure_ascii=False) + "\n")
                    out.flush()
                    ok += 1
                else:
                    err.write(json.dumps({"content_id": rec["content_id"]}, ensure_ascii=False) + "\n")
                    err.flush()
                    fail += 1
            if i % 100 == 0:
                rate = i / (time.time() - start)
                eta_min = (len(todo) - i) / rate / 60 if rate else 0
                print(f"  {i}/{len(todo)} (성공 {ok} 실패 {fail}) — {rate:.1f}건/s, ETA {eta_min:.0f}분", flush=True)

    out.close()
    err.close()
    print(f"완료: 성공 {ok} / 실패 {fail} (실패분은 재실행으로 충전)")


if __name__ == "__main__":
    main()
