# B04 · Populate the ESP32 Basic-lineage pin maps

Status: done
Blocked by: none
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

Fill the five stub pin maps `basic-a`, `gray-2017.09`, `gray-a`, `fire-a` and `m5go-a` (`"populated": false` today). M5's product pages (basic_v2.7, gray, fire / fire_v2.7, m5go_v2.7 on docs.m5stack.com) carry full pin tables: LCD, microSD, buttons, speaker, IP5306, Grove ports and the M-Bus. This is transcription plus citation, not research.

Follow `data/pinmaps/core2-a.json` for the shape: every used GPIO with its claims (`fixed`, `feature`, `bus`), `dir: in` on uses of input-only pins, connectors with ordered positions, and buses holding pins only. Watch for:

- Fire consumes G16/G17 for PSRAM; Basic doesn't.
- `gray-2017.09` differs from `gray-a` in that the IP5306 isn't on I2C.
- Port A shares the internal I2C bus on this lineage (G21/G22). Check that against the pages.
- New features go into `data/features.json` first (the buttons, if claimed).

Set `populated: true` only when the whole map is sourced.

## Inputs

- `data/pinmaps/core2-a.json` (the pattern)
- `data/schema/pinmap.schema.json`
- `board.py pins <board> --use ...` to check the result reads right

## Definition of done

- [x] All five maps `populated: true`, every entry cited
- [x] `board.py pins basic`, `pins gray@2019.06` and `pins fire` answer instead of refusing
- [x] `uv run scripts/validate.py` exits 0
- [x] `python -m unittest discover tests` passes
- [x] A test in `tests/test_board.py` covers one of the new maps (for example, a Fire PSRAM pin is never free)

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all. The five maps are transcribed from the pin tables on the basic, basic_v2.7, gray, fire, fire_v2.7 and m5go_v2.7 pages (retrieved 2026-09-28); every table and all 30 M-Bus positions were checked against the pages by an independent review. Choices made within the issue, each stated in the map's `notes`: buttons A/B/C (G39/G38/G37) are `fixed` with `dir: in`, not a new feature, because they reach no connector and nothing frees them; Ports B and C appear only on `fire-a` and `m5go-a`, since the Basic and Gray spec tables list one Grove port; Fire's G16/G17 are `fixed` PSRAM and still listed on Port C and M-Bus 15/16; on Gray and M5GO, whose PSRAM is `unknown` in the product data, G16/G17 carry no use and get the SoC's `psram_pins` caution; `gray-2017.09` has the same pins as `gray-a` (the IP5306 difference is product data). `board.py pins basic`, `pins gray@2019.06`, `pins gray@2017.09`, `pins fire` and `pins m5go` exit 0. `uv run scripts/validate.py` exits 0 (15 warnings, as before); `python -m unittest discover tests` passes (112 tests); `verify.py run --offline --skip build --skip trigger` has no failures. New tests: `test_fire_psram_pins_never_free`, `test_basic_port_a_is_the_internal_bus`; `test_unpopulated_pin_map_refuses` now picks a stub product from `data/`.
- **Next**: none.
- **Files touched**: `data/pinmaps/{basic-a,gray-2017.09,gray-a,fire-a,m5go-a}.json`, `tests/test_board.py`
- **Last commit**: see `git log -- data/pinmaps/fire-a.json`
- **Open questions**: none.
