# 구비바 v3 재정독 패스 + migration prep

**작성:** 2026-06-11  
**기준:** `MASTER_v2_M7_1_canonical_schema_pack_20260610.json` + `구비바_project_step1_20260610.json`  
**목적:** 구비바 케이스를 v3/M7.1 schema로 migration하기 전, 원문 문서의 확정·보류·차단 상태를 다시 정렬한다.

## 1. 재정독 판정

| 영역 | 판정 | v3 처리 |
|---|---|---|
| §1 정체성 | 닫힘. 본인 면담 발화 기반 v3 정체성 추출 확정. | `identity_summary.identity_clarity = high` |
| §2 데이터 정합성 | 1년 CSV 재검산 완료. 227방송일, 8컬럼. | `EvidencePackage` + `MeasurementCorrection`에 반영 |
| §3 보정 | 14h+ 노방종 0일. skip이 아니라 보정 미적용 통과. | `correction_method = raw_equals_corrected` |
| §6·§7·§9 | 결론문서가 아니라 조기 진입자료. | `open_analysis_tasks`와 red evidence로 보존 |
| §4 | blocking step. 종합게임 주 코호트 + 버추얼 보조 코호트. | `cohort.cohort_confidence = unknown` |
| §5 | 아직 미실행. | `CaseResult.case_result_status = not_ready` |
| O13 | 핵심 모듈이지만 확정결론 아님. | `synthesis_status = analyst_synthesis_pending_client_response` |
| O17 | 결과 확인일 지남. | `AbsenceInventory`에 unknown으로 보존 |
| PublicDemo | 불가. | `public_demo_status = blocked` |

## 2. 본인명시 용어 정정

기존 문서의 "본인 명시 확인 안 됨" 표현은 v3에서 다음처럼 정정한다.

```text
구성 재료 = 본인 면담 발화 기반
통합 구조 = 분석가 통합 해석
상태 = 전달 후 수용/교정 반응 확인 전
```

따라서 C21/O13은 재료가 불확실한 것이 아니라, **매력 의심·도네 자기검열·자기정의 격차를 하나의 동일 뿌리로 묶는 통합 구조의 수용/교정 반응이 아직 없는 상태**다.

## 3. 데이터 재검산

| 항목 | 값 |
|---|---:|
| CSV 행 수 | 227 |
| 기간 | 2025-05-29 ~ 2026-05-29 |
| 전체 기간 일수 | 366 |
| 방송일 | 227 |
| 비방송일 | 139 |
| 팔로워 | 471 → 711 |
| 팔로워 증가율 | 50.96% |
| 방송시간 중앙값 | 5.7h |
| 방송시간 최대 | 9.6h |
| 14h+ 노방종 | 0일 |
| peak max | 148 |
| peak p95 | 37.7 |
| peak median | 20.0 |
| recent 90d peak median | 23.0 |
| recent 90d peak p95 | 42.85 |
| recent 90d peak max | 67 |

## 4. v3 claim mapping 핵심

| ID | v3 claim_level | components_source | synthesis_status | interpretation_status | 비고 |
|---|---|---|---|---|---|
| C20 | L0_record | self_statement | client_accepted | active_claim | §1 정체성 본질 |
| C21 | L4_intervention_candidate | self_statement | analyst_synthesis_pending_client_response | open_claim | O13 핵심. 전달 후 반응 필요 |
| C2 | L1_descriptive_stat | metric | none | active_claim | 완만한 꾸준 성장형 데이터 |
| C3 | L1_descriptive_stat | metric | none | active_claim | 노방종 0일/보정 미적용 통과 |
| C23 | L0_record | self_statement | none | active_claim | 영속 의향 |
| C25 | L0_record | self_statement | none | active_claim | 매력 의심 우선순위 |
| C31 | L4_intervention_candidate | self_statement | client_accepted | active_claim | 큰 노선 및 토론 배틀 의사결정 |

## 5. 다음 작업 차단 목록

1. §4 final cohort 수집 전에는 §5 진단 불가.
2. §5·§7 근거 전에는 O13 전달문 확정 금지.
3. O17 결과 확인 전에는 쇼츠 실행장벽을 확정하지 말 것.
4. PublicDemoRow 생성 금지. 현 상태는 private validation case.
5. PortfolioRow 생성 금지. `CaseResult`도 stub/not_ready 상태만 허용.

## 6. 생성된 migration prep 산출물

- `구비바_project_v3_migration_candidate_20260611.json`
- `구비바_CaseResult_v3_stub_20260611.json`
- `구비바_EvidencePackage_v3_initial_20260611.json`
- `구비바_AbsenceInventory_v3_initial_20260611.json`
- `구비바_DisclosureLog_v3_initial_20260611.json`
- `구비바_ValidationCaseRegistryRow_v3_20260611.csv/json`

## 7. 권장 다음 순서

```text
1. migration candidate 검토
2. §4 Charles 진단 재개
3. Arthur collect protocol 보강
4. cohort_final + robustness table 생성
5. §5 6단계 진단
6. partial CaseResult로 승격
```
