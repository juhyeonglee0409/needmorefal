# Proposal: SESSION_NOTE → 핸드오프 데이터북 전환

- type: proposal (CC → Codex 검토 요청)
- date: 2026-07-04
- 배경: SESSION_NOTE.md가 1,100줄+ (계약의 30건 아카이브 임계 초과). operator가 스키마 기반 분할 방향을 승인, 축 설계는 검토 중. 오늘 두 세션이 같은 파일에 동시 쓰기 직전까지 간 사례 발생 (직렬화 규칙으로 회피).

## 제안 구조

```
_WORKING_CONTEXT/handoffs/
  2026-07-04T1730-CC.md          ← 핸드오프 1건 = 파일 1개
  2026-07-04T1644-Codex.md
INDEX.md                          ← 스크립트 생성 (최근 N건 frontmatter 표)
SESSION_NOTE_archive_~20260704.md ← 기존 파일 동결 (마이그레이션 없음)
```

각 핸드오프 파일:

```yaml
---
surface: CC | Codex | Cowork
timestamp: 2026-07-04T17:30       # ISO, 분 단위
task: 한 줄 제목
status: raw | reviewed | commit-candidate | hold | excluded
next_surface: CC | Codex | Cowork | operator
files: [상대경로, ...]
decision_ids: [DL_..., ...]       # 관련 결정 (없으면 빈 배열)
links: [관련 문서 slug, ...]
---

(산문: what was done / next surface가 할 일 / boundaries — 기존 5필드 서식 유지)
```

## 기대 효과

1. 쓰기 충돌 구조적 소멸 (핸드오프마다 다른 파일)
2. 새 세션 읽기 비용 절감 (INDEX만 읽고 필요 항목 파고들기)
3. frontmatter 기계 판독 → status/surface 필터 조회 가능
4. 기존 도구 승격: lint_handoff.py가 frontmatter 검증, status_board.py가 regex 대신 frontmatter 파싱

## 마이그레이션 정책 (제안)

- 기존 1,100줄은 역변환하지 않음. 동결 후 새 구조는 전방 적용만.
- 계약(12_CONTINUITY_CONTRACT) Part 1 개정 + DECISION_LOG 기록 필요 (operator 권한).

## Codex에 요청하는 검토 관점

1. 이 스키마가 Codex 세션의 핸드오프 작성 흐름에서 실용적인가? (필드 과다/과소, 매 세션 쓰기 마찰)
2. INDEX 생성을 어디에 붙일 것인가 — 별도 스크립트 vs CI vs 세션 종료 훅. 구현 관점 권고.
3. 파일명 규칙(타임스탬프+surface)의 충돌·정렬·Windows 경로 이슈.
4. frontmatter 파서를 stdlib로 갈 것인가(outreach의 자체 yaml 파서 재사용?) — 의존성 정책 관점.
5. 반대하거나 더 단순한 대안이 있으면 제시. 동의를 위한 동의 금지.
