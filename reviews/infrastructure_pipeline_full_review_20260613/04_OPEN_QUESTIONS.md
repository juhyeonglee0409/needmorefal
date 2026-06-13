# 04 Open Questions

## P0 / Gate Questions

1. What is the canonical short storage root for Pearson/Susan smoke and future run storage on Windows?

Current evidence: Pearson fails when the review-package path reaches 260 characters, but succeeds under `D:\Codex_Workspace\_tmp\p_smoke`.

2. Should browser profile directories ever live under `runs/{case_id}/{run_id}/00_inputs/`?

Current evidence: KimDalsu run stores a 141.43 MB Chrome profile under `00_inputs/local_chrome_profiles`; recursive search reads browser internals and profile paths. This should likely become a referenced runtime asset outside review/package scan roots.

3. What is the exact first-class patch-candidate schema from Pearson/Susan outputs to case package objects?

Current evidence: Pearson/Susan produce StorageReceipt/QAReport, but no stable `EvidencePackagePatchCandidate`, `AbsenceInventoryPatchCandidate`, or `DisclosureLogPatchCandidate` contract exists yet.

## P1 Questions

4. Should generic working-context status enums be patched to match M7.1 exactly, or should an explicit transition map be added?

5. Should Gubiba gain a `machine/README.md` equivalent to KimDalsu for consistent first-entry routing?

6. Should local test policy switch from direct Python test scripts to a pinned dev environment with `pytest`, `ruff`, and `mypy`, or keep standalone test scripts as the primary no-install path?

7. Should `IsaacInfra\_inbox` be moved to cold archive or marked with a stronger scan-exclude convention?

## P2 / Productization Questions

8. When should DuckDB/SQLite be introduced?

Current recommendation: not before Pearson/Susan file-backed contracts survive at least two source families and one patch-candidate handoff.

9. Which product path comes first: single-streamer deep-dive repeatability, MCN portfolio pilot, or public demo/preprint?

Current recommendation: single-streamer deep-dive repeatability first; public demo remains blocked.

10. What is the durable backup layout across active SSD, external HDD, optional external SSD, and cloud?

Current evidence is insufficient to confirm physical storage and backup policy.

