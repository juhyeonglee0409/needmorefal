# -*- coding: utf-8 -*-
"""TILLER v0.7 F층 휴리스틱 회귀 테스트 — 코드북 앵커 예시 + κ 오류 분석에서 추가된 사례.

사용법: cd corpus && python test_tiller_tag.py
정규식·판정 규칙을 수정할 때마다 실행할 것 (개선 큐 ④, TILLER_Framework_v0_7_0.md §2.9).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from tiller_tag import heuristic_tiller  # noqa: E402

CASES = [
    # (설명, body, 기대값 부분사전) — F층 코드북 앵커 예시 (§2.1~2.7)
    ("So1 조회", "X는 뭐야", {"channel": 1, "sounding": 1}),
    ("Ch2×So2 최소형", "이 코드의 문제가 로직 오류인지 성능 문제인지 판단하고, 원인을 추적해",
     {"channel": 2, "sounding": 2}),
    ("표준 발화 (Role+Category+Ch3)",
     "나는 LLM 상호작용의 인식론적 위험을 연구하고 있어. 환각이나 명시적 오류가 아닌, "
     "사실적 출력이 판단 기준을 이동시키는 현상에 집중해. 관련 연구를 찾아서 "
     "뒷받침/교정/무관/조건적 지지로 분류하고 각각의 근거를 제시해.",
     {"heading": "Role", "berth": "Category", "channel": 3}),
    ("So3 체인", "원인을 추적하고, 검증한 뒤에 결론을 도출해",
     {"sounding": 3}),
    ("So4 자기점검", "네 추론 과정에 오류가 있는지 점검해", {"sounding": 4}),
    ("So4 아님 (외부 대상)", "이 논문의 주장을 검토하고 문제점을 평가해", {"sounding": 2}),
    ("포맷 리스트는 Ch1", "블로그 글을 다음 형식으로 써줘:\n- 제목\n- 본문\n- 해시태그\n- 요약문",
     {"channel": 1}),
    ("순차 단계는 Ch 아님", "다음 순서로 해줘.\n1. 자료를 수집해\n2. 핵심을 정리해\n3. 결론을 작성해",
     {"channel": 1}),
    ("진짜 범주 리스트는 Ch3", "고객 피드백을 아래 범주로 분류해줘\n- 가격 불만\n- 품질 불만\n- 배송 불만\n- 기타",
     {"channel": 3}),
    ("SLACK raw 경계", "draw a cute strawberry on the table", {"slack": None}),
    ("SLACK raw 진짜", "해석 없이 원자료 상태로 보여줘", {"slack": "Raw"}),
    ("BERTH method", "단순 요약이 아니라 구조적 분석을 해줘. 나열하지 말고 인과로 엮어줘.",
     {"berth": "Method"}),
    ("BERTH 아님 (긍정 절차)", "step-by-step으로 단계별로 설명해줘", {"berth": None}),
    ("BEARING output", "위에서 네가 분석한 결과를 기반으로 요약해줘", {"bearing": "Output"}),
    ("BEARING 아님 (외부)", "previous studies show X. explain the topic", {"bearing": None}),
    ("HEADING frame 우연매칭 배제", "use the react framework to build a wireframe app",
     {"heading": None}),
    ("HEADING frame 진짜", "비용 구조의 관점에서 이 사업을 평가해줘", {"heading": "Frame"}),
    ("Ch4 열린 분기", "이 현상에 대해 가능한 모든 해석을 도출해줘", {"channel": 4}),
    # P3 v2 κ 오류 분석에서 추가된 사례 (2026-07)
    ("제약조건 리스트는 Ch1", "다음 제약 조건을 고려하여 코드를 작성해주세요:\n- Python 3.8 이상 호환\n- 외부 라이브러리 최소화\n- 메모리 사용량 최적화\n- 단위 테스트 포함",
     {"channel": 1}),
    ("요구사항 불릿은 Ch1", "Act as a creative math educator. Your method should:\n- Incorporate interactive elements\n- Focus on visual learning\n- Apply real world examples\n- Encourage collaboration",
     {"channel": 1}),
    ("쉼표 나열+중은 Ch3", "이 문제를 틀린 이유를 개념 부족, 실수, 오해 중 어디에 속하는지 분석해줘.",
     {"channel": 3}),
    ("슬래시+N가지는 Ch3", "AI 코치 시스템 프롬프트를 설계해줘. 친구/코치/멘토 3가지 스타일이 있어.",
     {"channel": 3}),
    ("카테고리 큐+리스트는 Ch3", "다음 카테고리에서 경고 신호를 찾아내줘:\n- 매출 인식 방식의 변화\n- 일회성 비용 처리\n- 영업현금흐름 vs 순이익 괴리\n- 재고 회전율 급변",
     {"channel": 3}),
    ("사진 용어 RAW는 slack 아님", "orange tabby cat selfie, 85mm f/11, ISO 100, 8K RAW, no blur",
     {"slack": None}),
    ("raw output 지시는 Raw", "search the logs and give me the raw output, unfiltered",
     {"slack": "Raw"}),
]


def main() -> int:
    fails = 0
    for name, body, expected in CASES:
        tags = heuristic_tiller(body)
        bad = {k: (tags[k], v) for k, v in expected.items() if tags[k] != v}
        if bad:
            fails += 1
            print(f"FAIL {name}")
            for k, (got, want) in bad.items():
                print(f"   {k}: got={got!r} want={want!r}  reason={tags.get(k + '_reason')}")
        else:
            print(f"ok   {name}")
    print(f"\n{len(CASES) - fails}/{len(CASES)} passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
