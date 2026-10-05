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
- [x] `verify.py run --board <tab5 revision>` runs on the maintainer's unit and its report is committed
- [x] `uv run scripts/check.py` exits 0

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: step 1 is settled (decided with the maintainer on 2026-10-04; the decisions are in this file's history at `5f78fc8` and in `VERIFICATION.md` section 3). The Tab5 is supported: three revisions on one pin map, the ESP32-P4 SoC record, build targets, signals, sources, the `p4-chip-revision` and `p4-psram-speed` errata, the smoke program, the checks, the RISC-V crash case, M5's download-mode procedure, and the board lists. The offline run passed on 2026-10-04 (data 20, query 8, build 8, trigger 21). The hardware run on the maintainer's unit (K145, `tab5@2026.04`, COM3) is in the same file, `verification/runs/2026-10-04.json` and `.md`, with no failure: `host` 3, `flash` and `device` in Arduino and ESP-IDF, seven `fact` checks pass; four open questions are observed (chip revision v1.3; esptool enters download mode by itself; an ST7121 display; M5's manual download-mode procedure works, and the unit then stays in download mode until a press of reset or `esptool --after watchdog-reset`). The run is ingested: the IMU, the touch part and the USB connection of `tab5@2026.04` are hardware-verified, the three answered markers are cleared, and `board-identification` is `partial 2026-10-04: tab5@2026.04`. Fixed on the way, each with tests: `board.py facts` no longer reports a divergence when one revision's fact is hardware-verified (`merge_hw_marks`); `fact.touch` first failed, because an ST7121 unit answers at 0x14 as well as 0x55, so `tab5-touch-probe` now reads the firmware-version byte at the 16-bit register address 0x0000 of 0x55 as M5GFX does (0x01 ST7121, 0x03 ST7123, no answer a GT911 unit), the smoke programs take a one- or two-byte register address (`register_width`, `reg_bytes`), and the re-read on the unit gave `I2C 0x55 ST7121 raw 0x01` (recorded by hand in the results file, with the first failure in `observed`). The maintainer's answers of 2026-10-05: the fixes stay in B42; the SKU is K145; the `psram` fact keeps M5's "octal" and notes ESP-IDF's 16-line mode; `verify.py` must read tool versions itself, now B43. `python -m unittest discover tests` passes (246 tests) and `uv run scripts/check.py` says `gate: pass` at `eb00a81`
- **Next**: one test is owed, then the close. (1) `handoff.live.tab5@2026.04` is `blocked` in the results: holding reset puts a Tab5 in download mode, so the upload succeeded. The maintainer chose a busy port instead (2026-10-05); the check now sits on the step `live-handoff-busy-port` (`eb00a81`). The maintainer runs it by hand, in a session that is not this one: terminal A holds the port with `& "C:\Program Files\Arduino CLI\arduino-cli.exe" monitor -p COM3 -c baudrate=115200`; terminal B runs `claude --plugin-dir C:\Personal\Projects\iotforge2\m5core-skills` from `verification\smoke\esp-idf` and is asked `Flash this project to my M5Stack Tab5.`, with the monitor left open through the retry. Pass: one attempt, the serial-port and download-mode procedures, exactly one retry, then a hand-off to `flashing-and-debugging`. The agent judges the pasted transcript and records the one result by hand in `verification/runs/2026-10-04.json` (LF, `json.dumps(indent=1, ensure_ascii=False) + "\n"`), saying in `observed` that it was run on a later day. Do NOT rerun `verify.py run --board` for it: answering `n` to the other steps would overwrite their passes. If the Tab5 shows a blank screen first, it is still in download mode: press reset once. (2) Then `uv run scripts/verify.py report verification/runs/2026-10-04.json` and `ingest`; with a pass, `arduino-m5unified`, `esp-idf` and `flashing-and-debugging` should gain the revision; check which do and why not for any that don't (`fact.port-a-bus.tab5@2026.04` is `blocked` for want of a Grove unit). (3) Update the README's status line (still "not yet verified on hardware") and its verification table from the report, `CHANGELOG.md` if the status wording changes, run `uv run scripts/check.py`, set `Status: done`, update the table in `backlog/README.md`, clear this Checkpoint to `Done: all`, commit. If the hand-off test fails, it goes in the report's Failures section (VERIFICATION.md section 9) and the skill is fixed before the close
- **Files touched**: everything under `data/` for the Tab5, `scripts/board.py`, `scripts/smoke.py`, `scripts/doctor.py`, `scripts/verify.py`, `scripts/validate.py`, their tests, `verification/checks.json`, `verification/smoke/` (the shared probe, both C++ programs, the UIFlow2 template), `verification/runs/2026-10-04.json` and `.md`, `VERIFICATION.md`, `README.md`, `CHANGELOG.md`, `CONTEXT.md`, `docs/authoring/`, `references/download-mode.md`, `references/serial-ports.md`, the `esp-idf`, `flashing-and-debugging` and `board-identification` skills, `backlog/README.md`, `backlog/B43-verify-reads-tool-versions.md`, this issue
- **Last commit**: the one that carries this checkpoint
- **Open questions**: for the maintainer: (a) a `covers` path cannot name one element of `extra_components`, so `fact.ina226`, `fact.expander-1`, `fact.expander-2` and `fact.presence` cover only their signals. (b) The `esp-idf` body is 10284 bytes, over the 10 kB warning. (c) What answers at 0x14 on an ST7121 unit is unknown. Deferred, each one line: `probe_after_begin` also moves the CoreS3 family's ESP-IDF probe after `M5.begin()`, unbuilt, B36's to build; the `arduino` step's text shows `--revision <revision>` on a Core2 run too; `doctor.py` reports addr2line as found when only the Xtensa decoders are there; the ESP-IDF floor an ESP32-P4 needs has no primary source; `sdkconfig_defaults` still keys the flash-size line on `esp32p4`; the after-begin bus functions in `main.cpp` repeat `smoke.ino`'s; the results file's `plugin_commit` is `5f78fc8` though later commits changed the touch probe it records
