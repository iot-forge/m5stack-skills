# B26 · Move the hardware-session steps into checks.json

Status: in-progress
Blocked by: none
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

`verify.py run --board` walks the operator through `VERIFICATION.md` section 6. B15 wrote the steps and their dependencies as two constants in `scripts/verify.py`, `BOARD_STEPS` and `DEPENDS`, and both are written for Core2 v1.3. Section 3 says any owned unit can run section 6. For another revision, though, `run --board` would put every check in its "any time" step with no dependencies. A check that should wait on a failed upload would then be asked, not marked `blocked`.

Move both into `verification/checks.json`, so a revision's hardware session is data like its checks:

- Each hardware check gets the section 6 step it belongs to and the check it depends on (`depends_on`, a check id). `run --board` reads them from `checks.json`, keeps the step order and blocks a dependant exactly as it does now.
- The step text (what the operator does at each step) moves too. Give it one home in `checks.json`, and keep it free of Core2-specific wording where the step itself is general.
- A revision whose checks carry no step makes `run --board` refuse, naming what is missing. It no longer lumps them all into "any time".
- Change no check id, and no `covers`. The Core2 v1.3 session asks the same questions in the same order, and blocks the same checks, as it does today.

## Inputs

- `VERIFICATION.md` sections 3 and 6
- `scripts/verify.py`: `BOARD_STEPS`, `DEPENDS`, `run_board`
- `tests/test_verify.py`: the `Board` tests, which pin today's behaviour
- [`B15-verify-py-and-checks.md`](B15-verify-py-and-checks.md), Checkpoint open question 6

## Definition of done

- [ ] `BOARD_STEPS` and `DEPENDS` are gone from `verify.py`; the steps and dependencies live in `checks.json`
- [ ] The existing `Board` tests pass unchanged
- [ ] A new test runs `run --board` for a revision made up in a copy of `checks.json`, and shows its steps and blocking work
- [ ] `run --board` refuses a revision whose checks have no step
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Decide the `checks.json` shape for a step and its text, then write the made-up-revision test
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
