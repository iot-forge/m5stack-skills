# B15 · Finish verify.py and checks.json

Status: open
Blocked by: [B14](B14-smoke-program.md), [B19](B19-align-verification-with-b01.md)
Gate: hardware-ready

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

Finish `scripts/verify.py` (only `run --offline` works; the rest exit 5) and complete `verification/checks.json`:

- `run --offline`: add `build.*`, and `trigger.*` through the headless command (VERIFICATION.md section 4, with `--allowedTools Skill`). Keep `handoff.*` operator-read.
- `run --board <revision>`: walk the operator through section 6's steps in order, record every observation, and mark the dependants of a failure `blocked`.
- `ingest`: apply section 8's rules exactly: hardware-test sources, `last_verified`, `confidence: high`, and each skill's `metadata.verification` and `tested-with`. A failure never edits `data/` (ADR 0004), and neither does an `open-question` result. An `open-question` check counts toward a skill's status once its result is `observed`, since it never passes (section 10).
- `report`: write `<date>.md` with section 8's five report sections.
- `checks.json`: every check in VERIFICATION.md with its kind, skills, revision and the data entries it covers (ingest relies on `covers`).

Test ingest against a fixture run file on a copy of `data/`, the way `tests/test_validate.py` does.

## Inputs

- `VERIFICATION.md` sections 4, 6, 8, 9 and 10
- `docs/adr/0004-hardware-results-write-data-refresh-does-not.md`
- `verification/results.schema.json`
- `scripts/verify.py` as it is

## Definition of done

- [ ] No `verify.py` command exits 5
- [ ] `checks.json` lists every check in VERIFICATION.md
- [ ] An ingest test on fixture results passes: pass results write sources, failures and `observed` results write nothing, and a skill whose only unpassed checks are `observed` open questions gets a `partial` or `verified` status
- [ ] `uv run scripts/verify.py run --offline` passes (the hardware-ready gate)
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Write the ingest test fixture first, then ingest
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
