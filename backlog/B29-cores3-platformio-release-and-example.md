# B29 · Record the CoreS3 PlatformIO release and M5's whole example

Status: done
Blocked by: none
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

Two data gaps B08 found while writing the `platformio` skill's "Unknown board ID" branch (`skills/platformio/references/board-ids.md`). The maintainer settled both as data work (2026-09-28). Follow `CONTRIBUTING.md` ("Changing board data"): every new fact cites a source in `data/sources.json`.

1. **The first release that ships `m5stack-cores3`.** `data/targets/platformio.json` notes the id as "present in platform-espressif32 develop (87cbed0)", and the `m5-pio-devkitc` erratum in `data/products/cores3.json` says the first release carrying it "is not recorded". Yet `espressif32` 7.0.1, installed on the maintainer's machine, lists it (`pio boards m5stack-cores3`, 2026-09-28). Find the first `platform-espressif32` release whose `boards/` holds `m5stack-cores3.json` (in a clone: `git log --diff-filter=A --format=%H -- boards/m5stack-cores3.json`, then `git tag --contains <that commit>`). Cite that release as a source, and word the target's `note` and the erratum so `board.py targets cores3 --toolchain platformio` and `board.py facts cores3` name it. Then an agent can tell the user which platform version to raise to.
2. **M5's whole CoreS3 example.** The `m5-pio-devkitc` erratum and the `platformio.gaps` texts of `cores3-se` and `cores3-lite` record M5's CoreS3 PlatformIO example as `board = esp32-s3-devkitc-1` with `-DBOARD_HAS_PSRAM`. When retrieved on 2026-09-28, the page's example also pinned `platform = espressif32@6.7.0` and set `-DARDUINO_USB_CDC_ON_BOOT=1` and `-DARDUINO_USB_MODE=1` (along with `-DESP32S3`, `-mfix-esp32-psram-cache-issue`, `-DCORE_DEBUG_LEVEL=5` and `upload_speed = 1500000`). Retrieve the page again, bump `m5-cores3`'s `ref`, and make those three texts carry every setting the example uses to configure the board: the platform pin, the board id and each build flag. Leave out debug-level and upload-speed choices, and say they were left out.
3. **The skill.** `skills/platformio/references/board-ids.md` tells the agent not to name a platform version the `board.py` output doesn't name. Once the output names one, check that the "Unknown board ID" steps read correctly with it (raise the pin to at least that version). Change the prose only if they don't.

## Inputs

- `data/targets/platformio.json` (`m5stack-cores3`), `data/products/cores3.json` (erratum `m5-pio-devkitc`), `data/products/cores3-se.json` and `data/products/cores3-lite.json` (`recommended_targets.platformio.gaps`), `data/sources.json` (`pio-esp32`, `m5-cores3`)
- https://github.com/platformio/platform-espressif32 (tags and `boards/`)
- https://docs.m5stack.com/en/core/CoreS3 (the PlatformIO section)
- [`B08-skill-platformio.md`](B08-skill-platformio.md), the Checkpoint's Open questions

## Definition of done

- [x] `board.py targets cores3 --toolchain platformio` and `board.py facts cores3` name the first `platform-espressif32` release that ships `m5stack-cores3`, cited to a source in `data/sources.json`
- [x] The `m5-pio-devkitc` erratum and the CoreS3-SE and CoreS3-Lite gaps texts carry M5's example's platform pin, board id and every board-configuring build flag, from a re-retrieved `m5-cores3`
- [x] `skills/platformio/references/board-ids.md` reads correctly with a named version (changed only if needed)
- [x] `uv run scripts/validate.py` exits 0
- [x] `python -m unittest discover tests` passes

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all. `m5stack-cores3` first ships in `platform-espressif32` 6.4.0: `boards/m5stack-cores3.json` was added in 91bdde3 (2023-08-02), `v6.4.0` (516520f) is the first tag that contains it (`git tag --contains`), and `v6.3.2` lacks the file. It is cited as the new source `pio-esp32-cores3`. The target's `note`, the `m5-pio-devkitc` erratum and the CoreS3-SE and CoreS3-Lite gaps texts name 6.4.0. `m5-cores3` was retrieved again on 2026-10-02; the erratum and both gaps texts carry M5's example's `platform = espressif32@6.7.0`, `board = esp32-s3-devkitc-1` and its five board-configuring build flags, and say the debug level and upload speed are left out. Test: `test_cores3_platformio_release_and_example` in `tests/test_board.py`. `skills/platformio/references/board-ids.md` needed no change: its "Unknown board ID" section passes on what the `board.py` output prints, which now names the release. After the close the maintainer asked for two more things (2026-10-02). The whole CoreS3 page was compared again with every fact that cites `m5-cores3` (specifications, I2C addresses, pin tables, the 30 M-Bus positions, the version table): no difference, so the 27 facts that cite only that page carry `last_verified: 2026-10-02`; facts that also cite another source keep their date. The `m5stack-cores3` target and the `m5-pio-devkitc` erratum went from `medium` to `high` confidence. `python -m unittest discover tests` passes; `uv run scripts/validate.py` exits 0.
- **Next**: none
- **Files touched**: data/sources.json, data/targets/platformio.json, data/products/cores3.json, data/products/cores3-se.json, data/products/cores3-lite.json, data/pinmaps/cores3-a.json, tests/test_board.py
- **Last commit**: a403471
- **Open questions**: none
