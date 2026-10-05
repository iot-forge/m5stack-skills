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

- **Done**: step 1 is settled (decided with the maintainer on 2026-10-04): three revisions keyed by date, `tab5@2025.05`, `tab5@2025.10` and `tab5@2026.04`; the ESP32-C6 is an `extra_components` entry with role `radio`; the data covers all four frameworks and the hardware run flashes ESP-IDF and Arduino only; a passing Tab5 run replaces Core2 v1.3 as the release bar (`host`, `fact`, and `flash` and `device` in Arduino and ESP-IDF on `tab5@2026.04`; `platformio` and `uiflow2-micropython` stay `unverified`); the run reads the touch controller and every I2C chip M5 lists; PlatformIO stays an erratum (`m5-pio-pioarduino`); the schematic PDF stays uncited; `verify.py run --offline` builds the smoke program for `core2@v1.3` and `tab5@2026.04`; the Tab5 session keeps the erase step and `handoff.live`. The data is sourced, the smoke program builds for `tab5@2026.04`, the checks are in `verification/checks.json`, and `VERIFICATION.md` sections 3 to 7 cover the Tab5 (all in the commits up to `4585e8f`). Since then, on 2026-10-04: (1) two errata on the three Tab5 revisions. `p4-chip-revision` says an ESP-IDF image fits chip revisions below v3.0 or v3.0 and later, never both, cited to ESP-IDF v6.1's `Kconfig.hw_support` (source `idf-p4-chip-revision`) and to both Arduino cores' `boards.txt`, whose `m5stack_tab5` builds for chips before v3.0 by default (`ChipVariant=prev3`); it does not say which revision a unit carries. `p4-psram-speed` says M5GFX needs PSRAM on, above 80 MHz. `smoke.py` reads its `sdkconfig` lines from them (`SDKCONFIG_LINES`), and the `esp-idf` skill writes the lines an erratum names, with `references/sdkconfig.md` ("An ESP32-P4's chip revision") saying how to choose. (2) `decoding-crashes.md` has the RISC-V case (`MEPC` and `RA`, no `Backtrace:` line by default, `riscv32-esp-elf-addr2line`, the RISC-V cause names, the ESP32-P4 reset codes); `download-mode.md` sends any `native USB` board down the native route and gives M5's Tab5 procedure with its untested marker. (3) The only description that names boards, `board-identification`'s, names Tab5. (4) `README.md`, `CHANGELOG.md`, the gate paragraph in `backlog/README.md` and one example in `VERIFICATION.md` section 10 name the Tab5. (5) `validate.py` requires `built_for` on a build check. (6) The code review of `4585e8f..cef34db` is applied (`d410f6c`): a v3.0 chip needs `CONFIG_ESP32P4_REV_MIN_300=y`, since ESP-IDF v6.1's default image starts at v3.1; `p4-psram-speed` also cites `idf-p4-psram`. (7) The offline run is in `verification/runs/2026-10-04.json` and `.md`: data 20, query 8, build 8 (four for `core2@v1.3`, three for `tab5@2026.04`, and `build.target-from-data`) and trigger 21 all pass, 0 failed; the four `handoff` checks are `blocked` until the hardware session. The account's session limit cut the first pass at `trigger.row-07`, so rows 1 to 6 ran at `cef34db` and the rest at `d410f6c` (the commits between change no description); the maintainer judged `trigger.row-11` on 2026-10-04. `python -m unittest discover tests` passes (245 tests) and `uv run scripts/check.py` says `gate: pass`
- **Next**: the hardware run, which the maintainer drives because `verify.py run --board` asks the operator at each step. In PowerShell, with the Tab5 on USB-C (it was COM3, 303A:1001): `$env:Path = "C:\Program Files\Arduino CLI;" + $env:Path; . C:\Espressif	ools\Microsoft.v6.1.PowerShell_profile.ps1`, then `uv run scripts/verify.py run --board tab5@2026.04 --write`. It merges into `verification/runs/<date>.json`; on a later day than 2026-10-04 that is a new file. Then `uv run scripts/verify.py report <that json>`, `uv run scripts/verify.py ingest <that json>`, read the report's Failures and Markers cleared sections and act on them, update the README's status line and verification table, run `uv run scripts/check.py`, tick the last two boxes and close the issue
- **Files touched**: since `4585e8f`: `data/products/tab5.json`, `data/sources.json`, `scripts/smoke.py`, `scripts/validate.py`, `tests/test_smoke.py`, `tests/test_validate.py`, `verification/smoke/README.md`, `skills/esp-idf/SKILL.md`, `skills/esp-idf/references/sdkconfig.md`, `skills/flashing-and-debugging/SKILL.md`, `skills/flashing-and-debugging/references/decoding-crashes.md`, `skills/board-identification/SKILL.md`, `references/download-mode.md`, `references/serial-ports.md`, `README.md`, `CHANGELOG.md`, `VERIFICATION.md`, `backlog/README.md`, `docs/authoring/boundaries.md`, `docs/authoring/skill-template.md`, `verification/runs/2026-10-04.json`, `verification/runs/2026-10-04.md`, this issue
- **Last commit**: the one that carries this checkpoint
- **Open questions**: for the maintainer: (a) a `covers` path cannot name one element of `extra_components`, so `fact.ina226`, `fact.expander-1`, `fact.expander-2` and `fact.presence` cover only their signals; widening it is a schema change. (b) The `esp-idf` body is 10343 bytes, over the 10 kB warning (it was 10147 before the Tab5 bullet); trim it here or in an issue of its own? Deferred, each one line: the rule in `probe_after_begin` also moves the CoreS3 family's ESP-IDF probe after `M5.begin()`, unbuilt, B36's to build; the `arduino` step's text shows `--revision <revision>` on a Core2 run too; `doctor.py` reports addr2line as found when only the Xtensa decoders are there; the ESP-IDF floor an ESP32-P4 needs has no primary source yet (the smoke project keeps `idf: ">=5.2"`); `sdkconfig_defaults` still keys the flash-size line on `esp32p4`; the after-begin bus functions in `main.cpp` repeat `smoke.ino`'s
