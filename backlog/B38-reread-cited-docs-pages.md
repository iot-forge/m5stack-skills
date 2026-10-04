# B38 · Re-read the M5 docs pages that supported revisions cite

Status: done
Blocked by: none
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

B37 recorded each M5 docs page's `content_sha256` on 2026-10-03, but the facts were last read on the page's `ref` date: 2026-09-26, or 2026-10-02 for `m5-cores3`. An edit M5 made between the two dates is inside the recorded hash, so `refresh.py` will never report it. The maintainer settled it on 2026-10-03: re-read the pages that supported revisions cite, and leave the pages only a stub cites.

15 of the 23 `m5-docs` sources are cited by a supported revision or by a pin map, target or signal: `m5-basic`, `m5-basic-v2.7`, `m5-gray`, `m5-fire`, `m5-fire-v2.7`, `m5-m5go-v2.7`, `m5-core2`, `m5-core2-v1.1`, `m5-core2-v1.3`, `m5-core2-for-aws`, `m5-core2-for-aws-v1.3`, `m5-tough`, `m5-cores3`, `m5-cores3-se`, `m5-cores3-lite`. The other 8 are cited only by a stub's `support` entry and stay as they are.

1. Run `uv run scripts/refresh.py` first. A page it lists as `CHANGED` moved after 2026-10-03; treat it the same way, and record the new hash at the end.
2. For each of the 15 pages, find every entry in `data/` that cites it (`src` holds its id, in `products/`, `pinmaps/`, `targets/` and `signals.json`), read the page, and check each of those entries against it.
3. Where the page and an entry disagree, do not decide alone which is right when another source backs the entry. Correct an entry the page alone supports; write the rest under Open questions for the maintainer.
4. For each page read, set its `ref` to `retrieved <today>` and its `content_sha256` to the hash `refresh.py` prints for it, by hand (CONTRIBUTING.md, "Changing board data"). Set `last_verified` to today on each entry you checked against the page.

`refresh.py` never writes `data/` (ADR 0003, ADR 0004). `data/**/*.json` are CRLF. The M5Stack MCP server is not a source; read the pages themselves.

## Definition of done

- [x] Each of the 15 pages has a `ref` no older than the day its hash was recorded
- [x] Every entry that cites one of them was checked against the page, and each disagreement is corrected or listed under Open questions
- [x] One real `uv run scripts/refresh.py` run reports every `m5-docs` page as unchanged
- [x] `uv run scripts/check.py` exits 0

The descriptions do not change, so no trigger rows need running. If a corrected fact changes what a skill tells the user, say so under Open questions.

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all
- **Next**: nothing in this issue. The maintainer answers the Open questions; each answer that changes data is new work.
- **Files touched**: `data/sources.json`, `data/signals.json`, `data/products/` (all 10 supported products), `data/pinmaps/` (all 11), `data/targets/platformio.json`, `data/targets/uiflow2.json`, this issue, `backlog/README.md`
- **Last commit**: Close B38: re-read the M5 docs pages that supported revisions cite
- **Open questions** (the maintainer decides each; none was changed in the data, and each entry named here still carries `last_verified: 2026-10-03`, which records that it was read against the page, not that the page confirms it):
  1. **Core2 speaker part.** `audio.speaker` is `1W-0928` on `core2@v1.0`, `core2@2023.02` and `core2@v1.3`, citing their own pages. The Core2 page names no speaker part, and the v1.3 page says only "Built-in Speaker". The v1.1 page ("1W (Size: 0928)") and both AWS pages ("1W-0928") do name it. Keep it and cite those pages, or say the part is not named?
  2. **Legacy Fire USB bridge.** `usb_bridge` is `CP2104` on `fire@2018.06`, `fire@2019.07`, `fire@2019.08` and `fire@2020.04`, citing `m5-fire`. That page has no USB chip row and its driver table lists both CP2104 and CH9102, so the note on `fire@2018.06` ("the legacy page lists CP2104 drivers only") is wrong. Gray, in the same position, is `unknown`. The `usb-vid` signal puts these four revisions under 10C4 only, so the answer changes that signal.
  3. **Core2 for AWS USB bridge.** `core2-for-aws@v1.0` is `CP2104`, as its own page says. The comparison table on the AWS v1.3 page gives "CP2104/CH9102" for it. The `usb-vid` signal lists it under 10C4 only, so a CH9102 reading is taken as proof of v1.3.
  4. **Gray TN-panel erratum.** `tn-panel` on the three Gray revisions says the M5Stack library before 0.2.8 shows inverted colours, citing `m5-gray`. The Gray changelog has no Note column; that sentence is on the Basic, Fire and M5GO pages only.
  5. **2018.2A PCB note.** "Devices with 2018.2A PCB version do not support C2C connection or PD power supply" is on the Basic, Basic v2.7, Gray, Fire, Fire v2.7 and M5GO v2.7 pages. Only `basic@v1.4` carries the `pcb-2018.2a` erratum. Which revisions should?
  6. **Addresses the cited page does not give.** `imu` MPU9250 at 0x68 on `fire@2018.06` and `m5go@2018.04` cites the product page alone, which gives 0x68 for the MPU6886 only (`gray@2017.12` cites `m5unified` for the same fact, with a note). `magnetometer` BMM150 at 0x10 on `m5go@2019.06` cites `m5-m5go-v2.7`, which never gives the BMM150's address (the Gray and Fire pages do).
  7. **Core2 v1.1 PlatformIO example.** The v1.1 page has two PlatformIO blocks that contradict each other. The first (`espressif32@6.12.0`, `board = m5stack-core2`, `default_16MB.csv`, `-DBOARD_HAS_PSRAM`) agrees with what `targets/platformio.json` gives `core2@v1.1` as "M5's own example". The second sets `board = m5stack-core-esp32` on `espressif32@6.7.0` with no partition line, which is the 4 MB Basic board. The entry cites `m5-core2`, not `m5-core2-v1.1`. `basic@v2.7` has the erratum `m5-pio-snippet-4mb` for the same kind of wrong example. Add one here, and cite the v1.1 page? An erratum would change what the platformio skill tells a v1.1 user.
  8. **ILI9342E erratum wording.** `lcd-ili9342e` says "older builds may show a blank or wrong display". The pages say only that M5GFX 0.2.27 or later is required.
