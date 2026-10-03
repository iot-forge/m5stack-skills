# B26 · Move the hardware-session steps into checks.json

Status: done
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

- [x] `BOARD_STEPS` and `DEPENDS` are gone from `verify.py`; the steps and dependencies live in `checks.json`
- [x] The existing `Board` tests pass unchanged
- [x] A new test runs `run --board` for a revision made up in a copy of `checks.json`, and shows its steps and blocking work
- [x] `run --board` refuses a revision whose checks have no step
- [x] `uv run scripts/validate.py` exits 0
- [x] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all. Recorded results:
  - `BOARD_STEPS`, `ANY_TIME` and `DEPENDS` are gone from `scripts/verify.py`. `checks.json` has a top-level `board_steps` (`id`, `text`: plug-in, erase, arduino, platformio, esp-idf, esp-bsp-display, live-handoff, uiflow2, any-time), and each Core2 v1.3 check has a `step` and, where it had one, a `depends_on` (a full check id). They were derived by a script from the old constants, so the mapping is the same. `run_board` takes `root=` and replaces `<revision>` in the step text.
  - Within a step, checks are asked in `checks.json` order. To keep step 3 asking `open-question.auto-download` and `open-question.lcd-driver` before the facts, those two entries moved to just before `fact.pmic`. No id or `covers` changed. The `checks.json` note says this.
  - A step is shown when the revision has a check in it, or when no check names it (the erase). `run --board` refuses a revision with a check whose `step` is missing or not in `board_steps`, naming each one. The cores3, cores3-se and cores3-lite open-question checks carry no step, so `run --board` now refuses those revisions instead of putting them all in "any time".
  - Same Core2 run: the old and new `run_board` give byte-identical prompts (all pass, plus failures at host.port, host.bridge, flash.arduino, device.arduino and flash.uiflow2, checked by the spec reviewer). The stderr is identical except that `<revision>` is now filled in. `test_the_core2_run_asks_in_this_order_and_blocks_on_these` (commit 82cb6bd, green before the change) pins the full order and block map. The existing `Board` tests are unchanged.
  - New tests: `MadeUpBoard` (a made-up revision in a copy of `checks.json`: step order, shown steps, transitive blocking, refusal for a missing or unknown step) and `PlantedChecks` in `test_validate.py`. `validate.py` now fails `verification.checks` when a `step` is not in `board_steps`, when a `depends_on` is not an earlier check of the same revision, or when a `depends_on` sits on a check with no step. It does not require a `step`, so the cores3 checks pass.
  - `VERIFICATION.md` sections 3 and 6 say the steps live in `checks.json`. `uv run scripts/validate.py`: 0 failures. `python -m unittest discover tests`: 139 OK (1 skipped).
  - Reviewed with `/code-review` (standards and spec). Applied: refuse an unknown step, not only a missing one; `ask_order`/`in_step`/`steps_in_use` names; cross-reference comments between `run_board` and validate.py; "session" changed to "run" in the new text (CONTEXT.md); `tearDown` and no named lambda in the new tests. Not applied: merging `MadeUpBoard.board` with `Board.board`, because the two differ in root and stderr and stay readable apart.
- **Next**: none
- **Files touched**: `scripts/verify.py`, `scripts/validate.py`, `verification/checks.json`, `VERIFICATION.md`, `tests/test_verify.py`, `tests/test_validate.py`
- **Last commit**: see `git log -- backlog/B26-board-steps-in-checks-json.md`
- **Open questions**: none
