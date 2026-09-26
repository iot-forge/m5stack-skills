---
status: accepted
date: 2026-09-24
---

# A passing hardware result writes into `data/`; refresh never does

[ADR 0003](0003-shared-pinmap-and-soc-records.md) says refresh compares upstream sources with `data/` and never edits it: a scraped value must not overwrite a verified one, so a person reads a drift report and edits by hand. Hardware verification goes the opposite way. `scripts/verify.py ingest` reads a run's results file and, for each **passing** hardware check, adds a `hardware-test` source to the entries that check covers, sets `last_verified` to the run date and `confidence` to `high`. It also rewrites each skill's `metadata.verification` and `metadata.tested-with`. The person reviews the git diff and commits it. A **failing** check never edits `data/`; it is written into the run report's Failures section for someone to diagnose.

The asymmetry follows from where the evidence comes from. Refresh brings in claims from outside, which may be wrong or stale. A hardware pass is the most trusted evidence the data can have: a direct chip read on a named unit, by a person following a written plan. A failure is different. It could be the data, the skill, the toolchain, a flaky cable or a faulty unit, and only a diagnosis can say which.

## Considered options

- **Ingest writes a report, and a person edits `data/` by hand**, the same as refresh. Rejected: the run is done once, offline, by one person, and hand-copying a source id onto every covered entry is exactly the tedious, error-prone step that makes provenance drift.
- **Hand-editing with no script.** Rejected for the same reason, and because nothing would check that the results and the data agree.
- **Ingest also writes on failure**, recording a contradicted fact. Rejected: it would let an undiagnosed failure, possibly a bad cable, overwrite a sourced fact.

## Consequences

- `verify.py ingest` is the only script allowed to write `data/`, and it only adds sources and raises confidence. It never changes a fact's value. A value found to be wrong on hardware changes only through a person's edit after the failure is diagnosed.
- Each check in `verification/checks.json` lists the data entries it covers, so ingest knows which entries to cite the new source on.
- The git diff is the review step. Ingest never commits.
