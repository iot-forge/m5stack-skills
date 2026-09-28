# B14 · Build the smoke program in four frameworks

Status: done
Blocked by: [B01](B01-fix-verification-documents.md), [B03](B03-chip-level-sources.md)
Gate: hardware-ready

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

Write the smoke program `VERIFICATION.md` section 5 describes, in `verification/smoke/<framework>/`, for Arduino/M5Unified (the reference), PlatformIO, ESP-IDF and UIFlow2. It:

1. prints `SMOKE <nonce>` and shows the nonce large;
2. reads chip IDs directly, using the probe fields in `data/signals.json`: PMIC, IMU, ATECC608B presence, INA3221 presence. For a probe with a `datasheet_gap`, the probe line also prints the raw register value ([ADR 0005](../docs/adr/0005-probe-datasheet-gap.md));
3. prints the libraries' self-report on a line labelled `SELF-REPORT (not evidence)`;
4. records the LCD driver for `open-question.lcd-driver.core2@v1.3`.

Probe code is generated from `signals.json` (a small generator in `verification/smoke/` or `scripts/`), not hand-copied, so a data correction reaches the sketch. The nonce is new for each generated project. Each project uses the target `board.py targets core2@v1.3 --toolchain <tc>` recommends, and M5GFX 0.2.27 or later.

Also add the `build.*` checks and `build.target-from-data` to `verification/checks.json`. The toolchains must be installed to build; the user installs them.

## Inputs

- `VERIFICATION.md` sections 4 (`build`) and 5
- `data/signals.json` (after B03)
- `board.py targets core2@v1.3`

## Definition of done

- [x] Four smoke projects generate with a fresh nonce
- [x] `build.*` passes for Arduino, PlatformIO and ESP-IDF: the build exits 0 and the nonce is in the image (or `blocked` with the missing toolchain named)
- [x] `build.target-from-data` passes
- [x] `uv run scripts/validate.py` exits 0
- [x] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all. On 2026-09-27 every `build.*` check passed, each with a fresh nonce found in its image: `build.arduino.esp32:esp32:m5stack_core2` (core 3.3.12), `build.arduino.m5stack:esp32:m5stack_core2` (core 3.3.9), `build.platformio.m5stack-core2` (espressif32 7.0.1) and `build.esp-idf.esp32` (ESP-IDF v6.1). All used M5Unified 0.2.23 and M5GFX 0.2.30, built with arduino-cli 1.5.2-rc.1 and PlatformIO 6.1.19. Every image contains M5GFX's `ILI9342 read-back` log strings, so the LCD-driver line will print. `build.target-from-data` passes. `tests/test_smoke.py` runs the UIFlow2 program under CPython against a simulated bus for each Core2-family revision.
- **Next**: none. B15 wires `scripts/smoke.py build` and `check-targets` into `verify.py run --offline`; their output is already in the results-file shape.
- **Files touched**: `scripts/smoke.py`, `tests/test_smoke.py`, `verification/smoke/**`, `verification/checks.json`, `.gitignore`; after the maintainer's answers: `VERIFICATION.md` section 4
- **Last commit**: see `git log -- verification/smoke`
- **Open questions** (the maintainer decides):
  1. **ESP-IDF target.** The project uses the bare `idf.py set-target esp32` from `board.py targets`' `bare_esp_idf_set_target`, not esp-bsp's `espressif/m5stack_core_2`: section 5 puts M5Unified in charge of the display, and the BSP would fight it. The check id is `build.esp-idf.esp32`. Should `VERIFICATION.md` section 4 say so? Settled: keep the bare target. Section 4's `build.target-from-data` now says that for ESP-IDF the recommended target is the bare `idf.py set-target`.
  2. **LCD driver record.** The C++ builds log at Info level, so M5GFX prints its own `[Autodetect] ILI9342 read-back DDh:.. CBh:.. -> ILI9342C/E` line, the panel's register read-back, during `M5.begin()`. The smoke program does not read the panel itself. The line appears once, before `SMOKE`, and not on screen, so the operator must capture serial from reset. UIFlow2 cannot read the panel. Settled: keep M5GFX's line. The operator opens the monitor and presses reset to capture it.
  3. **Probe selection.** The rule is every `probe` signal on `i2c_internal` whose outcomes name the revision. For Core2 that adds `touch-probe` (0x38 and 0x2E) to section 5's four. Settled: keep the rule.
  4. **ESP-IDF probe order.** The ESP-IDF build probes before `M5.begin()`, on `I2C_NUM_0` routed to the internal-bus pins, and deletes the bus afterwards. Doing it after would share M5Unified's `I2C_NUM_1`, which M5GFX treats as a foreign bus. So the probe lines come before the nonce reaches the screen, and chips M5Unified powers or resets (touch, via the AXP192) may read differently from the Arduino build. The `fact` checks come from the Arduino build only (section 5). Settled: keep probing before `M5.begin()`. A touch line that differs from the Arduino build's is expected, not a failure.
  5. **PlatformIO per-revision options.** `board_build.partitions = default_16MB.csv, -DBOARD_HAS_PSRAM` from the target's `per_revision` note are not applied. The note is prose, and the smoke program needs neither. Settled: leave them out. Revisit if B23 makes target options structured.
  6. **Arduino in `build.target-from-data`.** An arduino-cli sketch carries no target of its own, so the check compares `smoke.json`'s FQBNs with `board.py`. It catches a stale or hand-edited project, not a generator bug. Settled: accepted.
