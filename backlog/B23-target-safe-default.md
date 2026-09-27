# B23 · Mark a safe default per build target

Status: open
Blocked by: none
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

A build target's `per_revision` lines in `data/targets/*.json` can set different options for the revisions it covers (`esp32:esp32:m5stack_core`: v1.4 keeps the 4MB default, v2.5–v2.7 need `FlashSize=16M`). When the user can't tell which revision they have, a skill needs one option set that is safe on every revision in play. B07 wrote that choice into `arduino-m5unified` as reasoning ("the option every revision accepts; for flash size, the smaller"). The maintainer decided the data carries it instead.

1. **Schema.** In `data/schema/targets.schema.json`, add an optional `safe_default` to a target entry: the options to build with when the revision is unknown (`"FlashSize=4M"`, or the toolchain's equivalent), what the other revisions give up, and `src`. `"safe_default": null` with a `note` says no safe choice exists (for example a compile-time PMIC choice), so the revision must be identified.
2. **Data.** Give every target whose `per_revision` values differ a `safe_default` or an explicit `null`, cited: the core's `boards.txt` default, and a primary source for why the choice is safe (for flash size, that an image built for a smaller flash runs on a larger one). Check the `Gaps:` text in `data/products/*.json` that names a menu choice (`Choose Flash Size 16MB`) against the same rule.
3. **validate.py.** A rule: a target whose covered revisions' `per_revision` values differ must carry `safe_default` (an object or `null`). Add a planted fixture that breaks it.
4. **board.py.** `targets` prints the safe default, or says none exists, when the revisions in play diverge on a target's options. Add a test.
5. **Skills.** Replace the reasoning in `arduino-m5unified`'s "Choose the FQBN for the revision" step 4 with "use the safe default `targets` prints; when it says none exists, identify the revision". Keep the body under 10 kB: it has 4 bytes of headroom, so move material to `skills/arduino-m5unified/references/` if needed. If B08 or B09 is done by then, give `platformio` and `esp-idf` the same step; if not, add it to their Jobs.

## Inputs

- `data/targets/*.json`, `data/schema/targets.schema.json`, `data/products/*.json` (the `Gaps:` text), `data/sources.json`
- `scripts/board.py` (`cmd_targets`), `scripts/validate.py`, `tests/`
- `skills/arduino-m5unified/SKILL.md`, and [`B07-skill-arduino-m5unified.md`](B07-skill-arduino-m5unified.md), the Checkpoint's Open questions

## Definition of done

- [ ] Every target whose covered revisions differ in `per_revision` has a cited `safe_default`, or `null` with a note
- [ ] `validate.py` enforces it, with a planted fixture that fails
- [ ] `board.py targets basic --toolchain arduino` prints the safe default; a test covers it
- [ ] `arduino-m5unified` uses the printed safe default instead of reasoning, and its body stays under 10 kB
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: List the targets whose covered revisions differ in `per_revision`, across all five files in `data/targets/`
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
