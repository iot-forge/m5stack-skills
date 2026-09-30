# B16 · Tune the seven descriptions together, then run every trigger row

Status: done
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

- [x] All 21 rows pass under section 4's rules, run 3 times each
- [x] A results file for the run is committed in `verification/runs/`
- [x] `uv run scripts/validate.py` exits 0
- [x] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all. Recorded results:
  - Baseline: the 2026-09-28 run (verification/runs/2026-09-28.json, rows 01-15 at 2e9902f, the rest at 81972f9) already ran all 21 rows 3 times on these exact descriptions: every owner fired first in 3/3 and no negative row fired a skill. `git diff 2e9902f HEAD -- 'skills/*/SKILL.md' | grep '^[-+]description:'` is empty, and triggering reads only the name and description, so no separate baseline run was made.
  - Description review: all seven, read against skill-creator's description criteria (what and when, trigger strength, near-miss competition between siblings), the template's Description rules and boundaries.md rules 4, 5 and 7. Criteria only: the 21 rows are this plugin's eval set, so skill-creator's own `run_loop.py` query loop was not run. The bar for a change was a rule violation or a trigger risk a row shows. None was found, so no description changed. Pairs checked: platformio and esp-idf both defer M5Unified/M5GFX code to arduino-m5unified, and arduino-m5unified defers `platformio.ini` to platformio; flashing-and-debugging and uiflow2-micropython defer to each other; board-identification and pinout-lookup defer to each other. One gap is left: arduino-m5unified claims M5Unified includes in ESP-IDF projects but its deferral names only platformio, not esp-idf for sdkconfig. `validate.py` allows one sibling per deferral clause, and row-07 routes to esp-idf 3/3, so the extra always-loaded words aren't justified yet. neg-01's `main.py` weak spot held (0/3), so uiflow2-micropython keeps `boot.py or main.py`.
  - `trigger.*`, 2026-09-29, `claude` 2.1.285, `verify.py run --offline --skip build --operator claude --write` at 1c31609: 21/21 pass, 3 runs each. Row-07 run 2 also fired arduino-m5unified after esp-idf, which the table allows. trigger.row-11 routed to board-identification 3/3 and came back not-run (no terminal for the operator prompt); the maintainer judged its three saved answers pass, recorded as B15 did. `--skip build` because B16 is about triggers; the 5 `build.*` checks are not-run in the file. Results: verification/runs/2026-09-29.json and .md.
  - `uv run scripts/validate.py` exits 0 (16 warnings, none about a description). `python -m unittest discover tests`: 118 OK (1 skipped).
  - Reviewed with `/code-review` (standards and spec): no hard violation. The review asked for this record of the description review, and for the pair list above instead of "every pair defers both ways".
  - Observed, not fixed: in all three row-11 runs `--allowedTools Skill` blocked `board.py` and the reference read, and answer 3 fell back to general knowledge (labelled as unconfirmed). B28 covers pre-approving `board.py`. Row-11's answer 2 holds one U+FFFD where `claude -p` printed a `…` that wasn't UTF-8; `sh()` already decodes UTF-8 with `errors="replace"`.
- **Next**: none
- **Files touched**: `verification/runs/2026-09-29.json`, `verification/runs/2026-09-29.md` (new); no skill file
- **Last commit**: see `git log -- verification/runs/2026-09-29.json backlog/B16-description-tuning.md`
- **Open questions**: none
