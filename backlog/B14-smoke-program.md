# B14 · Build the smoke program in four frameworks

Status: open
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

- [ ] Four smoke projects generate with a fresh nonce
- [ ] `build.*` passes for Arduino, PlatformIO and ESP-IDF: the build exits 0 and the nonce is in the image (or `blocked` with the missing toolchain named)
- [ ] `build.target-from-data` passes
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Write the Arduino smoke sketch by hand once, then turn its probe part into the generator
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
