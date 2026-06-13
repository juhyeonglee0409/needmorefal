# CHZZK Subject Profile API Direct Collect Shape Patch Review - 2026-06-12

Scope: Scenario 3 offline/mock collect-shape fix only. No live web access, no Charles run, no Arthur inspect, no Arthur collect, no CollectionResult creation, and no `approved=true` directive creation.

## Inputs

- Current draft: `40_arthur_collect/directives/chzzk_subject_profile_api_body_collect_directive.draft_approved_false_20260612.json`
- Prior draft review: `20_review/chzzk_subject_profile_api_body_collect_directive_draft_review_20260612.md`
- InspectResult reference: `30_arthur_inspect/chzzk_subject_profile_api_body_rescout_api_direct_20260612.InspectResult.json`
- Protocol reference: `10_charles/chzzk_subject_profile_api_body_rescout_20260612.protocol.json`

## Current State

- Current draft approval status: `approved=false`.
- Current draft collect approval: `no`.
- CHZZK CollectionResult status: not present. The proposed result path `40_arthur_collect/results/chzzk_subject_profile_api_body_collect_20260612.CollectionResult.json` does not exist.
- Existing scalar `json_path_hints`:
  - `$.content.channelId`
  - `$.content.channelName`
  - `$.content.channelDescription`
  - `$.content.followerCount`
  - `$.content.channelImageUrl`
  - `$.content.openLive`

## Offline Reproduction

Synthetic payload:

```json
{
  "content": {
    "channelId": "dcbccbf2d8e2a1b095244c5856d3613a",
    "channelName": "김달수 Dalsu",
    "channelDescription": "synthetic description",
    "followerCount": 3755,
    "channelImageUrl": "https://example.invalid/channel.png",
    "openLive": false
  }
}
```

Observed with current scalar hints:

- Arthur `collect_api` selects the first matching hint: `$.content.channelId`.
- The raw row shape is value-only: `raw_keys_seen={"value"}`.
- The projected row has all requested fields as `null` because the row is scalar before projection.
- This confirms the scalar-only row risk before any approved collect.

Observed with record root `$.content`:

- Arthur `collect_api` selects `$.content`.
- One object row is collected.
- Row fields are populated: `channelId`, `channelName`, `channelDescription`, `followerCount`, `channelImageUrl`, `openLive`.
- No `{"value": ...}` raw row is produced.

## Root Cause

Arthur `collect_api._rows_from_payload()` tries `Prescription.json_path_hints` in order and returns rows from the first matching hint. `extract.jsonpath_collect()` wraps a non-wildcard scalar match as a one-item list, and `project_fields()` treats non-dict rows as `{"value": row}` before projection. Therefore scalar field paths in `json_path_hints` are row candidates, not field-only hints.

## Patch Recommendation

Smallest safe fix for this CHZZK profile API directive:

- Use `source_protocol.collection_plan.json_path_hints = ["$.content"]` as the collector row/root path.
- Preserve scalar field paths as secondary metadata under `source_protocol.collection_plan.field_json_path_hints`.
- Add `source_protocol.collection_plan.record_root_json_path = "$.content"` for review clarity.
- Keep `approved=false`; do not create `approved=true` until the operator explicitly approves the exact revised scope.

Created revised draft:

- `40_arthur_collect/directives/chzzk_subject_profile_api_body_collect_directive.draft_approved_false_record_root_20260612.json`
- Approval status: `approved=false`
- Collect approval: `no`

Future upstream recommendation:

- Charles should emit the object/container record root for singleton JSON profile endpoints such as CHZZK `content`.
- Arthur may later distinguish `record_root_json_path` from field-level JSON path hints, but this is not required for the current approved-false revised draft because the collector already honors `json_path_hints=["$.content"]`.

## Tests

Ran offline tests only:

- `tests/test_collect_api_v0_1.py`: `16 PASS / 0 FAIL`
- `tests/test_protocol_loader_v0_1.py`: `46 PASS / 0 FAIL`

Added coverage:

- CHZZK synthetic scalar hints reproduce value-only raw row risk.
- CHZZK synthetic `$.content` record root collects one object row.
- Collected row has `channelId`, `channelName`, `channelDescription`, `followerCount`, `channelImageUrl`, `openLive`.
- No scalar-only `value` row is produced for the revised shape.
- Loader parses the revised `approved=false` draft and preserves `json_path_hints=["$.content"]`.

## Boundary

- Live web access: no.
- Arthur live collect: no.
- Arthur inspect: no.
- Charles run: no.
- CollectionResult created: no.
- `approved=true` directive created: no.
- CaseResult, DisclosureLog, PublicDemoRow, package canonical data mutated: no.
- Raw JSON body, raw HTML, screenshots, token/cookie/auth values stored: no.

## Verdict

PASS. Offline mock proves object row extraction from `$.content`, and the revised approved-false draft is safe for later operator review.

Smallest next action: operator reviews the revised approved-false draft and this patch review. Do not set `approved=true` or run Arthur collect unless the operator explicitly approves the exact revised directive, URL scope, fields, output path, and limits.
