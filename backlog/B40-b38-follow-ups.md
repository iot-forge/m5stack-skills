# B40 · Settle the four follow-ups from the B38 re-read

Status: done
Blocked by: none
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

The B38 re-read turned up four things that were not disagreements between a page and an entry. The maintainer settled each on 2026-10-03.

1. **PSRAM mode on an ESP32-S3 board whose page gives none.** `cores3-lite@v1.0` has `psram: 8MB`, with no mode, as its page says. The esp-idf skill sets `CONFIG_SPIRAM_MODE_QUAD` or `CONFIG_SPIRAM_MODE_OCT` "as `facts` prints", and here it prints neither. The skill asks the user which mode the module is. Edit `skills/esp-idf/SKILL.md`, Create or configure step 4.
2. **An RTC backup cell the page is silent on.** `core2-for-aws@v1.3` and `tough@v1.0` have `backup_battery: null`. `null` means the sources say the part is absent (CONTRIBUTING.md), and these pages say nothing. Record `"unknown"`. `board.py` prints `null` as "backup cell not documented" today; fix it in this issue, test first: `"unknown"` prints that, and `null` prints "no backup cell".
3. **The CoreS3-SE battery.** `cores3-se@v1.0` says no battery, from the comparison table. Check the page and M5's schematic for what the board does have, and record it in the entry's note.
4. **The two PlatformIO targets B38 re-dated.** B38 set `last_verified` on `m5stack-fire` and `m5stack-core2` after checking them against the M5 page only. Check them against the pinned `pio-esp32` commit too; restore the earlier date if they do not hold.

A fifth, `soc_part: ESP32-D0WDQ6-V3` on Basic v1.4 and M5GO 2018.04, stays as it is: the maintainer accepted it.

`data/**/*.json`, `skills/*/SKILL.md` and `scripts/board.py` are CRLF.

## Definition of done

- [x] The esp-idf skill says what to do when `facts` prints a PSRAM size with no mode on `esp32s3`
- [x] `board.py facts` prints "backup cell not documented" for both revisions, from `"unknown"`, and a test covers it
- [x] The CoreS3-SE battery note says what the page shows, and the Checkpoint says what the schematic shows
- [x] The two PlatformIO targets are checked against the pinned commit, and the result is in the Checkpoint
- [x] `uv run scripts/check.py` exits 0

The skill's description does not change, so no trigger rows need running.

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all. Two results that left no trace in the files:
  - The PlatformIO targets hold against the pinned `pio-esp32` commit (87cbed0): `boards/m5stack-fire.json` and `boards/m5stack-core2.json` both exist, with 16MB flash and `-DBOARD_HAS_PSRAM`. Their `last_verified: 2026-10-03` stands.
  - M5's CoreS3-SE schematic (`Sch_M5_CoreS3_SE_v1.0.pdf`, text layer only; the drawing was not rendered) labels a part `BAT1/NC` and has a `VBAT` net. It is not a source in `data/sources.json`, so the battery note cites the page alone.
- **Next**: nothing
- **Files touched**: `skills/esp-idf/SKILL.md`, `scripts/board.py`, `tests/test_board.py`, `data/products/` (`tough`, `core2-for-aws`, `cores3-se`), this issue, `backlog/README.md`, `backlog/B18-decide-publication.md`
- **Last commit**: Close B40: settle the four follow-ups from the B38 re-read
- **Open questions**: none
