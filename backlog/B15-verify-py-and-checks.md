# B15 · Finish verify.py and checks.json

Status: done
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

- [x] No `verify.py` command exits 5
- [x] `checks.json` lists every check in VERIFICATION.md
- [x] An ingest test on fixture results passes: pass results write sources, failures and `observed` results write nothing, and a skill whose only unpassed checks are `observed` open questions gets a `partial` or `verified` status
- [x] `run --offline` reports no `data.planted-*` result for the two fixture-guard tests, and a failing guard makes every `data.planted-*` result `blocked`
- [x] `uv run scripts/verify.py run --offline` passes (the hardware-ready gate)
- [x] `uv run scripts/validate.py` exits 0
- [x] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all. Tests: tests/test_verify.py (Ingest, Offline, Triggers, Board, WriteRun, Report, ChecksJson; 60 tests), 3 new planted fixtures in tests/test_validate.py; `python -m unittest discover tests` 107 pass; `uv run scripts/validate.py` exits 0. The gate: verification/runs/2026-09-28.json and .md, 0 fail: data 17, query 8, build 5, trigger 21 pass; handoff.<skill> 4 blocked (section 4: until a port that exists but fails; handoff.live covers it). The run is two sittings merged by --write, because the account's spend limit cut claude -p off three times: `run --offline` at 2e9902f (2026-09-28 09:13-09:51) for data, query, build and trigger rows 01-15, then `run --offline --only` at 81972f9 for rows 16-18 and neg-01 to neg-03 (17:11-17:20). trigger.row-11 was judged pass by the maintainer from its three saved answers.
- **Next**: none. B17 (where and when the checks run) is unblocked.
- **Files touched**: scripts/verify.py, tests/test_verify.py, tests/test_validate.py, verification/checks.json, verification/triggers/, verification/runs/2026-09-28.json and .md, VERIFICATION.md, CONTRIBUTING.md
- **Last commit**: the B15 close commit (git log)
- **Open questions** (for the maintainer): (1) ingest leaves a skill's metadata unchanged when any of its checks is unsatisfied, and unions the revisions it already listed; (2) `SKILL_TOOLS` in verify.py decides which toolchains each skill's `tested-with` lists, with claude-code on every skill; (3) negative trigger rows count toward all seven skills' status; (4) a `covers` item naming a list (`extra_components`) cites every element; (5) section 4's headless command allows only the Skill tool, so a skill cannot run `board.py` there: two of row-11's three answers say so. The trigger verdict only reads which skill fires, but row-11's operator judgment reads answers the skill could not ground in data. Allow `Bash(uv run *board.py*)` in the command? (6) `run --board`'s step list and dependencies (BOARD_STEPS, DEPENDS) live in verify.py and are Core2-specific; a second revision's session would need them in checks.json. (7) A spend limit makes every later claude -p call exit 1 (recorded blocked); `run --offline` could stop the trigger rows at the first limit message instead of spending the rest.
