---
name: arduino-m5unified
description: M5Stack Core firmware in C++ with M5Unified and M5GFX — writes and fixes display, touch, button, speaker, IMU and power code, and builds and uploads Arduino sketches with arduino-cli, choosing the FQBN for each revision. Use when the project has *.ino files or includes M5Unified.h or M5GFX.h (PlatformIO and ESP-IDF projects included), or the user mentions M5.begin, M5.Display, the Arduino IDE or an FQBN. Not for platformio.ini configuration — use platformio.
license: MIT
allowed-tools:
  - Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/board.py" *)
  - Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py" *)
metadata:
  tested-with: "none"
  verification: "unverified"
---

# Arduino and M5Unified on M5Stack Core

Writes and fixes M5Unified/M5GFX code for M5Stack Core boards, whatever the build system: display, touch, buttons, speaker, IMU and power. It also runs the Arduino toolchain: picking the FQBN from `esp32:esp32:*` or `m5stack:esp32:*` for each revision, then building and uploading with `arduino-cli`. It owns what is specific to M5 and to each revision, and sends general Arduino questions to the official docs.

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
- [ ] Detect the project: *.ino, or an #include of M5Unified.h / M5GFX.h
```

## Write or fix M5Unified and M5GFX code

<!-- TODO: authored in the implementation backlog issue for arduino-m5unified. Until then this skill has no task guidance: follow the standing rules and the hand-offs, and say that this part of the skill is not written yet. -->

## Choose the FQBN for the revision

<!-- TODO: authored in the implementation backlog issue for arduino-m5unified. Until then this skill has no task guidance: follow the standing rules and the hand-offs, and say that this part of the skill is not written yet. -->

## Build and upload with arduino-cli

<!-- TODO: authored in the implementation backlog issue for arduino-m5unified. Until then this skill has no task guidance: follow the standing rules and the hand-offs, and say that this part of the skill is not written yet. -->

## Hand-offs

- `platformio.ini` configuration → use the `platformio` skill
- sdkconfig, IDF components, `idf.py` → use the `esp-idf` skill
- an upload still failing after one retry, no port, drivers → use the `flashing-and-debugging` skill
- panics, backtraces, boot loops, brownout → use the `flashing-and-debugging` skill
- "which board or revision do I have?" → use the `board-identification` skill
- a question that is about pins → use the `pinout-lookup` skill
- MicroPython / UIFlow2 → use the `uiflow2-micropython` skill
