# B16 · Tune the seven descriptions together, then run every trigger row

Status: in-progress
Blocked by: [B07](B07-skill-arduino-m5unified.md), [B08](B08-skill-platformio.md), [B09](B09-skill-esp-idf.md), [B10](B10-skill-uiflow2-micropython.md), [B11](B11-skill-pinout-lookup.md), [B12](B12-skill-flashing-and-recovery.md), [B13](B13-skill-crash-decoding.md)
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

The descriptions compete with each other, so they are tuned together once every skill is written. Put all seven through the `skill-creator` skill's description review, then run all 21 trigger rows of VERIFICATION.md section 4 three times each (about 63 headless runs, roughly $0.08 each).

A rewording must keep each skill's boundary and deferral target (`docs/authoring/boundaries.md`), and stay within the template's description rules. If `neg-01` misfires on a plain `main.py`, narrow `uiflow2-micropython`'s trigger to `boot.py` plus `import M5`; don't drop the file signal.

## Inputs

- every `skills/*/SKILL.md` description
- `docs/authoring/skill-template.md` (Description)
- `docs/authoring/boundaries.md` (Known trigger weak spots)
- `VERIFICATION.md` section 4

## Definition of done

- [ ] All 21 rows pass under section 4's rules, run 3 times each
- [ ] A results file for the run is committed in `verification/runs/`
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Run all 21 rows once as a baseline before changing any description
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
