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

- [ ] Each step 1 decision is recorded here or in an ADR
- [ ] Tab5's data is sourced and `board.py facts tab5` answers
- [ ] `verify.py run --board <tab5 revision>` runs on the maintainer's unit and its report is committed
- [ ] `uv run scripts/check.py` exits 0

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: the unit is identified over USB, read-only: `esptool chip-id` on COM3 reports an ESP32-P4, chip revision v1.3, USB-Serial/JTAG (VID 303A, PID 1001). Its display generation is not yet known
- **Next**: Put the step 1 questions to the maintainer
- **Files touched**: this issue, `backlog/README.md`, `backlog/B18-decide-publication.md`
- **Last commit**: the one that adds this issue
- **Open questions**: the five in step 1 (the maintainer decides)
