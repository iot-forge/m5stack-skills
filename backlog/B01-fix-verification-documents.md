# B01 · Fix the verification documents

Status: open
Blocked by: none
Gate: hardware-ready

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

Three small corrections found while scaffolding, all to documents the hardware session depends on:

1. `VERIFICATION.md` section 4, `trigger`: add `--allowedTools Skill` to the headless command. Without it `claude -p` denies the Skill tool, so the owner is detectable but the skill never loads. Note that on Windows `claude -p` also wants stdin closed (`< /dev/null`).
2. `CONTEXT.md`, **Result**: add `observed`, the result of an `open-question` check that ran and was recorded. `verification/results.schema.json` already accepts it.
3. Add the check `open-question.lcd-driver.core2@v1.3` to `VERIFICATION.md` section 7 and `verification/checks.json`: which LCD driver the unit carries (ILI9342C or ILI9342E, a change M5 dates 2026.8.7), and how that was determined. Say that the smoke program needs M5GFX 0.2.27 or later either way. The power-LED open question stays: M5's pages now document v1.3 as green, and the unit confirms it.

## Inputs

- `VERIFICATION.md` sections 4, 7 and 8
- `CONTEXT.md`
- `verification/checks.json`, `verification/results.schema.json`
- `board.py facts core2@v1.3 display` (the erratum text)

## Definition of done

- [ ] The three changes are made, and nothing else in `VERIFICATION.md` changes
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes
- [ ] `uv run scripts/verify.py run --offline` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Edit VERIFICATION.md section 4's headless command
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
