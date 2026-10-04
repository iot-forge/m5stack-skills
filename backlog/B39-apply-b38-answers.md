# B39 · Apply the maintainer's answers to B38's open questions

Status: in-progress
Blocked by: none
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

B38 re-read the 15 M5 docs pages that supported revisions cite and left eight disagreements under Open questions. The maintainer settled all eight on 2026-10-03. Apply each answer to `data/`, by hand, and set `last_verified` to today on each entry changed.

1. **Core2 speaker part.** On `core2@v1.0`, `core2@2023.02` and `core2@v1.3`, `audio.speaker` says the speaker is present and its part is not named: those pages name none.
2. **Legacy Fire USB bridge.** On `fire@2018.06`, `fire@2019.07`, `fire@2019.08` and `fire@2020.04`, `usb_bridge` is `unknown`, as Gray's is: the legacy Fire page has no USB chip row and lists drivers for both chips. Take the four revisions out of the `usb-vid` signal.
3. **Core2 for AWS USB bridge.** `core2-for-aws@v1.0` records both CP2104 and CH9102, citing its own page and the comparison table on the v1.3 page. List it under both `usb-vid` outcomes, so a CH9102 reading no longer proves v1.3.
4. **Gray TN-panel erratum.** Cut the sentence about the M5Stack library before 0.2.8 from the three Gray revisions; the Gray page does not have it.
5. **2018.2A PCB note.** Add the `pcb-2018.2a` erratum to the earliest revision of Gray, Fire and M5GO, as `basic@v1.4` has it, each citing its own page.
6. **Addresses the cited page does not give.** MPU9250 at 0x68 on `fire@2018.06` and `m5go@2018.04` also cites `m5unified`, with a note, as `gray@2017.12` does. BMM150 at 0x10 on `m5go@2019.06` cites the BMM150 data sheet; add it to `data/sources.json`.
7. **Core2 v1.1 PlatformIO example.** Add an erratum to `core2@v1.1` for the second PlatformIO block on its page, which uses the 4 MB Basic board id, as `basic@v2.7` has `m5-pio-snippet-4mb`. The `m5stack-core2` target cites the v1.1 page too.
8. **ILI9342E erratum wording.** `lcd-ili9342e` says what the pages say: M5GFX 0.2.27 or later is required. Cut "older builds may show a blank or wrong display" from every revision that carries it.

`data/**/*.json` are CRLF. `refresh.py` never writes `data/` (ADR 0003, ADR 0004).

## Definition of done

- [ ] Each of the eight answers is in `data/`, and each changed entry has today's `last_verified`
- [ ] `board.py tell-apart` on Fire and on Core2 for AWS reflects the changed `usb-vid` outcomes
- [ ] `uv run scripts/check.py` exits 0

The descriptions do not change, so no trigger rows need running. Answer 7 changes what the platformio skill tells a Core2 v1.1 user: the new erratum reaches them through `board.py`.

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: Apply answer 1 in `data/products/core2.json`
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
