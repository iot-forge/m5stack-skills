# B02 · Re-pin the data and triage upstream drift

Status: done
Blocked by: none
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

Bring the pinned upstream references up to date, and decide where the new upstream items belong. `uv run scripts/refresh.py` lists them. On 2026-09-26 it reported:

- UIFlow2 releases 2.5.1–2.5.3 (data pins 2.4.6). Find which release is current, and check its `M5STACK_Core2` build for two things: whether it covers Core2 v1.3's BMI270, and which M5GFX version it bundles (ILI9342E panels need 0.2.27 or later). Update the uiflow2 targets, the `uiflow2-release` source and Core2 v1.3's recommended UIFlow2 target.
- M5's Arduino core at 3.3.9 (data pins 3.3.8). Re-read its `boards.txt` for the Core targets and update the `arduino-m5stack-boards` source.
- `board.csv` BID 35 `tab5x`, and UIFlow2 images `M5STACK_ToughC5` and `M5STACK_CoreMatrix`. For each, read the product's page on docs.m5stack.com. A Core-family product gets a stub (`roadmap` or `out-of-scope`) with a sourced reason, following the stubs already in `data/products/`. Any other family is out of this plugin's v1; note it in the Checkpoint and add nothing.

Every change cites its source, and `refresh.py` never edits data: you do.

## Inputs

- `uv run scripts/refresh.py`
- `data/targets/`, `data/sources.json`, `data/products/`
- `docs/adr/0003-shared-pinmap-and-soc-records.md` (refresh never writes data)

## Definition of done

- [x] Every item in a fresh `refresh.py` report is updated in `data/`, or explained in the Checkpoint as deliberately left
- [x] `uv run scripts/validate.py` exits 0
- [x] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->
- **Done**: all. Each item in the 2026-09-26 `refresh.py` report:
  - UIFlow2 2.4.6 -> 2.5.3, the latest release (tag commit 50e4407). Its Core2 image builds M5Unified 0.2.21 (8530f53), whose `IMU_Class::begin` probes a BMI270 at 0x68, then 0x69, on any board where no MPU6886 answers; there is no Core2-specific BMI270 axis handling. It bundles M5GFX 0.2.28 (9bcedf4), enough for the ILI9342E. 2.4.6 bundled M5GFX 0.2.21. Updated: `uiflow2-boards`, `uiflow2-release`, the new `uiflow2-submodules`, `uiflow2-m5unified` and `uiflow2-m5gfx`, the `M5STACK_Core2` and `M5STACK_CoreS3` notes, and the UIFlow2 gaps of core2@v1.3 and core2-for-aws@v1.3. Both gaps stay low confidence: nothing has run on hardware.
  - M5 Arduino core 3.3.8 -> 3.3.9 (SHA-256 matches the package index). The `m5stack_core`, `_fire`, `_core2`, `_tough` and `_cores3` entries of `boards.txt` are byte-identical; it adds `m5stack_toughc5` and `m5stack_papermono`. Every fact citing `arduino-m5stack-boards` is re-dated, and the `usb-vid` signal needs no change.
  - BID 35 `tab5x` (also the image `M5STACK_Tab5X`), deliberately left: docs.m5stack.com has no page for it (checked the sitemap and the en and zh_CN product lists). `board-id-csv` stays pinned at 0b3aa6c so that the report keeps flagging it until a page appears.
  - Image `M5STACK_CoreMatrix` (BID 152, ESP32-C61HR8, already in board.csv at the pin), deliberately left: there is no docs page.
  - Image `M5STACK_CoreInk` and PlatformIO `m5stack-coreink` (in the fresh report, but not listed in this issue): the docs product list gives CoreInk series `E-Paper`, so it is not a Core product. Nothing was added.
  - Image `M5STACK_ToughC5`: see Open questions.
  - `arduino-esp32` ids not in our data: informational; the report itself says they are mostly other families. `m5stack_tab5` belongs to the Tab5 stub, which has no targets.
  - `validate.py` exits 0 (15 warnings, the same set as before B02); 32 tests pass.
- **Next**: none
- **Files touched**: `data/sources.json`, `data/targets/uiflow2.json`, `data/targets/arduino-m5stack.json`, `data/products/core2.json`, `data/products/core2-for-aws.json`, `data/products/cores3-lite.json`, `data/products/cores3-se.json`, `data/products/gray.json`, `data/products/m5go.json`
- **Last commit**: see `git log -- backlog/B02-repin-data-and-triage-drift.md`
- **Open questions** (the maintainer decides):
  1. ToughC5: stub it as a Core product or not? Evidence: a zh_CN-only page (https://docs.m5stack.com/zh_CN/core/ToughC5), SKU K162, ESP32-C5HR8 (RISC-V), 2.0" ILI9342C touch screen, M5-Bus header, BID 33 (in board.csv since before the pin), `m5stack_toughc5` in the M5 Arduino core 3.3.9, a UIFlow2 board directory but no 2.5.3 release image. The docs product list, whose `series` field is M5's family taxonomy, does not list it, nor does the product comparison table. The `/core/` in its URL proves nothing, because Atom, Stamp and E-Paper pages sit under `/en/core/` too. A stub would also bring in a new platform, `esp32-c5`.
  2. Core Metal (C001-CNC) and Faces Kit (K005) are series `Core` on the docs product list but absent from `data/products/`. `refresh.py` never reports them, because it watches toolchains and board.csv, not the docs product list. Add stubs in a new issue?
