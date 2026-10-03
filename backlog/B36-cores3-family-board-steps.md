# B36 · Give a CoreS3-family revision its hardware run once a unit is at hand

Status: open
Blocked by: a CoreS3, CoreS3 SE or CoreS3 Lite unit to run on (external; see step 1)
Gate: none

## Before you start

1. Ask the maintainer which CoreS3-family unit is at hand and its revision (`board-identification` settles it if the sticker doesn't). If none is, stop here, without claiming.
2. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
3. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
4. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

Since B26, `verify.py run --board <revision>` reads the run's steps from `verification/checks.json`: `board_steps`, and each check's `step` and `depends_on`. It refuses a revision with a check that has no step. The CoreS3-family revisions have only open-question checks, and none has a step:

- `open-question.manual-download.cores3@v1.0`
- `open-question.manual-download.cores3-se@v1.0`
- `open-question.mpremote.cores3-se@v1.0`
- `open-question.lite-image.cores3-lite@v1.0`
- `open-question.ghost-touch.cores3-se@v1.0`

So today `run --board cores3@v1.0`, `cores3-se@v1.0` and `cores3-lite@v1.0` refuse, naming these checks. That is correct while nobody owns such a unit. For the unit at hand, make its run work:

- Derive its `host`, `flash`, `device` and `fact` checks from `data/`, as `VERIFICATION.md` section 3 says: every component its revision lists, checked the same way as Core2 v1.3's. Each new check id ends in `.<revision>`, and each `fact` check names the revisions it rejects, as section 6's `fact` bullets do (B25). Add them to `checks.json` with `covers` where a pass cites data.
- Give every check of that revision a `step` and, where it needs an earlier check to pass, a `depends_on`, the way the Core2 v1.3 checks have them. Reuse the existing `board_steps` where the step is the same. Where a CoreS3-family unit needs a step Core2 does not, such as M5's manual download mode (hold RESET about 3 s until the green LED), add a step whose text is free of Core2- and CoreS3-specific wording where the step itself is general. Order inside a step follows the order in `checks.json`.
- Leave the other CoreS3-family revisions' checks as they are, unless the same unit settles them.
- Write the revision's section 6 table in `VERIFICATION.md`, next to Core2 v1.3's, and say in section 3 that this revision can now run section 6.

Change no existing check id, no `covers` and no `board_steps` text the Core2 v1.3 run uses: `test_the_core2_run_asks_in_this_order_and_blocks_on_these` must pass unchanged.

## Inputs

- `VERIFICATION.md` sections 3, 6 and 7
- `verification/checks.json`: the note, `board_steps` and the Core2 v1.3 checks as the pattern
- `uv run scripts/board.py facts <revision>` and `board.py targets <revision>`
- [`B26-board-steps-in-checks-json.md`](B26-board-steps-in-checks-json.md), the Checkpoint
- [`B20-rename-cores3-download-checks.md`](B20-rename-cores3-download-checks.md): M5's CoreS3 download-mode procedure

## Definition of done

- [ ] `run --board <revision>` for the unit at hand walks its steps without refusing, and a test pins its order and blocking as the Core2 one does
- [ ] Every check of that revision has a step; `uv run scripts/validate.py` exits 0
- [ ] `VERIFICATION.md` sections 3 and 6 cover the revision
- [ ] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Step 1 of Before you start: ask the maintainer which CoreS3-family unit is at hand
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
