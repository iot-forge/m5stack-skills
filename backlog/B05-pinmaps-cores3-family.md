# B05 · Populate the CoreS3-family pin maps

Status: open
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

- [ ] All three maps `populated: true`, every entry cited
- [ ] `board.py pins cores3 --use camera,sd` answers, and SE has no camera claims
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Fetch the CoreS3 page and transcribe cores3-a
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
