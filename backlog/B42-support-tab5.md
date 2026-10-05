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

- **Done**: step 1 is settled (decided with the maintainer on 2026-10-04; the decisions are in this file's history at `5f78fc8` and in `VERIFICATION.md` section 3). The Tab5 is supported: three revisions on one pin map, the ESP32-P4 SoC record, build targets, signals, sources, the `p4-chip-revision` and `p4-psram-speed` errata, the smoke program, the checks, the RISC-V crash case and M5's download-mode procedure, the board lists in the README, the changelog and the descriptions. The offline run passed on 2026-10-04 (data 20, query 8, build 8, trigger 21; `verification/runs/2026-10-04.md`). The hardware run on the maintainer's unit is in the same report (`verify.py run --board tab5@2026.04`, 2026-10-04, COM3, esptool 5.3.1, arduino-cli 1.5.2-rc.1 with the m5stack core, ESP-IDF v6.1): `host` 3, `flash` and `device` in Arduino and ESP-IDF, and six `fact` checks pass; four open questions are observed (chip revision v1.3; esptool enters download mode by itself; the display is an ST7121, so the unit is a `tab5@2026.04`; M5's manual download-mode procedure works, and esptool's reset afterwards leaves the unit in download mode). `fact.touch.tab5@2026.04` FAILED and `handoff.live.tab5@2026.04` and `fact.port-a-bus.tab5@2026.04` are `blocked` (see Next). The run is ingested (`9991d72`): the IMU and USB connection of `tab5@2026.04` are hardware-verified, and the three answered markers are cleared. `board.py facts` no longer reports a divergence when one revision's fact is hardware-verified (`merge_hw_marks`). `python -m unittest discover tests` passes (245 tests) and `uv run scripts/check.py` says `gate: pass`
- **Next**: the release bar is not met, so no skill left `unverified`. Two things stand in the way, and each needs the maintainer's word before it is built. (1) `fact.touch.tab5@2026.04`: on this ST7121 unit both 0x14 and 0x55 answer, so the `tab5-touch-probe` signal's rule (an answer at 0x14 means a GT911, a `tab5@2025.05`) is wrong. M5GFX 0.2.32 (`M5GFX.cpp`, the Tab5 branch of `autodetect`) reads one byte at register 0x0000 of 0x55 first: 1 is an ST7121, 3 an ST7123, and it takes an ACK at the GT911's address only when that read fails. A probe on that byte would separate all three revisions; this unit logged `M5Tab5 ST touch FW version 01`. Changing the signal is a data change with M5GFX as its source, then `smoke.py`, the check and VERIFICATION.md section 6 follow, and the Arduino step is re-read on the unit. What answers at 0x14 is unknown. (2) `handoff.live`: holding reset puts a Tab5 in download mode, so the upload succeeds and the step cannot produce a failing port; the four `handoff.<skill>` checks stay `blocked` and with them `arduino-m5unified` and `esp-idf`. It needs another way to make an upload fail on this board (a bare USB-to-serial adapter with nothing behind it, as VERIFICATION.md section 4 already allows, would do without the unit). Then: rerun the affected steps, `verify.py report` and `ingest`, the README's status line and verification table, and close
- **Files touched**: everything under `data/` for the Tab5, `scripts/board.py`, `scripts/smoke.py`, `scripts/doctor.py`, `scripts/verify.py`, `scripts/validate.py`, their tests, `verification/checks.json`, `verification/smoke/`, `verification/runs/2026-10-04.json` and `.md`, `VERIFICATION.md`, `README.md`, `CHANGELOG.md`, `CONTEXT.md`, `docs/authoring/`, `references/download-mode.md`, `references/serial-ports.md`, the `esp-idf`, `flashing-and-debugging` and `board-identification` skills, `backlog/README.md`, this issue
- **Last commit**: the one that carries this checkpoint
- **Open questions**: for the maintainer: (a) fix the touch signal and the hand-off step inside this issue, or close B42 on its Definition of done and open a new issue for them? B18 waits on B42 either way. (b) The run's `sku_sticker` is recorded as `1111`; what does the unit's sticker say? (c) The boot log reports the PSRAM in `X16 Mode` and ESP-IDF's only mode for an ESP32-P4 is `SPIRAM_MODE_HEX`, while the data says `32MB octal` from M5's page: keep M5's word, or note the difference? (d) `verify.py run --board` asks the operator for nine tool versions it could read itself, and takes anything at `observed`; worth an issue? (e) A `covers` path cannot name one element of `extra_components`, so `fact.ina226`, `fact.expander-1`, `fact.expander-2` and `fact.presence` cover only their signals. (f) The `esp-idf` body is 10284 bytes, over the 10 kB warning. Deferred, each one line: `probe_after_begin` also moves the CoreS3 family's ESP-IDF probe after `M5.begin()`, unbuilt, B36's to build; the `arduino` step's text shows `--revision <revision>` on a Core2 run too; `doctor.py` reports addr2line as found when only the Xtensa decoders are there; the ESP-IDF floor an ESP32-P4 needs has no primary source; `sdkconfig_defaults` still keys the flash-size line on `esp32p4`; the after-begin bus functions in `main.cpp` repeat `smoke.ino`'s
