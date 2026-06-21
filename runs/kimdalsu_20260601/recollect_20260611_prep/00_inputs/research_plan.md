# KimDalsu Recollection ResearchPlan Draft

## Metadata

- case_id: `kimdalsu_20260601`
- run_id: `recollect_20260611_prep`
- status: `draft`
- created_at: `2026-06-11T18:33:35+09:00`
- scenario: `Scenario 3 - Charles/Arthur collection preparation`
- collect_status: `not_requested`
- approval_status: `operator_review_required_before_collect`

## Boundary

This plan separates prior KimDalsu outputs from new evidence.

Legacy materials are fixed as baseline/reference only. They may be used to define comparison questions, expected identity checks, and calibration notes, but they must not be treated as fresh evidence for a new CaseResult, PortfolioRow, or PublicDemoRow.

No CaseResult promotion, disclosure downgrade, PublicDemoRow creation, or CollectDirective approval is included in this draft.

## Legacy Reference Lock

Treat these as legacy/reference, not fresh evidence:

- `김달수_케이스/deliverables/milestone_report/김달수_채널분석_컨설팅리포트.md`
- `KimDalsu_TargetBatchPlan_MASTER_v2_M7_1_20260611/legacy/previous_milestone_report/김달수_채널분석_컨설팅리포트_LEGACY_20260601.md`
- `김달수_케이스/machine/김달수_CaseResult_v3_partial_20260611.json`
- `김달수_케이스/machine/김달수_EvidencePackage_v3_initial.json`
- `김달수_케이스/machine/김달수_AbsenceInventory_v3_initial.json`
- `김달수_케이스/machine/김달수_DisclosureLog_v3_initial.json`
- `김달수_케이스/machine/김달수_PortfolioRow_v3_partial_20260611.json`
- `김달수_케이스/machine/김달수_DecisionCard_v3_partial_20260611.json`
- `김달수_케이스/source_inputs/legacy_project/김달수_project_original.json`
- `김달수_케이스/source_inputs/current_analysis/김달수_보고직후_인터뷰로그_20260601.md`
- `김달수_케이스/data/daily_stats/김달수_Dalsu_방송통계_1년_20260528.csv`
- `김달수_케이스/data/cohort/김달수_코호트_131명.csv`
- `김달수_케이스/data/cohort/수집대상_183명.csv`
- `김달수_케이스/data/cohort/김달수_코호트_분석_방법과결과.md`

## Research Intent

Prepare a new collection pass that can answer whether the current public and profile-gated data still supports the prior KimDalsu diagnosis, without reusing the prior report as proof.

Primary intent:

1. Reconfirm the subject channel identity and current channel metrics.
2. Rebuild the current CHZZK LoL/MOBA cohort population from fresh source data.
3. Match follower counts and channel URLs/hashes for cohort members.
4. Cross-check follower ranking against public sources where possible.
5. Collect public CHZZK profile signals for subject identity and recent category alignment.
6. Collect public YouTube content funnel candidates as weak supporting signals only.
7. Preserve any collection absence, boundary signal, not_verifiable status, protocol_hash, directive_hash, and source path.

## Research Questions

- RQ1: Does the current subject channel profile resolve to the intended platform channel id/hash?
- RQ2: What are the latest available subject metrics from Softcon and CHZZK public sources?
- RQ3: What is the latest available CHZZK LoL/MOBA cohort population and what filters are required?
- RQ4: Can follower counts and channel URLs/hashes be matched for the cohort with acceptable coverage?
- RQ5: Do public follower-ranking sources corroborate or conflict with the profile-gated source?
- RQ6: Are public YouTube content-funnel signals present, and are they only weak/contextual rather than causal evidence?
- RQ7: Which data gaps should become AbsenceInventory patch candidates rather than final absence judgments?

## Required Field Groups

Subject current stats:

- `run_id`, `case_id`, `streamer_key`, `platform`, `platform_channel_id`, `channel_name`, `channel_url`, `follower_count`, `stream_hours`, `peak_viewers`, `avg_viewers`, `viewership`, `max_chat_6m`, `avg_chat_6m`, `category_1`, `collected_at`, `raw_record_path`, `disclosure_tag`

Cohort population:

- `run_id`, `cohort_cell_id`, `cohort_type`, `source_name`, `source_url`, `request_url`, `platform`, `channel_id`, `channel_name`, `channel_url`, `primary_category`, `category_basis`, `aggregation_window_start`, `aggregation_window_end`, `total_stream_hours`, `peak_viewers`, `avg_viewers`, `viewership`, `follower_count`, `is_virtual`, `is_esports_team`, `is_tournament`, `is_corporate`, `exclude_reason`, `raw_record_path`, `collected_at`, `disclosure_tag`

Follower rank:

- `run_id`, `source_name`, `source_url`, `platform`, `channel_id`, `channel_name`, `channel_url`, `follower_count`, `follower_rank`, `channel_hash`, `collected_at`, `raw_record_path`, `disclosure_tag`

Subject public profile:

- `run_id`, `case_id`, `streamer_key`, `platform`, `platform_channel_id`, `channel_name`, `channel_url`, `profile_text`, `follower_count`, `recent_live_or_vod_titles`, `recent_categories`, `collected_at`, `raw_record_path`, `disclosure_tag`

External content funnel:

- `run_id`, `case_id`, `streamer_key`, `platform`, `content_id`, `content_url`, `posted_at`, `content_type`, `content_topic`, `duration_sec`, `title`, `identity_fit`, `views`, `likes`, `comments`, `shares`, `cta_present`, `main_link_present`, `conversion_signal`, `follower_delta_1d`, `follower_delta_3d`, `follower_delta_7d`, `recommendation`, `evidence_refs`, `disclosure_tag`

## Out Of Scope

- Reading the full legacy client report.
- Treating legacy CaseResult as fresh evidence.
- Collecting before Arthur InspectResult is reviewed against this ResearchPlan.
- Setting any CollectDirective to `approved=true`.
- Promoting CaseResult from `partial` to `ready`.
- Creating or approving a PublicDemoRow.
- External sharing or disclosure downgrade from `red`.

## Planned Pipeline

1. Validate `target_batch_plan.draft.json` against this ResearchPlan.
2. Run Charles scout per target and preserve full ScoutReport.
3. Extract only top-level `protocol` from each ScoutReport.
4. Run Arthur inspect on protocol-only inputs.
5. Compare InspectResult to this ResearchPlan using the intent-alignment gate.
6. If aligned, draft CollectDirective with `approved=false`.
7. Ask operator for explicit approval before any collect.
8. After any future approved collect, write patch candidates only.
