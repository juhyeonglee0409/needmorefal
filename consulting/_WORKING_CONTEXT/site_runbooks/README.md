# Site Runbooks

사이트별 실전 운영 지식을 한 곳에 모은 디렉터리.

## Purpose

protocol, decision log, session note, run note에 흩어진 "이 사이트에서 실제로 뭐가 먹혔고 뭐가 깨졌는지"를 빠르게 찾게 한다.

이 문서들은 canonical 판단 상태(CaseResult, disclosure, promotion)를 바꾸지 않는다. 각 runbook은 최신 운영 지도이고, 상세 근거는 기존 run note / decision log / session note로 링크한다.

## Files

| File | Site | Status |
|---|---|---|
| `TEMPLATE_SITE_RUNBOOK.md` | (template) | — |
| `SOFTC_ONE_RUNBOOK.md` | softc.one | active |
| `AURO_LIVE_RUNBOOK.md` | auro.live | partial |
| `CHZZK_RUNBOOK.md` | chzzk.naver.com | partial |

## Relationship to Other Documents

| Document | Role | Runbook과의 관계 |
|---|---|---|
| `03_STREAMER_CASE_GENERIC_PROTOCOL.md` | 케이스 무관 수집 파이프라인 원칙 | runbook은 사이트별 특화. 원칙은 generic protocol이 정본. |
| `07_DECISION_LOG.md` | 정책/운영 결정 기록 | runbook은 결정 로그를 대체하지 않음. 결정 ID를 포인터로 참조. |
| `SESSION_NOTE.md` | 세션 핸드오프 노트 | runbook은 session note를 삭제/병합하지 않음. proven run 포인터만. |
| Run notes (work/ 하위) | 개별 수집 실행 기록 | runbook은 run note 요약 + 포인터. run note 자체는 보존. |

## Staleness Management

- **Proven Run 추가 시**: 해당 runbook의 `Last verified` 날짜를 갱신한다.
- **Working Route 변경 시**: 경로 상태 변경 + `Last verified` 갱신.
- **30일 이상 검증 없으면**: `Status`를 `stale`로 변경하되, 내용은 삭제하지 않는다.
- **새 decision log 엔트리가 해당 사이트를 scope에 포함하면**: runbook의 Related Decisions에 추가한다.

## Constraints

- 쿠키, 토큰, localStorage, auth header, raw HTML, screenshot 내용 금지.
- Session note, decision log, run note를 삭제하거나 병합하지 않는다.
- Runbook은 요약과 포인터만 가진다.
