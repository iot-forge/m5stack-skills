# B05 · Populate the CoreS3-family pin maps

Status: done
Blocked by: none
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

Fill the stub pin maps `cores3-a`, `cores3-se-a` and `cores3-lite-a` from the CoreS3, CoreS3 SE and CoreS3-Lite pages on docs.m5stack.com. As in B04, follow `data/pinmaps/core2-a.json`.

The S3 boards differ from the Core2 pattern:

- The camera takes many GPIOs; the SE has none.
- Several resets and interrupts go through the AW9523B expander, not GPIOs; record them as notes, not pins.
- Audio I2S uses G0 (MCLK), G33, G34, G13 and G14.
- The internal bus is G12/G11, and Ports A/B/C are G2/G1, G9/G8 and G17/G18.
- G19/G20 are USB, and G0 is a strapping pin that the boards' download mode relies on.

Add `camera` claims where a map has them.

## Inputs

- `data/pinmaps/core2-a.json`
- `data/socs/esp32-s3.json`
- `data/schema/pinmap.schema.json`

## Definition of done

- [x] All three maps `populated: true`, every entry cited
- [x] `board.py pins cores3 --use camera,sd` answers, and SE has no camera claims
- [x] `uv run scripts/validate.py` exits 0
- [x] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all. The three maps are transcribed from the pin tables on the CoreS3, CoreS3 SE and CoreS3-Lite pages (retrieved 2026-09-28; Lite's M-Bus is a diagram image on its page), and an independent review checked every pin, bus, connector and all 30 M-Bus positions against them with no transcription errors. Choices made within the issue, each stated in the map's `notes`: G35 is `fixed` LCD DC plus a `bus` use as the microSD's MISO, so it is never free; G0 is the mic's MCLK (audio table), not I2S_LRCK (M-Bus label); G13 is speaker out and G14 mic in, following each page's M-Bus diagram where the SE and Lite audio tables swap them (M5Unified's pin configuration agrees for CoreS3 and SE, cited as the new source `m5unified-audio`; Lite has no second source and is `confidence: medium`); G19/G20 are `fixed` native USB; G43/G44 carry no use; Port A is its own I2C bus; Ports B and C appear only on the maps whose pages list them (not Lite); SE's stub `bmi270_aux` bus is removed, as the SE has no IMU. `board.py pins cores3 --use camera,sd` exits 0, and SE's `--use camera` reports that camera claims no pins. `uv run scripts/validate.py` exits 0 (15 warnings, as before); `python -m unittest discover tests` passes (115 tests, 1 skipped: no supported product's pin map is a stub any more). New tests: `test_cores3_camera_and_sd_pins_taken`, `test_camera_claims_follow_the_camera_component`, `test_fixed_pin_on_a_bus_is_taken`.
- **Next**: none.
- **Files touched**: `data/pinmaps/{cores3-a,cores3-se-a,cores3-lite-a}.json`, `data/sources.json`, `tests/test_board.py`
- **Last commit**: see `git log -- data/pinmaps/cores3-a.json`
- **Open questions**: the maintainer decides. The claim model cannot say that two features share a pin by design. On the CoreS3 family, speaker and mic both claim I2S BCK (G34) and WS (G33), so `board.py pins cores3 --use speaker,mic` reports a CONFLICT ("they cannot run at once"), as it does for Core2's G0. For CoreS3 that is true of M5Unified, which re-installs its one I2S port for each (stated in the maps' notes), but it is not established for the hardware, which may run full duplex. Is CONFLICT the right answer here, or should shared I2S clocks get their own representation (an `i2s` bus, or a library-limit marker)?
