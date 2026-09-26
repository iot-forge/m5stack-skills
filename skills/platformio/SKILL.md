---
name: platformio
description: M5Stack Core projects under PlatformIO — creates and configures platformio.ini (board id, framework, lib_deps, partitions, PSRAM, build flags) and builds, uploads and monitors with the pio CLI. Use when the project has platformio.ini, or the user runs pio or wants a new PlatformIO project for a Core board. Not for M5Unified or M5GFX code — use arduino-m5unified.
license: MIT
allowed-tools:
  - Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/board.py" *)
  - Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py" *)
metadata:
  tested-with: "none"
  verification: "unverified"
---

# PlatformIO on M5Stack Core

Creates and configures PlatformIO projects for M5Stack Core boards, and builds, uploads and monitors them with the `pio` CLI. It owns `platformio.ini`: board id, framework, `lib_deps`, partitions, PSRAM and build flags. The code inside the project belongs to other skills.

## Standing rules

<!-- standing-rules:start -->
1. **Board facts come from `board.py`.** Before stating any hardware fact (pins, chips, I2C addresses, memory, build targets), run `board.py` with the user's own words for the board and answer only from its output. Name the revisions in play. Where the output has no answer, say the data has none. A board's report of what it is (`M5.getBoard()`, UIFlow2's `BOARD_ID`) is never evidence.
2. **Name every write to a board before it runs.** State the port, the board, and what the operation destroys, then wait for the user's go-ahead:
   - routine application flash: confirm once per port per session;
   - full erase, NVS erase, partition-table or bootloader write, deleting files on the device: confirm every time;
   - eFuse burn: print the command with a warning that it is irreversible, and let the user run it.
3. **Discover read-only first.** Run `doctor.py` and list serial ports before any write. One candidate port: use it and name it. Several: ask which. None: report what `doctor.py` found (cable, driver, download mode).
4. **The user reports what the board does.** Success is command output plus the user's observation of the screen, LEDs or serial monitor; ask for that observation before calling a step done.
5. **Detect and surface toolchains and drivers.** Report what is missing and how the user gets it; the user installs.
6. **Versions come from the project or the installed toolchain** (`platformio.ini`, `idf_component.yml`, `arduino-cli core list`, `idf.py --version`), never from memory.
7. **The M5Stack MCP server is secondary.** Label answers that come from it. Where it disagrees with `board.py`, `board.py` wins and you report the disagreement. When it is unreachable, continue from local data and say so.
<!-- standing-rules:end -->

## Paths (substituted at invocation, use verbatim)

- Board query: `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/board.py" <subcommand> "<the user's words for the board>"`
- Environment check: `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py"`

Run each with the Bash tool, one command per call: the skill pre-approves exactly these commands. If `uv` is not found, tell the user this plugin needs it (see its README) and stop.

## Start here

Copy this checklist and tick it off:

```
- [ ] Run doctor.py; surface anything missing
- [ ] Resolve the board: board.py find "<user's words>"; note the revisions in play
- [ ] Detect the project: platformio.ini (read its framework line)
```

## Create or configure platformio.ini

<!-- TODO: authored in the implementation backlog issue for platformio. Until then this skill has no task guidance: follow the standing rules and the hand-offs, and say that this part of the skill is not written yet. -->

## Build, upload and monitor with pio

<!-- TODO: authored in the implementation backlog issue for platformio. Until then this skill has no task guidance: follow the standing rules and the hand-offs, and say that this part of the skill is not written yet. -->

## Hand-offs

- M5Unified / M5GFX code → use the `arduino-m5unified` skill
- sdkconfig and component questions in a `framework = espidf` project → use the `esp-idf` skill
- an upload still failing after one retry, no port, drivers → use the `flashing-and-debugging` skill
- panics, backtraces, boot loops, brownout → use the `flashing-and-debugging` skill
- "which board or revision do I have?" → use the `board-identification` skill
- a question that is about pins → use the `pinout-lookup` skill
