---
name: pinout-lookup
description: M5Stack Core GPIO and connector lookup — reports which pins a board's features consume, which are free, which conflict, what Port A/B/C and the M-Bus expose, and which I2C addresses are taken, per revision. Use when the user asks which GPIO to use, whether a pin is free or safe (strapping, input-only, ADC2 with WiFi), or how to wire something to a Grove port. Not for which chips a board carries — use board-identification.
license: MIT
allowed-tools:
  - Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/board.py" *)
metadata:
  tested-with: "none"
  verification: "unverified"
---

# M5Stack Core pinout lookup

Answers GPIO-level questions for M5Stack Core boards, per revision. It covers which pins the features in use consume, what's free, what conflicts, what Port A/B/C and the M-Bus expose, and who sits on the shared I2C bus at which address. SoC cautions (strapping, input-only, ADC2 under WiFi) come with every pin it recommends.

## Standing rules

<!-- standing-rules:start -->
1. **Board facts come from `board.py`.** Before stating any hardware fact (pins, chips, I2C addresses, memory, build targets), run `board.py` with the user's own words for the board and answer only from its output. Name the revisions in play. Where the output has no answer, say the data has none. A board's report of what it is (`M5.getBoard()`, UIFlow2's `BOARD_ID`) is never evidence.
2. **Name every write to a board before it runs.** State the port, the board, and what the operation destroys, then wait for the user's go-ahead:
   - routine application flash, including a toolchain's normal upload (`arduino-cli upload`, `pio run -t upload`, `idf.py flash`) that also rewrites the bootloader and partition table: confirm once per port per session;
   - full erase, NVS erase, a partition-table or bootloader write on its own, deleting files on the device: confirm every time;
   - eFuse burn: print the command with a warning that it is irreversible, and let the user run it.
3. **Discover read-only first.** Run `doctor.py` and list serial ports before any write. One candidate port: use it and name it. Several: ask which. None: report what `doctor.py` found (cable, driver, download mode).
4. **The user reports what the board does.** Success is command output plus the user's observation of the screen, LEDs or serial monitor; ask for that observation before calling a step done.
5. **Detect and surface toolchains and drivers.** Report what is missing and how the user gets it; the user installs.
6. **Versions come from the project or the installed toolchain** (`platformio.ini`, `idf_component.yml`, `arduino-cli core list`, `idf.py --version`), never from memory.
7. **The M5Stack MCP server is secondary.** Label answers that come from it. Where it disagrees with `board.py`, `board.py` wins and you report the disagreement. When it is unreachable, continue from local data and say so.
<!-- standing-rules:end -->

## Paths (substituted at invocation, use verbatim)

- Board query: `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/board.py" <subcommand> "<the user's words for the board>"`

Run each with the Bash tool, one command per call: the skill pre-approves exactly these commands. If `uv` is not found, tell the user this plugin needs it (see its README) and stop.

## Start here

Copy this checklist and tick it off:

```
- [ ] Resolve the board: board.py find "<user's words>"; note the revisions in play
```

## Answer which pins are free, taken or conflicting

<!-- TODO: authored in the implementation backlog issue for pinout-lookup. Until then this skill has no task guidance: follow the standing rules and the hand-offs, and say that this part of the skill is not written yet. -->

## Explain one pin or connector

<!-- TODO: authored in the implementation backlog issue for pinout-lookup. Until then this skill has no task guidance: follow the standing rules and the hand-offs, and say that this part of the skill is not written yet. -->

## Hand-offs

- which chips, memory or features a board has, which board to buy → use the `board-identification` skill
- writing the code that drives the pin → use the framework skill for the project (`arduino-m5unified`, `platformio`, `esp-idf` or `uiflow2-micropython`)
- a specific Grove/M-Bus unit's wiring or driver beyond the port's pins → declined; points to the `m5stack` MCP server
