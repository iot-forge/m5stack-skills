# B42 · Support Tab5 and give the maintainer's unit its hardware run

Status: in-progress
Blocked by: —
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

Tab5 is a `roadmap` stub: `data/products/tab5.json` holds one revision, `tab5@v1.0`, with no facts, and `board.py` refuses it. The maintainer has a Tab5 (2026-10-04) and wants it supported and run on hardware before the plugin is published, so [B18](B18-decide-publication.md) is parked behind this issue.

**Step 1 is a decision, settled with the maintainer in a `/grilling` session.** The agent asks; it never answers for the maintainer. The questions, with the facts found so far:

- **Revisions.** M5's Tab5 page lists three display and touch generations under one SKU pair (C145, K145): ILI9881C with GT911 at release (2025-05-09), ST7123 from 2025-10-14, and ST7121 from 2026-04-28. Is that three revisions, or one revision with component alternatives (as the ILI9342E is on Core2)? And which one is the maintainer's unit?
- **The radio co-processor.** Tab5 has an ESP32-P4 and an ESP32-C6-MINI-1U for Wi-Fi. The schema has one `soc` per revision; this is the "second radio SoC" question the Roadmap also names for CoreS3 Thread BR.
- **Frameworks.** M5 documents all four for Tab5. Which does this issue cover, and which does the hardware run flash?
- **The smoke program and probes** on an ESP32-P4: which chips the run reads (BMI270, RX8130CE, INA226, the two PI4IOE5V6408, ES8388, ES7210 are on I2C).
- **The release bar.** `VERIFICATION.md` section 3 names one Core2 v1.3. Does a Tab5 run replace it, join it, or stay outside it?

Then build what was decided:

- A `data/socs/esp32-p4.json` record, a Tab5 pin map, build targets, signals and sources, each fact cited to a primary source. `tab5` leaves `roadmap` only for what is sourced.
- Its `host`, `flash`, `device` and `fact` checks in `verification/checks.json`, each with a `step` and `depends_on`, as B36 describes for a CoreS3-family unit. Change no Core2 v1.3 check.
- `scripts/doctor.py` and `flashing-and-debugging` where an ESP32-P4 differs: it is RISC-V, so crash decoding needs `riscv32-esp-elf-addr2line`, and M5's download mode is "hold reset about 2 s until the green LED flashes rapidly".
- The skills' descriptions and bodies where they name the supported boards, `README.md` and `CHANGELOG.md`.
- Run the hardware session on the maintainer's unit and ingest it.

If step 1 shows this is more than a few sessions, split it into issues here or chart a map with `/wayfinder`, as the README says.

## Inputs

- M5's Tab5 page, source `m5-tab5` (https://docs.m5stack.com/en/core/Tab5)
- `data/products/tab5.json`, `data/schema/`, and `data/products/cores3.json` as the pattern
- [`B36-cores3-family-board-steps.md`](B36-cores3-family-board-steps.md): how a second unit gets its run
- `VERIFICATION.md` sections 3, 6 and 7
- The README's Roadmap row for Tab5

## Definition of done

- [x] Each step 1 decision is recorded here or in an ADR
- [x] Tab5's data is sourced and `board.py facts tab5` answers
- [ ] `verify.py run --board <tab5 revision>` runs on the maintainer's unit and its report is committed
- [ ] `uv run scripts/check.py` exits 0

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: step 1 is settled (decided with the maintainer on 2026-10-04): three revisions keyed by date, `tab5@2025.05`, `tab5@2025.10` and `tab5@2026.04`; the ESP32-C6 is an `extra_components` entry with role `radio`; the data covers all four frameworks and the hardware run flashes ESP-IDF and Arduino only; a passing Tab5 run replaces Core2 v1.3 as the release bar; the run reads the touch controller and every I2C chip M5 lists, by id register where a datasheet gives one and by presence otherwise. The data is sourced: `data/socs/esp32-p4.json`, the pin map `tab5-a` (one for all three revisions), the three revisions in `data/products/tab5.json`, two new signals (`tab5-lcd-label`, `tab5-touch-probe`), the Tab5 outcomes on `sku-sticker`, `usb-vid` and `imu-probe`, and targets in both Arduino cores, UIFlow2 and esp-bsp (`validate.py` 0 failures; `board.py facts tab5`, `pins`, `targets`, `frameworks` and `tell-apart` answer; `tests/test_board.py` has three Tab5 tests). Two `board.py` fixes went in with the data, test-first: `frameworks` answers for `esp32-p4`, and `pins` drops its UNUSABLE line when the SoC has none. The stub tests and `query.stub-refuses` now use CoreS3 Thread BR. Leads from the unit, not facts: `esptool chip-id` on COM3 gave ESP32-P4 chip revision v1.3 on USB-Serial/JTAG (303A:1001), and its boot log printed `M5Tab5 detected ST7121 display` and `ST touch FW version 01`, so it is taken to be `tab5@2026.04` until the run confirms it
- **Next**: the checks and the smoke program. (1) Add presence or id-register probes to `data/signals.json` for the INA226 (0x41), both PI4IOE5V6408 (0x43, 0x44), ES8388 (0x10), ES7210 (0x40) and RX8130CE (0x32), each id value cited to its datasheet (M5's Tab5 page links them) or given a `datasheet_gap`. Read so far, not yet in `data/sources.json`: the INA226 datasheet M5 links (TI ZHCS078A) gives register 0xFE as 0x5449 and 0xFF as 0x2260, both 16-bit; the PI4IOE5V6408 datasheet (Diodes DS40583 rev 3-5, https://www.diodes.com/assets/Datasheets/PI4IOE5V6408.pdf) gives register 0x01 as 0xA2 at power-up, and its bit 1 clears when read, so 0xA0 on later reads: the probe must accept both; the ES8388 and ES7210 datasheets M5 links name no id register, and neither does the RX8130CE register manual, so those three are presence only; the ST7123 touch protocol document M5 links (V01.11) names register 0x0000 as Firmware Version but gives no values, so 1 and 3 come from M5GFX alone. M5GFX tells the ST7121 from the ST7123 by one byte read from 0x55 after writing the two-byte register address 0x0000 (1 is ST7121, 3 is ST7123): `smoke_probe.hpp` reads one-byte register addresses only, so either extend it or record this as an `open-question` check read off M5GFX's log line. (2) The Arduino smoke program already builds for `tab5@2026.04` from the data alone: `smoke.py build arduino --revision tab5@2026.04` passed for both cores on 2026-10-04 (esp32 3.3.12, m5stack 3.3.9, M5Unified 0.2.23, M5GFX 0.2.30), not flashed. Make the rest of `smoke.py generate` work for it: the ESP-IDF `main.cpp` probes before `M5.begin()`, when the touch controller may still be held in reset through the I/O expander, so check the touch scan there on the unit; the ESP-IDF project needs PSRAM on at 200 MHz and 16 MB flash in `sdkconfig.defaults` (M5GFX refuses the Tab5 otherwise), and PlatformIO has no target, so `generate` must skip it. Then `smoke.py build arduino esp-idf --revision tab5@2026.04`. (3) Add the `host`, `flash`, `device`, `fact` and `open-question` checks for `tab5@2026.04` to `verification/checks.json` with `step` and `depends_on`, a download-mode step (hold reset about 2 s until the green LED flashes rapidly), and move the release bar in `VERIFICATION.md` section 3 and `verify.py` (`RELEASE_UNIT`). (4) `doctor.py` and `flashing-and-debugging` for RISC-V, the skills' descriptions, `README.md` (the intro's board list and the JTAG row; the roadmap-stub row is done) and `CHANGELOG.md`. (5) The hardware run
- **Files touched**: `data/socs/esp32-p4.json`, `data/pinmaps/tab5-a.json`, `data/products/tab5.json`, `data/signals.json`, `data/sources.json`, `data/targets/` (four files), `scripts/board.py`, `tests/test_board.py`, `tests/test_validate.py`, `VERIFICATION.md` (query.stub-refuses), this issue
- **Last commit**: the one that carries this checkpoint
- **Open questions**: (maintainer) PlatformIO. Its own platform has no ESP32-P4 board at the pinned commit, so `board.py targets tab5` says PlatformIO has no target and `frameworks` says no; M5's pioarduino example is recorded as the erratum `m5-pio-pioarduino`. Is that enough for "the data covers all four frameworks", or should the pioarduino fork become a source with a target record? (maintainer) The schematic PDF (dated 2025-06-09, the release board) was read as text only and is not cited; every pin comes from M5's page, its pin map overview picture and M5Unified
