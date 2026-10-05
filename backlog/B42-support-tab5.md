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

- **Done**: step 1 is settled (decided with the maintainer on 2026-10-04): three revisions keyed by date, `tab5@2025.05`, `tab5@2025.10` and `tab5@2026.04`; the ESP32-C6 is an `extra_components` entry with role `radio`; the data covers all four frameworks and the hardware run flashes ESP-IDF and Arduino only; a passing Tab5 run replaces Core2 v1.3 as the release bar; the run reads the touch controller and every I2C chip M5 lists, by id register where a datasheet gives one and by presence otherwise; PlatformIO stays an erratum (`m5-pio-pioarduino`) with no target record; the schematic PDF stays uncited; a signal may have a single outcome. Four more decisions on 2026-10-04: (a) the bar is `host`, `fact`, and `flash` and `device` in Arduino and ESP-IDF on `tab5@2026.04`, and the `platformio` and `uiflow2-micropython` skills stay `unverified` after a Tab5 run; (b) `verify.py run --offline` builds the smoke program for both `core2@v1.3` and `tab5@2026.04`; (c) the ESP32-P4 chip revision becomes an erratum on the Tab5 revisions, cited to a primary Espressif source, plus an open-question check; (d) the Tab5 session keeps the erase step and `handoff.live`. The data is sourced (`validate.py` 0 failures; `board.py facts tab5` answers). The smoke program generates and builds for `tab5@2026.04`: `smoke.py build arduino esp-idf --revision tab5@2026.04` passed all three checks on 2026-10-04 (esp32 3.3.12, m5stack 3.3.9, M5Unified 0.2.23, M5GFX 0.2.30, ESP-IDF v6.1), not flashed. In `smoke.py`: a framework `board.py` recommends no target for is skipped (PlatformIO); the ESP-IDF program probes after `M5.begin()` when the revision has an I/O expander on the internal bus (`SMOKE_PROBE_AFTER_BEGIN`); `sdkconfig.defaults` for `esp32p4` turns PSRAM on at 200 MHz, sets the flash size and `CONFIG_ESP32P4_SELECTS_REV_LESS_V3=y`; the M5Unified and M5GFX floors come from the errata a revision carries (`LIBRARY_FLOORS`), and `idf_component.yml` is now generated. `doctor.py` finds `riscv32-esp-elf-addr2line` in all three toolchains. The checks are in `verification/checks.json`: three Tab5 build checks (`built_for` names each build check's revision), 20 checks for `tab5@2026.04` with `step` and `depends_on`, and two steps of its own, `chip-id` and `manual-download`. `verify.py`: `RELEASE_UNIT` is `tab5@2026.04`; a skill gains a revision only when one of its checks is on that revision; the report shows `n/a` where a revision has no such check; the offline run builds and checks targets per revision. `VERIFICATION.md` sections 3 to 7 cover the Tab5. `python -m unittest discover tests` passes (242 tests) and `uv run scripts/check.py` says `gate: pass`
- **Next**: (1) The chip-revision erratum, decision (c). ESP-IDF v6.1's `components/esp_hw_support/port/esp32p4/Kconfig.hw_support` has `ESP32P4_SELECTS_REV_LESS_V3` (default n: the image supports v3.0 and later only, and the two ranges exclude each other). Find a primary Espressif source (the ESP-IDF chip-revision docs or the ESP32-P4 datasheet or a PCN) and add a source and an erratum to the three Tab5 revisions; do not state which chip revision Tab5 units carry beyond what a source says: v1.3 is one unit's `esptool chip-id` reading, a lead until the run records it (`open-question.chip-revision.tab5@2026.04`). Then say it in the `esp-idf` skill, with PSRAM at 200 MHz (M5GFX gives up on a Tab5 without it), keeping the body near 10 kB (it is 10147 bytes, already a warning). The smoke project's `idf: ">=5.2"` floor is unchanged: no primary source gives the ESP-IDF floor M5Unified needs on an ESP32-P4 (esp-bsp's 5.4 is esp-bsp's own). (2) `flashing-and-debugging`: `references/decoding-crashes.md` step 4 picks the decoder from `soc_part` and knows only the two Xtensa ones; an ESP32-P4 needs `riscv32-esp-elf-addr2line`, and a RISC-V panic prints no `Backtrace:` line (read ESP-IDF v6.1 `docs/en/api-guides/fatal-errors.rst` in `C:\esp\v6.1\esp-idf` for what it prints and how to decode it). `references/download-mode.md` gets M5's Tab5 procedure (hold reset about 2 s until the green LED flashes rapidly) with the marker *(untested on hardware: open-question.manual-download.tab5@2026.04)*. (3) The skills' descriptions and bodies where they name the supported boards, then the 63 trigger rows (about 35 minutes; see the memory note on trigger runs). (4) `README.md` (the intro's board list, the status line, the JTAG row), `CHANGELOG.md`, the hardware-ready gate paragraph in `backlog/README.md` (it still names the Core2 v1.3 as the one planned unit), and `VERIFICATION.md` sections 8, 10 and 11 where an example names `core2@v1.3`. Left from the code review of `6053dec..21983f5` (2026-10-04), each to settle or drop: make `sdkconfig_defaults` read the chip-revision setting from the erratum once it exists, as `LIBRARY_FLOORS` does for the libraries, instead of keying on `esp32p4`; the rule in `probe_after_begin` (an I/O expander on the internal bus) also moves the CoreS3 family's ESP-IDF probe after `M5.begin()`, which is intended but unbuilt and belongs to B36; the `arduino` step's text gained `--revision <revision>`, which a Core2 run shows too; `fact.ina226`, `fact.expander-1`, `fact.expander-2` and `fact.presence` cover only their signals, because a `covers` path cannot name one element of `extra_components` and a presence read does not prove the part; `validate.py` does not yet require `built_for` on a build check; `doctor.py` reports addr2line as found when only the Xtensa decoders are there; the ESP-IDF floor an ESP32-P4 needs belongs on `data/socs/esp32-p4.json` with an Espressif source; the after-begin bus functions in `main.cpp` repeat `smoke.ino`'s and could move to `common/`. (5) `uv run scripts/verify.py run --offline --write` (with PowerShell, the arduino-cli folder on PATH and the EIM profile loaded), then the hardware run: `verify.py run --board tab5@2026.04 --write`, `verify.py report`, `verify.py ingest`, commit. The unit is on COM3 (303A:1001). Generate with `--revision tab5@2026.04`
- **Files touched**: `data/` (the SoC, pin map, product, signals, sources, targets, one schema), `CONTEXT.md`, `scripts/board.py`, `scripts/smoke.py`, `scripts/doctor.py`, `scripts/verify.py`, `tests/test_board.py`, `tests/test_validate.py`, `tests/test_smoke.py`, `tests/test_doctor.py`, `tests/test_verify.py`, `verification/checks.json`, `verification/smoke/esp-idf/main/main.cpp`, `verification/smoke/esp-idf/main/idf_component.yml` (removed: generated now), `verification/smoke/README.md`, `.gitignore`, `VERIFICATION.md`, `README.md` (the roadmap row), this issue
- **Last commit**: the one that carries this checkpoint
- **Open questions**: none
