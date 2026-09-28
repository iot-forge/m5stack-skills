# B15 · Finish verify.py and checks.json

Status: in-progress
Blocked by: [B14](B14-smoke-program.md), [B19](B19-align-verification-with-b01.md)
Gate: hardware-ready

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

Finish `scripts/verify.py` (only `run --offline` works; the rest exit 5) and complete `verification/checks.json`:

- `run --offline`: add `build.*`, and `trigger.*` through the headless command (VERIFICATION.md section 4, with `--allowedTools Skill`). Keep `handoff.*` operator-read.
- `run --offline`, planted results: report only the rule fixtures in `tests/test_validate.py` as `data.planted-<rule>`. Two tests there guard the fixture, not a rule: `test_committed_data_passes` (the unbroken copy validates) and `test_fixture_leaves_out_smoke` (B24: the copy leaves out `verification/smoke/`). Name them in a set in `verify.py`, the way `query_map` names the query tests, and never report them as `data.planted-*`. If either fails, every `data.planted-*` result is `blocked` (a prerequisite failed, VERIFICATION.md section 1), with the failing test's line as its output.
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
- [ ] `run --offline` reports no `data.planted-*` result for the two fixture-guard tests, and a failing guard makes every `data.planted-*` result `blocked`
- [ ] `uv run scripts/verify.py run --offline` passes (the hardware-ready gate)
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: ingest (tests.test_verify.Ingest: pass cites `hw-<date>-<revision>`, failures and `observed` write nothing, `observed`-only skill gets `partial`, handoff `satisfied_by`), run --offline planted-per-rule and fixture guards (Offline), trigger rows through `claude -p` (Triggers), run --board (Board), merge-on-write (WriteRun), report (Report), checks.json lists every check in VERIFICATION.md (ChecksJson). New planted fixtures for data.json, data.schema, data.pinmap-stub.
- **Next**: rerun the gate on the current code, in PowerShell with arduino-cli on PATH and the ESP-IDF v6.1 profile dot-sourced: `uv run scripts/verify.py run --offline`. If it passes, tick the Definition of done and close. Gate run 2026-09-27 21:24-21:45 (code at 7807776, before the review fixes): exit 1. data, query and all 16 data.planted-* pass; build.platformio.m5stack-core2 and build.target-from-data pass; the two Arduino builds and build.esp-idf.esp32 blocked (arduino-cli and idf.py not on that shell's PATH); trigger.row-01 to row-06 pass in all 3 runs; row-07 to row-18 and neg-01 to neg-03 'fail' only because every claude -p run from row-07 on hit the account's monthly spend limit and exited 1. The code at 25d949f records that as blocked, not fail.
- **Files touched**: scripts/verify.py, tests/test_verify.py, tests/test_validate.py, verification/checks.json, verification/triggers/, VERIFICATION.md
- **Last commit**: 25d949f
- **Open questions**: design calls made in this session, for the maintainer to confirm: (1) `run --write` merges into the date's results file (confirmed); (2) trigger.row-11 is operator-read (confirmed); (3) `handoff.<skill>` counts when `handoff.live.<revision>` passes (confirmed); (4) ingest leaves a skill's metadata unchanged when any of its checks is unsatisfied, and unions the revisions it already listed; (5) `SKILL_TOOLS` in verify.py decides which toolchains each skill's `tested-with` lists, with claude-code on every skill; (6) negative trigger rows count toward all seven skills' status; (7) a `covers` item naming a list (`extra_components`) cites every element.
