# B22 · Update ToughC5 once M5 releases it

Status: open
Blocked by: M5's release of ToughC5 (external; see step 1)
Gate: none

## Before you start

1. Open https://docs.m5stack.com/en/products?id=controllers-core. If ToughC5 is not listed there, or https://docs.m5stack.com/en/core/ToughC5 returns 404, M5 has not released it: stop here, without claiming.
2. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
3. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
4. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

`data/products/toughc5.json` is a stub added by B02 while ToughC5 was unreleased: `market_status: upcoming`, `support: roadmap`, family `core` (the maintainer's decision, following the Tough), sourced to M5's Chinese page only. Once M5 releases it:

- Re-read the product's English page and its entry in M5's product list (the `series` field, see B02's Checkpoint). Update the stub's `sku`, `soc`, `market_status` (`listed`) and `support.reason`, and add the English page as its source. If M5 lists it under another family than Core, ask the maintainer before changing `family`.
- Check which toolchains now carry a ToughC5 target: M5's Arduino core (`m5stack_toughc5` appeared in 3.3.9), espressif/arduino-esp32 `boards.txt`, platformio/platform-espressif32 `boards/`, a UIFlow2 release image for `M5STACK_ToughC5` (2.5.3 had a board directory but no image), and esp-bsp. Record what you find in the Checkpoint.
- Whether ToughC5 becomes `supported` is a design question: the ESP32-C5 is a new platform (RISC-V, dual-band Wi-Fi 6), and `board.py frameworks` knows only `esp32` and `esp32-s3`. Write it under Open questions for the maintainer; do not add v1 facts inside this issue.

Every change cites its source.

## Inputs

- `data/products/toughc5.json`, `data/sources.json` (`m5-toughc5`)
- `uv run scripts/refresh.py` (it flags `M5STACK_ToughC5` as a Core-looking image)
- [`B02-repin-data-and-triage-drift.md`](B02-repin-data-and-triage-drift.md), the Checkpoint

## Definition of done

- [ ] The ToughC5 stub reflects the released product, citing its English page
- [ ] The toolchain targets found are listed in the Checkpoint, and the support question is under Open questions
- [ ] `uv run scripts/validate.py` exits 0
- [ ] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Step 1 of Before you start: check whether M5 has released ToughC5
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
