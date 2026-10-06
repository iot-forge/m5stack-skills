# B43 · Make verify.py read the tool versions itself

Status: in-progress
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

- [ ] `verify.py run --board` and `run --offline` record tool versions without asking for them, with a test for each tool's parsing
- [ ] The SKU and `observed` prompts reject the two answers above, with tests
- [ ] `VERIFICATION.md` says where the versions come from
- [ ] `uv run scripts/check.py` exits 0

## Stopping rule

At about 90% of your context, or before ending for any other reason: overwrite the Checkpoint below, commit everything, and stop. When the Definition of done is fully ticked: set `Status: done`, update the README's status table, clear the Checkpoint to `Done: all`, and commit.

## Checkpoint

<!-- Overwrite, never append. The next session starts from here. -->

- **Done**: nothing yet
- **Next**: claim the issue
- **Files touched**: none
- **Last commit**: none
- **Open questions**: none
