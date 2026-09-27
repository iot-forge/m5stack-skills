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
- [ ] The ATECC608B probe has a wake sequence and an expected reply, cited
- [ ] The S3 ADC2 question is answered in the data, or in the Checkpoint with the source that says there is no such rule
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: List each probe in signals.json with the part and datasheet it needs
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
