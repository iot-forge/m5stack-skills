---
name: esp-idf
description: M5Stack Core boards under ESP-IDF — creates, configures and builds idf.py projects, sets sdkconfig options (flash size, PSRAM, partitions) and adds M5Unified or esp-bsp as IDF components. Use when the project has sdkconfig, idf_component.yml, a top-level CMakeLists.txt calling project(), or a platformio.ini with framework = espidf, or the user runs idf.py or menuconfig. Not for M5Unified or M5GFX API code — use arduino-m5unified.
license: MIT
allowed-tools:
  - Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/board.py" *)
  - Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py" *)
metadata:
  tested-with: "none"
  verification: "unverified"
---

# ESP-IDF on M5Stack Core

Creates, configures and builds ESP-IDF projects for M5Stack Core boards with `idf.py`. It sets the sdkconfig options that depend on the board (flash size, PSRAM, partitions) and adds M5Unified or an esp-bsp component. Bare ESP-IDF knows only the SoC, so the build target comes from `board.py`.

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

## Start here

Copy this checklist and tick it off:

```
- [ ] Run doctor.py; surface anything missing
- [ ] Resolve the board: board.py find "<user's words>"; note the revisions in play
- [ ] Detect the project: sdkconfig, idf_component.yml, a top-level CMakeLists.txt calling project(), or platformio.ini with framework = espidf
```

## Create or configure an idf.py project

<!-- TODO: authored in the implementation backlog issue for esp-idf. Until then this skill has no task guidance: follow the standing rules and the hand-offs, and say that this part of the skill is not written yet. -->

## Add M5Unified or an esp-bsp component

<!-- TODO: authored in the implementation backlog issue for esp-idf. Until then this skill has no task guidance: follow the standing rules and the hand-offs, and say that this part of the skill is not written yet. -->

## Build and flash with idf.py

<!-- TODO: authored in the implementation backlog issue for esp-idf. Until then this skill has no task guidance: follow the standing rules and the hand-offs, and say that this part of the skill is not written yet. -->

## Hand-offs

- M5Unified / M5GFX API code → use the `arduino-m5unified` skill
- `platformio.ini` itself → use the `platformio` skill
- an upload still failing after one retry, no port, drivers → use the `flashing-and-debugging` skill
- panics, backtraces, boot loops, brownout → use the `flashing-and-debugging` skill
- "which board or revision do I have?" → use the `board-identification` skill
- a question that is about pins → use the `pinout-lookup` skill
