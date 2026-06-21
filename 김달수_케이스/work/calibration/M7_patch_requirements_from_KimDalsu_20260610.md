# M7 Patch Requirements from 김달수 1차 마일스톤 리포트

**입력:** 김달수 채널분석 컨설팅리포트  
**목적:** M7 Schema Stabilization Patch에 실제 완성 산출물 요구를 반영한다.  
**상태:** M6.5 calibration 결과. M7 착수 전 반영 권고.

---

## 1. M7에 반드시 추가할 canonical objects

### 1.1 DeliverableMilestone

김달수 리포트는 `CaseResult` 자체가 아니라 클라이언트용 1차 마일스톤 산출물이다. 따라서 `CaseResult` 안에 다음 구조를 둔다.

```json
{
  "deliverable_milestones": [
    {
      "milestone_id": "milestone_1_analysis_report",
      "milestone_type": "analysis_report",
      "audience": "client",
      "section_sequence": [],
      "client_impact_headline": "string",
      "headline_metrics": [],
      "completed": true,
      "execution_manual_included": false,
      "tracking_sheet_included": false,
      "disclosure_tag": "red"
    }
  ]
}
```

### 1.2 MeasurementCorrection

김달수 리포트의 가장 중요한 방법론적 발견은 노방종으로 인한 평균시청자 왜곡이다. M7에는 다음 객체가 필요하다.

```json
{
  "measurement_corrections": [
    {
      "correction_id": "string",
      "affected_metric": "avg_viewers",
      "distortion_source": "long_stream_hours",
      "correction_method": "peak_ratio | time_weighted | exclude_long_stream_days | none",
      "raw_vs_corrected_summary": "string",
      "recommendation_impact": "string",
      "evidence_refs": [],
      "disclosure_tag": "yellow|red"
    }
  ]
}
```

### 1.3 CohortBenchmark with Robustness Tests

```json
{
  "cohort": {
    "population_source": "string",
    "base_population_n": null,
    "filter_steps": [],
    "final_n": null,
    "rank_metrics": [],
    "robustness_tests": [],
    "precision_guardrail": "string",
    "cohort_confidence": "high|medium|low"
  }
}
```

### 1.4 StrategicTarget

```json
{
  "strategic_targets": [
    {
      "target_name": "string",
      "target_metric": "string",
      "recommended_band": "string|null",
      "warning_threshold": "string|null",
      "tradeoff_rationale": "string",
      "monitoring_window": "string|null",
      "tracking_required": true
    }
  ]
}
```

### 1.5 ContentFunnelAnalysis

```json
{
  "content_funnel_analysis": [
    {
      "content_type": "string",
      "reach_signal": "high|medium|low|unknown",
      "conversion_signal": "high|medium|low|unknown",
      "identity_fit": "fit|partial|misfit|unknown",
      "recommendation": "string",
      "caveat": "string|null"
    }
  ]
}
```

### 1.6 Limitations and OpenAnalysisTasks

부록 B/C가 실제로 리포트의 안전장치 역할을 하므로, 한계와 open은 별도 필드로 유지한다.

```json
{
  "limitations": [],
  "open_analysis_tasks": []
}
```

---

## 2. M7 canonical enum 보정

### 2.1 milestone_type

```text
analysis_report
execution_manual
tracking_sheet
portfolio_row
decision_card
public_demo_row
```

### 2.2 correction_method

```text
peak_ratio
time_weighted
exclude_long_stream_days
raw_equals_corrected
not_applicable
```

### 2.3 identity_fit

```text
fit
partial
misfit
unknown
```

### 2.4 interpretation_status

```text
active_claim
revised_claim
killed_claim
open_claim
monitoring_claim
```

---

## 3. CaseResult canonical patch

M7의 `CaseResult`는 최소한 다음 필드를 포함해야 한다.

```json
{
  "case_id": "string",
  "methodology_version": "string",
  "case_type": "private_validation_case|client_deliverable_case|portfolio_pilot_case|public_demo_case|research_reference_case",
  "data_depth": "public_only|creator_shared|mcn_internal|mixed",
  "subject": {
    "streamer_key": "string",
    "platform_channel_id": "string|null",
    "public_alias": "string|null"
  },
  "milestone_status": {
    "analysis_milestone": false,
    "analysis_close": false,
    "execution_manual_included": false,
    "tracking_sheet_included": false,
    "execution_close": false
  },
  "deliverable_milestones": [],
  "identity_summary": {},
  "measurement_corrections": [],
  "cohort": {},
  "claims": [],
  "strategic_targets": [],
  "content_funnel_analysis": [],
  "recommendations": [],
  "limitations": [],
  "open_analysis_tasks": [],
  "external_validation": [],
  "evidence_refs": [],
  "absence_refs": [],
  "disclosure": {},
  "bridge_readiness": {}
}
```

---

## 4. PortfolioRow 변환 시 주의

김달수 리포트는 풍부한 클라이언트 리포트다. 이를 `PortfolioRow`로 변환하면 다음 정보가 쉽게 소실된다.

| 소실 위험 | 보존 방식 |
|---|---|
| 측정 보정의 이유 | `portfolio_derivation_refs[]`에 correction refs 연결 |
| 정밀 수치의 안전 해석 | `precision_guardrail` 연결 |
| 미해결 과제 | `absence_flags`와 별도로 `open_analysis_tasks_refs[]` 연결 |
| 목표 band와 경보선 | `strategic_targets_refs[]` 연결 |
| 콘텐츠 도달/전환 분리 | `content_funnel_refs[]` 연결 |

따라서 `PortfolioRow`에는 다음 필드를 추가한다.

```json
{
  "portfolio_derivation_refs": [],
  "strategic_targets_refs": [],
  "measurement_correction_refs": [],
  "open_analysis_tasks_refs": []
}
```

---

## 5. M7 우선순위

### Critical

1. `measurement_corrections[]` 추가
2. `CaseResult` canonical schema 단일화
3. `synthesis_status`와 `interpretation_status` enum 정리

### High

4. `deliverable_milestones[]` 추가
5. `cohort.robustness_tests[]` 추가
6. `milestone_status` 추가
7. `limitations[]` / `open_analysis_tasks[]` 추가
8. `disclosure.public_demo_blockers[]` 추가

### Medium

9. `strategic_targets[]` 추가
10. `content_funnel_analysis[]` 추가
11. `recommendations[]`에 priority/tracking basis 추가
12. `external_validation[]` 추가

---

## 6. 구비바로 돌아가기 전 조건

김달수 calibration 결과상, M7을 완료하지 않고 구비바 migration을 진행하면 다음 손실이 발생할 수 있다.

- 구비바의 §3 “노방종 0일 통과”가 measurement correction object에 남지 않음.
- 구비바의 §4 주/보조 코호트 강건성 검증이 cohort object에 충분히 남지 않음.
- O13 통합 구조가 claim status와 client reaction status로 분리되지 않음.
- O17 쇼츠 실험이 strategic target인지 execution tracking인지 불명확해짐.

따라서 순서는 유지한다.

```text
M6.5 김달수 calibration
→ M7 schema stabilization
→ QA Round 2
→ 구비바 project.json v3 migration
```
