# 03 Current State

## Executive Snapshot

The system is a strong internal pilot framework, not a productized pipeline.

Current maturity:

- Documentation and architecture: strong
- Charles/Arthur diagnostic and execution contracts: strong
- Pearson/Susan executable smoke: partial-to-strong
- Case package discipline: partial but usable
- Productization: early
- Public demo readiness: blocked until explicit disclosure work

## Tool State

| Tool | Observed Version | Evidence |
|---|---:|---|
| Charles | 0.10.1 | `scouter --version` |
| Arthur | 0.6.1 | `python -m arthur.cli --version` |
| Pearson | 0.1.0 | `python -m pearson --version` |
| Susan | 0.1.0 | `python -m susan --version` |

Representative tests passed:

- Charles pipeline contract: 11 pass
- Arthur CLI/pipeline/profile/protocol tests: 130 pass combined
- Pearson CLI/artifact tests: 28 pass combined
- Susan CLI: 20 pass
- Pearson/Susan integration smoke: 58 pass

`pytest` is not installed in the active bundled Python, but standalone tests run directly.

## Case State

| Case | CaseResult | Portfolio | PublicDemo | Disclosure |
|---|---|---|---|---|
| KimDalsu | `partial` | `partial_ready` | absent / synthetic candidate in README | `red`, `defer` |
| Gubiba | JSON `not_ready`, README `stub` wording | `not_ready` | `blocked` | `red`, `blocked` |

Case package shape is mostly sound:

- human dossier and machine objects are separated
- `machine/`, `data/`, `deliverables/`, `source_inputs/`, `references/`, `work/`, `archive/` exist
- archive is documented as not fresh evidence

Known unevenness:

- KimDalsu has `machine/README.md`; Gubiba does not.
- README status wording sometimes uses human terms such as `stub` where M7.1 enum says `not_ready`.

## Collection / Run State

KimDalsu recollect run:

- Charles executed.
- Arthur inspect executed.
- Bounded Arthur collect executed for approved scopes.
- Operator approval is recorded in RUN_MANIFEST for approved collect copies.
- CHZZK public profile collect produced 1 item and `not_verifiable`.
- Softcon smoke collect executed but stopped at `chrome_profile_checkpoint_not_cleared`; zero items; boundary evidence only.
- No CaseResult, DisclosureLog, PublicDemoRow, or package canonical data was promoted.

## Pearson / Susan Real-Artifact Smoke

Short path:

- Pearson stored the CHZZK CollectionResult under `D:\Codex_Workspace\_tmp\p_smoke`.
- StorageReceipt preserved `verification_status=not_verifiable`, boundary count, protocol hash, directive hash, and promotion state `stored_not_promoted`.
- Susan QA produced verdict `conditional` with reason `verification_not_verifiable`.
- Susan validate returned `valid=true`.

Long review package path:

- Pearson store failed at path length 260 when writing `artifacts\normalized_items.csv`.
- Same input works in a shorter path.

Interpretation:

- Pearson/Susan logic works on the observed artifact.
- Windows path length and storage root depth are an operational blocker for reliable repeated use.

## Filesystem Scan

Top-level counts:

| Root | Files | Size |
|---|---:|---:|
| `IsaacInfra` | 4,238 | 239.66 MB |
| `Streamer Consulting Project` | 876 | 145.27 MB |
| `Instruction` | 4 | 0.08 MB |
| `_tmp` | 6 before smoke outputs | 0.08 MB before smoke outputs |

Streamer project largest areas:

| Area | Files | Size |
|---|---:|---:|
| `runs` | 729 | 142.88 MB |
| `00_inputs/local_chrome_profiles` inside KimDalsu run | 614 | 141.43 MB |
| Gubiba package | 47 | 0.91 MB |
| KimDalsu package | 54 | 0.87 MB |
| TargetBatchPlan package | 27 | 0.36 MB |
| `_WORKING_CONTEXT` | 16 | 0.10 MB |

IsaacInfra largest area:

| Area | Files | Size |
|---|---:|---:|
| `_inbox` | 3,534 | 230.11 MB |
| `Charles` | 541 | 6.26 MB |
| `Arthur` | 96 | 3.07 MB |

Key finding:

The context layer is small, but runtime/profile/archive areas dominate scans and can pollute broad `rg`/review operations.

## Runtime State

Observed locally:

- OS: Microsoft Windows NT 10.0.26200.0
- 64-bit OS: true
- logical processor count: 12
- PowerShell: 5.1
- Python: 3.12.13 from Codex runtime
- pip: 26.0.1
- `rg` available
- `git` available, but `D:\Codex_Workspace` is not currently a git repository
- `node`, `npm`, `uv`, `jq` were not found on PATH in this shell

Hardware details such as RAM, physical disk type, and GPU were not available because CIM queries were denied in the sandbox.

