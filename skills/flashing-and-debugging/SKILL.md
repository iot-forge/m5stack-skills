---
name: flashing-and-debugging
description: M5Stack Core flashing, recovery and crash diagnosis — flashes .bin images with esptool, erases flash and NVS, fixes serial ports, drivers and download mode, and decodes panics, backtraces, boot loops and brownout resets. Use when an upload keeps failing ("Failed to connect", "No serial data received"), no serial port appears, the monitor shows a Guru Meditation Error or repeated resets, or the user has a .bin to flash. Not for UIFlow2 firmware — use uiflow2-micropython.
license: MIT
allowed-tools:
  - Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/board.py" *)
  - Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py" *)
metadata:
  tested-with: "none"
  verification: "unverified"
---

# Flashing, recovery and crash diagnosis on M5Stack Core

Flashes, recovers and diagnoses M5Stack Core boards regardless of toolchain. It flashes `.bin` images with esptool, erases flash and NVS, and fixes ports, drivers and download mode. It decodes panics, backtraces, reset reasons, boot loops and brownout. It takes over when a framework skill's normal upload has failed twice or its monitor shows a crash.

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
- [ ] Detect the project: a .bin to flash, or serial output showing a panic, backtrace or reset loop
```

## Flash a .bin with esptool

<!-- TODO: authored in the implementation backlog issue for flashing-and-debugging. Until then this skill has no task guidance: follow the standing rules and the hand-offs, and say that this part of the skill is not written yet. -->

## Erase flash or NVS

<!-- TODO: authored in the implementation backlog issue for flashing-and-debugging. Until then this skill has no task guidance: follow the standing rules and the hand-offs, and say that this part of the skill is not written yet. -->

## Fix ports, drivers and download mode

<!-- TODO: authored in the implementation backlog issue for flashing-and-debugging. Until then this skill has no task guidance: follow the standing rules and the hand-offs, and say that this part of the skill is not written yet. -->

## Decode panics, backtraces and reset loops

<!-- TODO: authored in the implementation backlog issue for flashing-and-debugging. Until then this skill has no task guidance: follow the standing rules and the hand-offs, and say that this part of the skill is not written yet. -->

## Hand-offs

- UIFlow2 firmware and REPL → use the `uiflow2-micropython` skill
- a project's normal build and upload → use the framework skill for the project (`arduino-m5unified`, `platformio`, `esp-idf` or `uiflow2-micropython`)
- bugs in the user's own code → use the framework skill for the project (`arduino-m5unified`, `platformio`, `esp-idf` or `uiflow2-micropython`)
- "which board or revision do I have?" → use the `board-identification` skill
- JTAG / OpenOCD → declined: not covered in this version of the plugin
