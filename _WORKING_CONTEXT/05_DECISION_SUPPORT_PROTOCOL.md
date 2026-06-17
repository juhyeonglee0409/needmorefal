# Decision Support Protocol

This file defines how the session (any surface: Codex, Claude Code, Cowork) should help because the implemented Pearson/Susan are not yet wired to canonical mutation, and ND/BEARING remain unimplemented; final judgment, disclosure, promotion, and collection approval stay with the operator.

Canonical escalation fence for delegated Code-to-Codex work orders:
`D:\Codex_Workspace\Instruction\delegation\DELEGATION_FENCE_v0_1.md`.
On delegation-specific conflicts, preserve this file's judgment boundaries and stop for operator approval.

## Role

The session may act as temporary judgment support, not final judgment authority.

Use these labels:

```text
operator_recommendation
decision_note
review_note
patch_candidate
remaining_risk
needs_user_approval
```

Avoid these labels unless the user explicitly approves:

```text
final_decision
CaseResult ready
public_demo_allowed
absence_confirmed
verified_success
```

## Judgment Areas Requiring User Approval

- CaseResult `partial -> ready`
- PortfolioRow readiness
- PublicDemoRow creation
- disclosure tag finalization or downgrade from red
- CollectDirective `approved=true`
- treating `undetermined` as true absence
- treating `not_verifiable` data as sufficient for a claim
- publishing or external sharing

## How To Write Recommendations

Every recommendation should include:

```text
recommendation:
evidence:
source_paths:
assumptions:
risks:
approval_needed:
```

## Special Handling

### not_verifiable

Meaning: verification criterion is missing or input is thin. It is not equivalent to failure.

Allowed statement:

```text
The collection can be retained as evidence with data_quality=not_verifiable.
```

Not allowed without approval:

```text
The collection proves the claim.
```

### Absence

Arthur absence sources are provenance, not final meaning:

```text
charles_not_found
arthur_collection_failed
target_absent
undetermined
```

Susan/ND would decide final absence meaning later. Until then, keep as patch candidates.

### Disclosure

Default to red for real client cases.

Use yellow only for reviewed anonymized candidates. External sharing still needs a new disclosure review.

### Reference Cases

Reference-case baselines belong in dedicated reference files, not in this generic decision protocol.

For KimDalsu-specific baseline, read:

```text
08_REFERENCE_CASE_KIMDALSU.md
```

For another streamer, derive the baseline from that streamer's own package README, dossier, machine objects, and disclosure log.
