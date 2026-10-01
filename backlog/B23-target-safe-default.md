# B23 · Mark a safe default per build target

Status: in-progress
Blocked by: [B33](B33-arduino-body-under-10kb.md)
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

- [x] Every target whose covered revisions differ in `per_revision` has a cited `safe_default`, or `null` with a note
- [x] `validate.py` enforces it, with a planted fixture that fails
- [x] `board.py targets basic --toolchain arduino` prints the safe default; a test covers it
- [ ] `arduino-m5unified` uses the printed safe default instead of reasoning, and its body stays under 10 kB
- [x] `uv run scripts/validate.py` exits 0
- [x] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**:
  - Three targets diverge across all five `data/targets/` files: `esp32:esp32:m5stack_core` and `m5stack:esp32:m5stack_core` (flash size) get `safe_default` `FlashSize=4M (the default)`, cited to their `boards.txt` and to the new source `idf-flash-size-check` (ESP-IDF v5.5 `esp_flash_spi_init.c`: a chip larger than the image header is used at the header's size; a smaller one fails the probe). `espressif/m5stack_core_2` gets `null`; its target `note` (compile-time PMU) says why. Proof: `uv run scripts/validate.py` exits 0.
  - The `Gaps:` text naming a menu choice (`Choose Flash Size 16MB`, Gray and M5GO) needs no change: every Gray and M5GO revision has 16MB.
  - `validate.py` rule `data.safe-default` (missing on a diverging target; `null` without a note), planted by `test_diverging_target_without_safe_default` and `test_no_safe_default_without_note`, mapped in `verify.py` `PLANTED` and `checks.json` (`data.planted-safe-default`).
  - `board.py targets` prints `safe default when the revision is unknown: ...` or `no safe default: ...` only while the covered revisions in play diverge; `test_target_safe_default`.
  - `arduino-m5unified` step 4, `platformio` step 3 and `esp-idf` step 3 (esp-bsp) use the printed safe default. `python -m unittest discover tests`: 127 run, OK.
  - Not done: the `arduino-m5unified` body is 10163 bytes (`validate.py`), over 10000; it was 10166 before this issue.
- **Next**: when B33 is done, re-run `uv run scripts/validate.py`; with no `skill.size` warning for `arduino-m5unified`, tick the last box and close.
- **Files touched**: `data/schema/targets.schema.json`, `data/sources.json`, `data/targets/arduino-esp32.json`, `data/targets/arduino-m5stack.json`, `data/targets/esp-bsp.json`, `scripts/validate.py`, `scripts/verify.py`, `scripts/board.py`, `verification/checks.json`, `tests/test_validate.py`, `tests/test_board.py`, `skills/arduino-m5unified/SKILL.md`, `skills/platformio/SKILL.md`, `skills/esp-idf/SKILL.md`, `backlog/B35-cross-target-safe-choice.md` (new)
- **Last commit**: 6432f27 (review findings), then the commit that records the decisions below
- **Open questions** (settled by the maintainer, 2026-09-30):
  - The body-size item can't be met without moving text. Do B33 next and close B23 after it, or fold B33's block-2 move into B23? Settled: B33 next, unchanged; B23 is blocked by it and closes after.
  - A `safe_default` lives on a target, so it can't cover a choice between targets (PlatformIO's two Basic ids, esp-idf's flash via `facts ... DIVERGES`); both skills keep their prose fallback. Should that choice live in data? Settled: yes, in a new issue, [B35](B35-cross-target-safe-choice.md); its shape is decided there.
