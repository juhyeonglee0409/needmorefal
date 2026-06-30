# Intent Alignment Checklist

Use this checklist after Charles protocol extraction and Arthur inspect, before any CollectDirective is approved.

## Required Gate

Arthur collect remains blocked unless every applicable item below is reviewed against `00_inputs/research_plan.md` and `00_inputs/target_batch_plan.draft.json`.

## Checklist

- InspectResult source matches the intended target id and source domain.
- InspectResult best path is executable and not `manual_review`.
- `pre_check.gate_status` is not restricted, not_attempted, or phase2_error unless operator explicitly approves review.
- `login_required` or `profile_required` targets have only profile summaries recorded; no secret values are stored.
- Target URL resolved by Charles still fits the approved scope and allowed domains.
- Required fields in TargetBatchPlan are plausibly collectible from the inspected protocol.
- Missing required fields are recorded as field coverage gaps, not silently inferred from legacy data.
- Subject identity checks match expected channel id/hash or name constraints where applicable.
- Cohort collection target returns the intended LoL/MOBA population, not a broad unrelated ranking.
- Follower ranking targets can produce channel URL/hash or a documented absence.
- Public cross-check targets are treated as corroboration only, not replacement for profile-gated data.
- YouTube content funnel data is treated as weak/contextual and not causal proof.
- `not_verifiable` is preserved if verification criteria are unavailable.
- absences preserve Arthur provenance values such as `charles_not_found`, `arthur_collection_failed`, `target_absent`, or `undetermined`.
- `boundary_signals`, `protocol_hash`, `directive_hash`, raw artifact paths, and source paths are preserved.
- No CaseResult, DisclosureLog, PublicDemoRow, or package canonical file is mutated from inspect output.
- Any CollectDirective drafted after this review has `approved=false` until explicit operator approval.

## Stop Conditions

Stop and return to operator review if:

- InspectResult target identity does not match the ResearchPlan intent.
- Required fields cannot be collected and the gap changes the research question.
- A target-specific bypass, private/internal source, or secret-bearing workflow is required.
- The approved scope must expand beyond the draft TargetBatchPlan.
- Disclosure boundary shifts toward public/external use.
