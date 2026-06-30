# Reference Case - KimDalsu

This is a reference case, not the default project protocol.

Use it when a future task explicitly concerns KimDalsu, or when an example of a `partial` client deliverable case is useful. For generic streamer work, read `03_STREAMER_CASE_GENERIC_PROTOCOL.md` first.

Source of truth:

```text
D:\Codex_Workspace\Streamer Consulting Project\김달수_케이스\
```

## Current State

```text
case_id: kimdalsu_20260601
case_type: client_deliverable_case
analysis_status: analysis_closed
report_status: completed on 2026-06-01
execution_status: tracking
case_result_status: partial
portfolio_row_status: partial_ready
public_demo_status: synthetic_candidate
default_disclosure: red
```

## First Files To Consult

- `김달수_CASE_DOSSIER_v3.md`
- `machine/김달수_CaseResult_v3_partial_20260611.json`
- `machine/김달수_EvidencePackage_v3_initial.json`
- `machine/김달수_AbsenceInventory_v3_initial.json`
- `machine/김달수_DisclosureLog_v3_initial.json`
- `deliverables/milestone_report/김달수_채널분석_컨설팅리포트.md` only for exact client-report evidence

## Core Diagnosis

- Not stagnation. Healthy rapid growth over the one-year window.
- Some average-viewer decline is measurement distortion from long streams/no-end streams.
- Peak viewers and chat are more reliable than raw average viewers for this case.
- Cohort position: strong live pull relative to follower count.
- Strategic target: reach 10k followers while preserving adjusted viewer/follower ratio around 1.0-1.2%.
- Warning line: 0.7% or lower at 10k implies hollow growth risk.

## Data Assets

| Asset | Path | Known shape |
|---|---|---|
| daily stats | `data/daily_stats/김달수_Dalsu_방송통계_1년_20260528.csv` | 287 rows; date/followers/stream hours/chat/peak/avg/viewership |
| final cohort | `data/cohort/김달수_코호트_131명.csv` | 131 rows; streamer/followers/peak/avg/adjusted ratio/category/hash |
| initial target list | `data/cohort/수집대상_183명.csv` | 183 rows |
| cohort method | `data/cohort/김달수_코호트_분석_방법과결과.md` | methodology and limitations |

## Open Gates

The case remains `partial` because:

- execution manual is absent
- tracking sheet is absent
- PublicDemoRow is absent/not collected
- 6/16 follow-up items are pending

Pending follow-up:

```text
O17 - 솔랭 vs 종겜 격차 검증
O18 - 자기 의심 영역 정밀화
O19 - 저챗 보강 액션 검토
```

## Disclosure Boundary

Default is `red`.

Restricted terms:

```text
김달수
Dalsu
롤
사촌동생
구체 수치/코호트 명단
보고 직후 인터뷰 원문
```

Allowed public-safe direction:

```text
A스트리머
MOBA 게임
개별 Deep-Dive 분석 마일스톤
```

The anonymized report is only a candidate. External use requires a fresh disclosure review.

## How To Use This Case

KimDalsu is best used as a completed/partial reference case for:

- CaseResult partial vs ready gate
- EvidencePackage and AbsenceInventory examples
- disclosure red/yellow boundaries
- cohort data shape and measurement correction logic

Do not treat it as automatically ready for public demo or CaseResult promotion.
