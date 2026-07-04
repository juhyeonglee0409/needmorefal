# 핸드오프 데이터북 전환 제안 리뷰 (implementation/operations)

- type: review_note
- date: 2026-07-04
- task: proposal_handoff_databook_20260704 검토
- owner: Codex (review only)
- status: reviewed

CC 제안 5개 관점에 대해, 현재 운영 중인 `SESSION_NOTE.md`와 `consulting/tools/ops/lint_handoff.py`, 그리고 `consulting/tools/outreach`의 YAML 처리 방식만 근거로 판단.

## 1) 스키마 실용성 (현재 핸드오프 작성 흐름 적합성)

결론: 조건부

- 근거:
  - 현재 `SESSION_NOTE.md`는 `## [Surface] date` 블록이 누적되는 단일 파일 형식이라 동시 세션 쓰기 충돌이 발생했음(세션 노트 상단 기록 근거).
  - `lint_handoff.py`는 이 헤더 형식만 검증(`## [CC|Codex|Cowork] YYYY-MM-DD` + 분 단위 시간 경고)하며, 제안 스키마를 전혀 인지하지 못함.
  - 즉, 제안 스키마는 운영상 장점이 있지만, **적용 전 `lint_handoff.py`와 관련 도구를 frontmatter-aware로 확장**해야 함.
- 간단한 개선안:
  - 기존 `## [Surface] ...` 헤더 호환 + 선택적 frontmatter(필수값만 필수화)로 단계 도입하면 기존 툴 교체 비용을 최소화 가능.

## 2) INDEX 생성 위치 (별도 스크립트 vs CI vs 세션 종료 훅)

결론: 반대 (CI 단독), 조건부 (훅+스크립트 조합)

- 근거:
  - 제안은 다수 파일 기반 인덱싱이라 세션 내 즉시 가시성이 중요함. CI-only는 로컬/오프라인 상태에서 INDEX 갱신 지연.
  - `lint_handoff.py`는 CI 게이팅 관점으로 단일 파일 체크에 강점이 있으나, INDEX 생성은 현재 기능 범위를 벗어남.
- 권고:
  - `codex`가 `collect/normalize/patch` 작업 직후 실행할 수 있는 **로컬 전용 생성 스크립트**를 두고,
  - CI에서는 INDEX와 본문 정합성만 read-only 검증.

## 3) 파일명 규칙(타임스탬프+surface) 충돌/정렬/Windows 이슈

결론: 조건부

- 근거:
  - 예시 `2026-07-04T1730-CC.md`는 Windows 문자 제약(콜론 미사용)에는 유리하고 정렬도 날짜 기준으로 안정적.
  - 다만 1분 단위면 동일 분 동시 생성 충돌 가능성이 있음(특히 CC/Codex 동시 편집이 잦은 세션 환경).
  - `SESSION_NOTE.md`에서 이미 동시 쓰기 충돌 이력이 있으므로, 충돌 완화가 핵심.
- 간단한 대체안:
  - 시간 정밀도를 초 단위 또는 `T1730-01` 같이 순번 suffix를 추가해 충돌 가능성을 원천 제거.

4) frontmatter 파서: stdlib vs outreach 자체 YAML 파서 재사용

결론: 반대 (outreach 파서 직접 재사용)

- 근거:
  - `consulting/tools/outreach/classify.py`의 `_load_simple_yaml_lists`는 `key:` + `- item` 형태의 단순 리스트만 파싱하며, 타입/스키마 검증/오류 반납이 거의 없음.
  - proposal frontmatter는 문자열/배열/상태값 등을 요구하므로 범위와 엄밀도가 미달.
  - stdlib만으로는 정식 YAML 파싱이 불가하며(표준 라이브러리에 YAML 파서 없음), 신뢰성 있는 파싱을 위해 별도 파서 정책이 필요.
- 권고:
  - (A) `PyYAML` 도입 + schema 검증, 또는
  - (B) `json-frontmatter`로 포맷을 제한(표준 `json` 파싱)해 명세 단순화.

## 5) 반대/조건부/단순 대안 제시

결론: 조건부 + 단순 대안 동의

- 근거:
  - 완전 교체보다 **2단계 마이그레이션**이 운영 안정성이 높음.
  - 1단계: 새 파일 방식 + index 생성기만 도입해 동시쓰기 충돌/읽기 탐색성 개선.
  - 2단계: 기존 `SESSION_NOTE.md`는 `ARCHIVE`로 영구화한 뒤 최소 1~2주 운영 후 툴/CI 정합성 확인 후 폐기.
- 제안 대안(더 단순):
  - 최초엔 `.md` handoff 단일 생성 + 경량 frontmatter, 기존 `SESSION_NOTE` 유지 + 읽기 전용 파서만 추가.
  - `outreach` 파서는 독립 모듈로 두고, frontmatter 파서는 ops 전용으로 분리 구현.
