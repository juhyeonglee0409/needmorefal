# Legacy relocation note — 김달수

기존 1차 마일스톤 리포트는 이번 TargetBatchPlan에서 정본 분석 입력이 아니라 `legacy reference`로 처리한다.

## 이동 위치
- `legacy/previous_milestone_report/김달수_채널분석_컨설팅리포트_LEGACY_20260601.md`

## 사용 가능
- 스키마 gap 확인
- baseline 판단과 새 수집 결과 비교
- 클라이언트 전달문 구조 참조

## 사용 금지
- 새 CaseResult의 fresh evidence로 직접 사용
- 새 PortfolioRow 점수의 직접 근거로 사용
- PublicDemoRow 직접 공개본으로 사용

새 run의 판단 근거는 Charles/Arthur 수집 산출물과 수동 분석 결과에서 만들어야 한다.

---

## 2026-06-16 Data Cleanup

The following duplicate files were removed from this TargetBatchPlan package because identical copies exist in the canonical case package:

### Removed: legacy/baseline_data/ (5 files → 김달수_CASE_PACKAGE_v3_20260611/data/)
- 김달수_Dalsu_방송통계_1년_20260528.csv → data/daily_stats/
- 김달수_코호트_131명.csv → data/cohort/
- 김달수_코호트_분석_방법과결과.md → data/cohort/
- 수집대상_183명.csv → data/cohort/
- 스크래핑_작업명세서_구현팀.md → data/cohort/specs/

### Removed: legacy/previous_milestone_report/ (1 file → 김달수_CASE_PACKAGE_v3_20260611/deliverables/)
- 김달수_채널분석_컨설팅리포트_LEGACY_20260601.md → deliverables/milestone_report/김달수_채널분석_컨설팅리포트.md

### Removed: references/ (4 files → 김달수_CASE_PACKAGE_v3_20260611/references/current_framework/)
- MASTER_streamer_mcn_framework_v2_draft_M7_1_QA2_patched_20260610.md
- MASTER_v2_M7_1_canonical_enum_table_20260610.csv
- MASTER_v2_M7_1_canonical_schema_pack_20260610.json
- 스트리머_채널진단_방법론_v3_draft_START_20260610.md

### Removed: .zip
- KimDalsu_TargetBatchPlan_MASTER_v2_M7_1_20260611.zip (unzipped version already present)

### Removed from CASE_PACKAGE: machine/schema/ (3 files → references/current_framework/)
- MASTER_v2_M7_1_canonical_enum_table_20260610.csv
- MASTER_v2_M7_1_canonical_schema_pack_20260610.json
- MASTER_v2_M7_1_disclosure_boundary_matrix_20260610.csv

All removals were SHA-256 verified identical before deletion. Canonical copies remain in 김달수_CASE_PACKAGE_v3_20260611/.
