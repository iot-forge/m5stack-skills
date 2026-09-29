# B31 · Add a hardware check: the esp-bsp Core2 display on an ILI9342E unit

Status: done
Blocked by: none
Gate: hardware-ready

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

The `lcd-ili9342e` erratum (Core2 and CoreS3 units made from 2026.8.7 carry an ILI9342E LCD driver) names only M5GFX: programs need M5GFX 0.2.27 or later. The esp-bsp Core2 component drives the panel with its own `esp_lcd_ili9341` driver, not M5GFX, and the data has nothing on that driver with an ILI9342E. The `esp-idf` skill says so (`skills/esp-idf/references/esp-bsp.md`, "Add the component"). The maintainer decided (2026-09-28, B09's open question 3) that the hardware session records an observation for it.

1. Add `open-question.esp-bsp-ili9342e.core2@v1.3` to `verification/checks.json`: kind `open-question`, skills `esp-idf`, revision `core2@v1.3`, note `VERIFICATION.md section 7`.
2. In `VERIFICATION.md` section 7 ("Runnable on a Core2 v1.3"), add the question: with the esp-bsp Core2 component and `CONFIG_BSP_PMU_AXP192=y` (what `board.py targets core2@v1.3 --toolchain esp-idf` prints), does esp-bsp's own `display` example show its picture correctly? Record the component version, the ESP-IDF version, and what the display shows. When `open-question.lcd-driver.core2@v1.3` finds an ILI9342C, record that this observation says nothing about the ILI9342E.
3. In `VERIFICATION.md` section 6, add the step: build esp-bsp's `examples/display` for `m5stack_core_2` (the example the component's `idf_component.yml` lists) and flash it through `idf.py`, after step 5 and before the UIFlow2 step. It replaces the ESP-IDF smoke program, so it goes after `device.esp-idf.core2@v1.3`. If [B26](B26-board-steps-in-checks-json.md) is done by then, put the step in `checks.json` the way B26 moved the others.
4. Mark the sentence in `skills/esp-idf/references/esp-bsp.md` that says the data has nothing on that driver with *(untested on hardware: open-question.esp-bsp-ili9342e.core2@v1.3)*, so `validate.py` ties the two together.

## Inputs

- `verification/checks.json` (`open-question.lcd-driver.core2@v1.3` as the pattern), `VERIFICATION.md` sections 6 and 7
- `skills/esp-idf/references/esp-bsp.md`
- espressif/esp-bsp at the pinned commit in `data/sources.json` (`esp-bsp`): `bsp/m5stack_core_2/idf_component.yml` (lists `examples/display`), `examples/display`
- [`B09-skill-esp-idf.md`](B09-skill-esp-idf.md), the Checkpoint's Open questions

## Definition of done

- [x] `open-question.esp-bsp-ili9342e.core2@v1.3` is in `verification/checks.json`
- [x] `VERIFICATION.md` section 7 states the question and what to record, and section 6 (or `checks.json`, after B26) has the step that runs it
- [x] `skills/esp-idf/references/esp-bsp.md` carries the untested marker for it
- [x] `uv run scripts/validate.py` exits 0
- [x] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all
- **Next**: none
- **Files touched**: `verification/checks.json`, `VERIFICATION.md`, `scripts/verify.py`, `tests/test_verify.py`, `skills/esp-idf/references/esp-bsp.md`
- **Last commit**: d1620ce
- **Open questions**: none. Found while writing the step: at the pinned commit `examples/display` picks its board through `bsp_selector` and `sdkconfig.bsp.m5stack_core_2`, which sets `CONFIG_BSP_PMU_AXP2101=y`, so the section 6 step layers `CONFIG_BSP_PMU_AXP192=y` on top.
