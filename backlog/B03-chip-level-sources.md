# B03 · Cite chip-level facts to datasheets

Status: in-progress
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

- [ ] Every probe with a register cites a datasheet
- [x] The ATECC608B probe has a wake sequence and an expected reply, cited
- [x] The S3 ADC2 question is answered in the data, or in the Checkpoint with the source that says there is no such rule
- [x] `uv run scripts/validate.py` exits 0
- [x] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**:
  - New rule `data.probe-datasheet` in `scripts/validate.py`: a probe that reads a register must cite a `datasheet` source, or carry `probe.datasheet_gap` (downgrades the failure to a warning). Check: `python -m unittest discover tests` (3 new planted tests).
  - `imu-probe` cites `ds-mpu6886`, `ds-mpu9250`, `ds-mpu6050`, `ds-bmi270`; `ina3221-probe` cites `ds-ina3221`. Every register and value matched the datasheet (0x75 = 0x19 / 0x71 / 0x68; BMI270 0x00 = 0x24 at 0x68/0x69; INA3221 0xFF = 0x3220). Check: `uv run scripts/validate.py` exits 0 with no `data.probe-datasheet` line for these two.
  - `atecc-probe` has machine-readable `wake`, `read_bytes` and `expected.present` = 04 11 33 43, cited to `ds-atecc608b-tngtls` (DS40002250B: address 0x35, tWLO 60 us, tWHI 1500 us, status 0x11 after wake). The CRC bytes 0x33 0x43 are computed from the data sheet's CRC rule, and the probe note says so. Check: `uv run scripts/board.py tell-apart bid:2` prints the note.
  - `data/socs/esp32-s3.json` has an `adc2_wifi` caution on G11-G20, cited to `idf-adc-oneshot-esp32s3` (Hardware Limitations: "ADC2 is also used by Wi-Fi"; `adc_oneshot_read()` "may fail when the ADC is in use by other drivers/peripherals, and return ESP_ERR_TIMEOUT") and `idf-gpio-esp32s3` (the ADC2_CH0-9 pin list). Check: validate exits 0.
- **Next**: The maintainer answers open question 1. Then either cite the AXP datasheets on `pmic-probe` and drop its `datasheet_gap`, or change the expected values, and tick the first box.
- **Files touched**: `scripts/validate.py`, `tests/test_validate.py`, `data/sources.json`, `data/signals.json`, `data/socs/esp32-s3.json`, this file
- **Last commit**: B03: apply review fixes
- **Open questions** (the maintainer decides each):
  1. **PMIC probe, datasheet vs M5Unified.** `pmic-probe` reads register 0x03 at 0x34 and expects AXP192 = 0x03, AXP2101 = 0x4A (M5Unified). The AXP192 datasheet v1.13 (https://dl.linux-sunxi.org/AXP/AXP192%20Datasheet%20v1.13.pdf, and M5's 4-page summary) lists no register 0x03: its table goes 00, 01, 04, 06-0B. The AXP2101 datasheet V1.0 (2021, https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/docs/datasheet/core/K128%20CoreS3/AXP2101_Datasheet_V1.0_en.pdf) also skips 0x03. The AXP2101 rev 0.1 (2019, https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/docs/products/core/Core2%20v1.1/axp2101.pdf, PDF page 22) defines 0x03 as chip_id_h[7:6], chip_version[5:4] (00 = A, 01 = B), chip_id_l[3:0], with {chip_id_h, chip_id_l} = 01_0111, which reads 0x47 (A) or 0x57 (B), not 0x4A. Nothing was changed: the probe carries a `datasheet_gap` and no AXP datasheet is in `sources.json`. Options: keep M5Unified's values and cite the hardware test on day one; or read the value and accept either.
  2. **The `probe.datasheet_gap` waiver** was added so the new rule doesn't turn `validate.py` red for every other issue while question 1 is open. Keep it, rename it, or replace it?
  3. **BMM150** is in the Job list, but no probe reads it: it appears only as the `magnetometer` component (behind the BMI270 aux interface on CoreS3, on the bus on Fire). No datasheet was added, because an uncited source fails validation. Cite the BMM150 datasheet on those component entries, or drop it from B03?
  4. For information: RM-MPU-9250A-00 rev 1.4 says "Reset value: 0x68" and "The default value of the register is 0x71" in the same section. It is cited for 0x71, which matches M5Unified. TDK's rev 1.6 link returns 404.
  5. **`data.probe-datasheet` is coarse.** It passes if the probe cites any `kind: datasheet` source, not one per part it reads, and ESP-IDF doc pages are also `kind: datasheet`. Checking per part would mean mapping each `expected` key to a source. Is the coarse rule enough?
