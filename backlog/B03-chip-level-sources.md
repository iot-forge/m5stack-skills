# B03 · Cite chip-level facts to datasheets

Status: done
Blocked by: none
Gate: hardware-ready

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

The smoke program is generated from the `probe` signals in `data/signals.json`, and VERIFICATION.md asks for their registers and expected values to be cited to each part's datasheet. Today they cite M5Unified's driver source.

1. For AXP192, AXP2101, MPU6886, MPU9250, MPU6050, BMI270, INA3221 and BMM150: find the datasheet, add it to `data/sources.json` (kind `datasheet`), and check the register and value each probe uses against it. Add the datasheet to the probe's `src`. Where the datasheet disagrees with M5Unified, record both in the Checkpoint and raise it before changing anything.
2. **ATECC608B**: its probe has `register: null`. From the datasheet, record the wake sequence and the reply that proves presence, in the probe's machine-readable fields, so a sketch can be generated from it.
3. **ESP32-S3 ADC2**: `data/socs/esp32-s3.json` has no ADC2-under-Wi-Fi rule. Find Espressif's statement for the S3 (the ADC oneshot hardware limitations page is the likely place) and add the rule if it applies, cited.

## Inputs

- `data/signals.json`
- `data/socs/esp32-s3.json`
- `VERIFICATION.md` section 5 (what the smoke program reads)

## Definition of done

- [x] Every probe with a register cites a datasheet (`pmic-probe` carries a `datasheet_gap` instead, by the maintainer's decision; ADR 0005)
- [x] The ATECC608B probe has a wake sequence and an expected reply, cited
- [x] The S3 ADC2 question is answered in the data, or in the Checkpoint with the source that says there is no such rule
- [x] `uv run scripts/validate.py` exits 0
- [x] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all
- **Next**: none
- **Files touched**: `scripts/validate.py`, `scripts/board.py`, `tests/test_validate.py`, `tests/test_board.py`, `data/sources.json`, `data/signals.json`, `data/socs/esp32-s3.json`, `docs/adr/0005-probe-datasheet-gap.md`, `CONTRIBUTING.md`, `references/identifying-a-revision.md`, `backlog/B14-smoke-program.md`, `backlog/B21-per-value-probe-sources.md`
- **Last commit**: see `git log -- backlog/B03-chip-level-sources.md`
- **Open questions** (settled by the maintainer, 2026-09-26):
  1. `pmic-probe` expects AXP192 = 0x03 and AXP2101 = 0x4A (M5Unified). The AXP192 datasheet v1.13 (https://dl.linux-sunxi.org/AXP/AXP192%20Datasheet%20v1.13.pdf) lists no register 0x03. The AXP2101 V1.0 (https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/docs/datasheet/core/K128%20CoreS3/AXP2101_Datasheet_V1.0_en.pdf) skips it too. The AXP2101 rev 0.1 (https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/docs/products/core/Core2%20v1.1/axp2101.pdf, PDF page 22) gives {chip_id_h, chip_id_l} = 01_0111, which reads 0x47 or 0x57. Settled: keep M5Unified's values; the hardware run settles them. The Core2 v1.3 run settles the AXP192 value only.
  2. The `probe.datasheet_gap` waiver. Settled: keep it; its uses and how the end user sees it are in ADR 0005, `CONTRIBUTING.md` and `references/identifying-a-revision.md`, and `board.py tell-apart` prints it.
  3. BMM150: no probe reads it, and its datasheet (BST-BMM150-DS001: default address 0x10, chip ID 0x32 at 0x40 once 0x4B bit 0 is set) cannot confirm M5's wiring. Settled: dropped from B03.
  4. `data.probe-datasheet` is coarse. Settled: per-value sources and gaps, `hardware-test` as backing, and a separate kind for ESP-IDF pages, in [B21](B21-per-value-probe-sources.md).
  5. RM-MPU-9250A-00 rev 1.4 gives register 0x75 a reset value of 0x68 and a default of 0x71. Settled: recorded in `imu-probe`'s caveats.
