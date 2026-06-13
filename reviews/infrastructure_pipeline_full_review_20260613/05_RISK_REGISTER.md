# 05 Risk Register

| ID | Priority | Category | Risk | Evidence | Recommended Fix |
|---|---|---|---|---|---|
| R01 | P0 | storage | Windows path length breaks Pearson storage in realistic nested review/run roots | Pearson failed at 260-char `normalized_items.csv`; same input passed under short `_tmp` root | define short storage root; shorten Pearson target keys; add path-length guard test |
| R02 | P0 | security/filesystem | Chrome profile is copied inside run inputs and dominates scan surface | `local_chrome_profiles` = 614 files / 141.43 MB; recursive search read browser internal state | move profiles outside runs; store only local reference summaries; add scan/package exclusion policy |
| R03 | P1 | schema | working context status enums drift from M7.1 canonical status values | `stub/archived/none/ready/review_required` vs `not_ready/portfolio_ready/public_demo_ready/blocked` | patch generic protocol or add explicit transition map |
| R04 | P1 | pipeline | Pearson/Susan to case-package patch-candidate handoff is not first-class | StorageReceipt/QAReport exist; package mutation remains manual | define patch candidate schemas and one no-mutation handoff smoke |
| R05 | P1 | tooling | `pytest` absent in current runtime despite many tests | `python -m pytest` fails; direct scripts pass | document direct-test policy or pin dev env with pytest |
| R06 | P1 | filesystem | no repo-root `.gitignore` or git repo detected at workspace root | `git status` says not a repo; root `.gitignore` absent | define repo boundary and ignore/exclude rules for runtime/profile/raw artifacts |
| R07 | P1 | data_collection | Softcon inspect/collect parity unresolved | inspect can reach visible/profile-cleared state; collect smoke stopped at checkpoint | run only synthetic/transport parity harness before next live retry |
| R08 | P1 | workflow | review/search commands can accidentally traverse raw/profile artifacts | broad `rg` hit profile internals and rendered anti-bot HTML | add source-map-only search policy and exclude globs |
| R09 | P2 | case_package | case package helper docs are uneven | KimDalsu has `machine/README.md`; Gubiba does not | add lightweight per-folder READMEs where useful |
| R10 | P2 | productization | only one bounded fresh evidence candidate exists after recollect flow | CHZZK profile candidate passed; follower/rank/cohort/public crosscheck incomplete | repeat inspect-level gates on low-risk public targets |
| R11 | P2 | storage | `_inbox` dominates IsaacInfra size and scan surface | `_inbox` = 3,534 files / 230.11 MB | cold archive or stronger lookup-only convention |
| R12 | P2 | runtime | hardware/storage facts are partially unknown | CIM denied; physical disk/RAM/GPU unknown | document operator hardware inventory outside sandbox |
| R13 | P3 | productization | ND and BEARING are not implemented | specs/architecture mention future roles only | keep as future layer; do not block human-operated MVP |
| R14 | P3 | database | premature DB adoption could obscure artifact contracts | build queue says file contract must stabilize before PostgreSQL | defer DuckDB/SQLite/PostgreSQL until file-backed gates pass |

