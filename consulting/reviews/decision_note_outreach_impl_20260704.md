# decision_note: 아웃리치 파이프라인 구현 이견 판정

- date: 2026-07-04
- 관련: `review_note_vtuber_outreach_pipeline_implementation_20260704.md` (Codex) ↔ `specs/vtuber_outreach_pipeline_spec_20260704.md` v0.3 (CC)
- 판정: operator (2026-07-04)

| # | Codex 이견 | 판정 |
|---|---|---|
| 1 | CHZZK API 경로 정합성 | `/service/v1/*` 3종은 2026-07-03~04 라이브 프로브로 검증됨 (스펙 §0). **runbook이 낡은 것** — CHZZK_RUNBOOK에 신규 surface 반영 완료 (CC). |
| 2 | S3/S7 LLM 의존 | 과제 범위 재확인: LLM은 인터페이스 stub만, S7 범위 밖. 갭 없음. |
| 3 | tools/outreach 부재 | 신설이 과제 자체. 기각. |
| 4 | 출력 스키마 (NDJSON 풀 vs collector CSV 관례) | **operator 판정: NDJSON append-only 채널풀 채택.** 근거: `opted_out` 영구 보존이 콜드메일 컴플라이언스 핵심 — upsert+append 구조가 덮어쓰기보다 안전. S6 지표는 기존 collector CSV 관례 유지, 조인은 compose 단계에서. |
| 5 | S6 소프트콘 게이트 분리 | 동의 — 스펙 v0.3 및 pilot2_softcon_route.md에 이미 반영됨 (사용자 세션 경로, 별도 실행 계약). |

status: active
