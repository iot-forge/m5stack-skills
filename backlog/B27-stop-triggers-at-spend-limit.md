# B27 · Stop the trigger rows at the first account-limit message

Status: open
Blocked by: none
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

Each `trigger.*` check runs `claude -p` 3 times, and there are 21 rows. When the account hits its spend or usage limit, every later call answers "You've hit your monthly spend limit … resets <time>" and exits 1. `verify.py` records each of those runs `blocked`, which is right, but it keeps calling `claude` for every remaining row. On 2026-09-27 and 2026-09-28 that happened three times (at rows 07, 11 and 16), and each run went on to its end making calls that could not succeed.

Change `run --offline` so that:

- The first `claude -p` run whose result is an account-limit message marks its row `blocked`, with that message in the output.
- Every trigger row after it is recorded `blocked` without calling `claude`, with an output saying the account limit stopped the run.
- The command's summary on stderr says the limit stopped the trigger rows, gives the reset time from the message, and prints the `--only` options that rerun exactly the rows left.
- Rows that finished before the limit keep their results. The data, query and build checks are unaffected.

Detect the limit from the run's own output (the `result` event's text, together with a non-zero exit), not from a timer or a count of calls.

## Inputs

- `scripts/verify.py`: `trigger_result`, `run_offline`, `main`
- `tests/test_verify.py`: the `Triggers` tests and `FakeRunner`
- The message as `claude -p` gave it on 2026-09-28, as the `result` event's text with exit code 1: "You've hit your monthly spend limit · raise it at claude.ai/settings/usage?from=cc_cli_limit_message · your session limit resets 2:10pm (America/Los_Angeles)"
- [`B15-verify-py-and-checks.md`](B15-verify-py-and-checks.md), Checkpoint open question 7

## Definition of done

- [ ] A test with a fake `claude` that hits the limit on some row shows that row `blocked` with the message, every later row `blocked` with no further `claude` call, and every earlier row keeping its result
- [ ] The stderr summary gives the reset time and the `--only` options for the rows left
- [ ] A test shows an ordinary `claude` failure (non-zero exit, no limit message) still blocks only its own row
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Write the failing test with a fake `claude` that hits the limit on the third row
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
