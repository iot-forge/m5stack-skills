# B42 · Support Tab5 and give the maintainer's unit its hardware run

Status: done
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

- **Done**: all. The hand-off test that was owed passed: the maintainer ran `handoff.live.tab5@2026.04` on 2026-10-06 in a separate session with an `arduino-cli monitor` holding COM3, and the `esp-idf` skill attempted once, read both port references, retried exactly once and handed off to `flashing-and-debugging` (checked against that session's log; recorded by hand in `verification/runs/2026-10-04.json`). After the ingest, `board-identification`, `arduino-m5unified`, `esp-idf` and `flashing-and-debugging` are `partial 2026-10-04: tab5@2026.04`; `pinout-lookup`, `platformio` and `uiflow2-micropython` stay `unverified`. The code review since `d410f6c` is applied: `board.py`'s `value_groups` (a note no longer splits a value one revision had verified; differing dates are given per revision), section 10 of `VERIFICATION.md` documents the `on <revisions> only` mark, and the run now holds the boot-log lines that `tab5.json` and `sdkconfig.md` cite it for. `python -m unittest discover tests` passes (253 tests) and `uv run scripts/check.py` says `gate: pass`
- **Next**: nothing in this issue. The maintainer answered Open questions (a) to (d) on 2026-10-06; [B44](B44-apply-b42-answers.md) applies the answers, and with them the release bar is met
- **Files touched**: everything under `data/` for the Tab5, `scripts/board.py`, `scripts/smoke.py`, `scripts/doctor.py`, `scripts/verify.py`, `scripts/validate.py`, their tests, `verification/checks.json`, `verification/smoke/`, `verification/runs/2026-10-04.json` and `.md`, `VERIFICATION.md`, `README.md`, `CHANGELOG.md`, `CONTEXT.md`, `docs/authoring/`, `references/download-mode.md`, `references/serial-ports.md`, the `arduino-m5unified`, `esp-idf`, `flashing-and-debugging` and `board-identification` skills, `backlog/README.md`, `backlog/B43-verify-reads-tool-versions.md`, this issue
- **Last commit**: Close B42: the Tab5 is supported and has its hardware run
- **Open questions** (the maintainer decides each; (a) to (d) are answered, see Next):
  1. **(a) The release bar.** Two things are owed on it: `fact.port-a-bus.tab5@2026.04` is `blocked` for want of a Grove unit, and `handoff.platformio` and `handoff.uiflow2-micropython` are `blocked`, because a Tab5 cannot cover them and they need a port that exists but fails. Get the parts, or change the bar?
  2. **(b) The first `fact.touch` failure.** The report's Failures section says None: the address scan failed, the probe was fixed and re-read in the same sitting, and the result is a `pass` with the failure in `observed` (the maintainer kept the fixes in B42 on 2026-10-05). Section 9 of `VERIFICATION.md` wants a failure in the Failures section and nothing fixed during the session. Leave the record, or rewrite it in section 9's shape?
  3. **(c) "Markers cleared: None".** `verify.py report` scans the files as they are now, so a report regenerated after the three Tab5 markers were removed no longer lists them. Should the report take them from the results instead?
  4. **(d) A check run on a later day.** `handoff.live` ran on 2026-10-06 and sits in the run of 2026-10-04, with the date in `observed`; the skills' status and `plugin_commit` (`5f78fc8`) carry the run's date and commit. `CONTEXT.md` calls a run one sitting.
  5. **(e)** A `covers` path cannot name one element of `extra_components`, so `fact.ina226`, `fact.expander-1`, `fact.expander-2` and `fact.presence` cover only their signals.
  6. **(f)** The `esp-idf` body is 10284 bytes, over the 10 kB warning.
  7. **(g)** What answers at 0x14 on an ST7121 unit is unknown.

  Deferred, each one line: `probe_after_begin` also moves the CoreS3 family's ESP-IDF probe after `M5.begin()`, unbuilt, B36's to build; the `arduino` step's text shows `--revision <revision>` on a Core2 run too; `doctor.py` reports addr2line as found when only the Xtensa decoders are there; the ESP-IDF floor an ESP32-P4 needs has no primary source; `sdkconfig_defaults` still keys the flash-size line on `esp32p4`; the after-begin bus functions in `main.cpp` repeat `smoke.ino`'s; the step `live-handoff-busy-port` does not say to regenerate the smoke project first, and the hand-off session met a generated `smoke_probe.hpp` older than `main.cpp` and regenerated it itself; the steps `live-handoff` and `live-handoff-busy-port` repeat their pass clause; `board.py` reads the hardware-verified date back out of the text `fmt_entry` builds
