# B43 · Make verify.py read the tool versions itself

Status: done
Blocked by: —
Gate: none

## Before you start

1. If `verification/runs/` holds a report, read the **Failures** section of the latest `<date>.md`. Anything there that touches this issue comes first.
2. Read [`backlog/README.md`](README.md) (how issues work, the checkpoint rule) if you haven't this session.
3. Set `Status: in-progress`, update the status table in the README, and commit. That commit is your claim.

## Job

`verify.py run --board` opens by asking the operator to type nine tool versions (`TOOLCHAINS` in `scripts/verify.py`), and an offline run records none. On the Tab5 run of 2026-10-04 the maintainer asked why, and decided on 2026-10-05 that a version is never entered by hand. The same run showed two more places where free typing went wrong: the SKU prompt took `1111`, and an `observed` prompt took `good`.

- `verify.py` reads each version from the tool: `arduino-cli version`, `arduino-cli core list` and `lib list` (the core that was used, and M5Unified), `pio --version`, `idf.py --version`, `esptool version`, `mpremote --version`, `claude --version`. `doctor.py` already finds most of these tools; use what it finds rather than a second search. A tool that is missing is left out, as a blank answer is today.
- The `esp32 core` entry names the core the run flashed with (`esp32:esp32` or `m5stack:esp32`) and its version. Today it is free text.
- The UIFlow2 image has no tool to ask: take its version from the image the `uiflow2` step flashes (`board.py targets`), or ask only for that one.
- An offline run records its versions too (`run.toolchains` is `{}` in `verification/runs/2026-10-04.json` before the board run merged in).
- The SKU prompt offers the revision's `sku` values from `data/` and accepts only one of them. An `observed` answer that is a single result letter is asked again.

## Inputs

- `scripts/verify.py`: `TOOLCHAINS`, `run_board`, `SKILL_TOOLS`
- `scripts/doctor.py`: how each tool is found on this machine
- `VERIFICATION.md` sections 6, 8 and 10 (`metadata.tested-with`)
- `tests/test_verify.py`

## Definition of done

- [x] `verify.py run --board` and `run --offline` record tool versions without asking for them, with a test for each tool's parsing
- [x] The SKU and `observed` prompts reject the two answers above, with tests
- [x] `VERIFICATION.md` says where the versions come from
- [x] `uv run scripts/check.py` exits 0

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: all. Both runs record the tool versions unasked (`ToolVersions`, one test a tool, and the `Offline` and `Board` tests); the SKU prompt takes only a SKU `data/` gives the revision and the `observed` prompt asks again after a result letter or a bare verdict (`Board`); `VERIFICATION.md` section 6 says where the versions come from; `uv run scripts/check.py` exits 0
- **Next**: nothing
- **Files touched**: `scripts/verify.py`, `tests/test_verify.py`, `VERIFICATION.md`, this issue, `backlog/README.md`
- **Last commit**: Close B43: verify.py reads the tool versions itself
- **Open questions**: one, for the maintainer. On the maintainer's machine `doctor.py` finds no `esptool` on `PATH` (the Arduino core and PlatformIO each bundle one) and finds `idf.py` only from a shell with the ESP-IDF environment active. A board run from a plain shell now records neither, where the run of 2026-10-04 had `esptool 5.3.1` and `esp-idf v6.1` typed in, and the next `ingest` would then cut `flashing-and-debugging`'s `tested-with` down to `claude-code`. Should `doctor.py` also look for the esptool a toolchain bundles, as it does for addr2line (B34)? That would be a new issue. Until it is settled, start a board run from the ESP-IDF shell with an esptool on `PATH`. Three choices made here are worth a look as well: the `observed` prompt also asks again after `pass`, `fail`, `good`, `bad`, `ok`, `okay` and `fine`, since the Job names a result letter and the Definition of done names `good`; an offline run names every installed Arduino core, because it flashes nothing; and an offline run written after a board run on the same day keeps the board run's `esp32 core`
