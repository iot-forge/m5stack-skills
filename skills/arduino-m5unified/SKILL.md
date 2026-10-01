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
- Environment check: `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py"`

Run each with the Bash tool, one command per call: the skill pre-approves exactly these commands. If `uv` is not found, tell the user this plugin needs it (see its README) and stop.

## Start here

Copy this checklist and tick it off:

```
- [ ] Run doctor.py; surface anything missing
- [ ] Resolve the board: board.py find "<user's words>"; note the revisions in play
- [ ] Detect the project: *.ino, or an #include of M5Unified.h / M5GFX.h
```

When `board.py` prints `Unknown board` with suggestions, show them to the user and ask which they mean.

## Write or fix M5Unified and M5GFX code

1. Read the M5Unified and M5GFX versions (`arduino-cli lib list`, `lib_deps` in `platformio.ini`, or `idf_component.yml`). The user installs a missing one. Done when both are named or reported missing.
2. Run `board.py facts "<user's words>" <fields the code touches>` (`display touch imu pmic audio rtc`). Pass on every `DIVERGES` branch and every `erratum` line. When an erratum names an M5GFX version, require that version or later in `lib_deps`, `idf_component.yml` or the user's install, and say so if the installed one is older. Done when every part the code relies on is in this output.
3. Read `${CLAUDE_SKILL_DIR}/references/choosing-pins.md` when the code uses `sd`, `speaker`, `mic`, `rgb_led`, `rs485`, `camera` or a connector pin; to narrow the revisions there, read `${CLAUDE_PLUGIN_ROOT}/references/identifying-a-revision.md`. Done when every pin in the code comes from `board.py pins`.
4. Write through M5Unified, never a chip driver: `#include <M5Unified.h>`, then `auto cfg = M5.config(); M5.begin(cfg);` in `setup()`, and `M5.update()` at the top of every `loop()` pass. Use its classes (`M5.Display`, `Touch`, `BtnA`–`BtnC`, `Speaker`, `Mic`, `Imu`, `Power`, `Rtc`): M5Unified detects the parts at runtime, so one sketch covers every branch `facts` printed. Never branch on `M5.getBoard()` to pick a revision. On a touch board without front buttons, M5Unified reads `M5.BtnA`–`M5.BtnC` from touches below the display *(untested on hardware: open-question.touch-below-240.core2@v1.3)*. Done when the code includes no chip library and no register address of its own.
5. Read `${CLAUDE_SKILL_DIR}/references/fixing-m5-code.md` when existing code fails: it won't build, hangs in `M5.begin()`, shows a blank display, ignores buttons or touch, cuts audio short, or includes `M5Stack.h`, `M5Core2.h` or `M5CoreS3.h`. Done when its fix is applied or handed off.

Done when the project builds (with arduino-cli below, or through the `platformio` or `esp-idf` skill) and the user reports the screen or serial output doing what was asked.

## Choose the FQBN for the revision

1. Take the installed cores from `doctor.py`'s `cores:` line (`esp32:esp32` is Espressif's, `m5stack:esp32` is M5's). Read `${CLAUDE_SKILL_DIR}/references/installing-a-core.md` when neither is installed. Done when at least one core is installed.
2. Pick the core: the one in an FQBN the project already names (`default_fqbn` in `sketch.yaml`, a build script); else the only one installed; both, with no FQBN in the project: ask. Done when one core is chosen.
3. Run `board.py frameworks "<user's words>"`; when its `arduino (M5Unified/M5GFX)` line is not `yes`, give the user what it prints. Then run `board.py targets "<user's words>" --toolchain arduino` and use the line for that core (`arduino-esp32` or `arduino-m5stack`):
   - A per-revision line naming a menu option (`FlashSize=16M`) becomes an FQBN option: `<FQBN>:FlashSize=16M`.
   - `has no target of its own. Recommended: <FQBN>. Gaps: ...`: use it, and give the user the gaps as printed. A gap naming a menu choice (`Choose Flash Size ...`) is an FQBN option too; `arduino-cli board details` gives its id.
   - Pass on `note:` lines and `[medium confidence]` as printed.

   Done when you have one FQBN, with its options, that is right for every revision still in play.
4. Read `${CLAUDE_SKILL_DIR}/references/unknown-revision.md` when per-revision lines differ and the revision is unknown. Read `${CLAUDE_PLUGIN_ROOT}/references/identifying-a-revision.md` when only host or probe signals remain. Done when the lines agree for the revisions left, or the fallback is told.
5. Run `arduino-cli board details -b <FQBN>`: it checks the id and options against the installed core, whose ids vary by version (the `note:` line). Done when it exits 0, lists every option you set, and the user has the FQBN and any gaps.

## Build and upload with arduino-cli

1. Run `arduino-cli compile --fqbn <FQBN> <sketch dir>`. Fix errors in the user's code here. Done when it exits 0.
2. Run `doctor.py --ports`. Read `${CLAUDE_PLUGIN_ROOT}/references/serial-ports.md` unless exactly one port has a `<-` marker that fits the board. No port: hand off to the `flashing-and-debugging` skill with what `doctor.py` found. Done when one port is named, or the hand-off is made.
3. Name the port, the board and what the upload replaces (the application on it); wait for the go-ahead, once per port per session (standing rule 2). Done when the user has said to go ahead.
4. Run `arduino-cli upload -p <port> --fqbn <FQBN> <sketch dir>`. Done when it exits 0 and esptool reports the write verified.
5. If the upload fails for a reason other than the code (`Failed to connect`, `Wrong boot mode detected`, a port that won't open, a write that stops part way):
   1. Read `${CLAUDE_PLUGIN_ROOT}/references/serial-ports.md` and `${CLAUDE_PLUGIN_ROOT}/references/download-mode.md`, and apply the case that matches the error.
   2. Retry the upload exactly once.
   3. If it fails again, stop and hand off to the `flashing-and-debugging` skill with the `doctor.py` output and the exact error text.

   Done when the retry succeeds, or the hand-off is made.
6. Ask the user to run `arduino-cli monitor -p <port> -c baudrate=<the sketch's rate>` themselves (it runs until stopped) and report the screen and serial output. Read `${CLAUDE_SKILL_DIR}/references/fixing-m5-code.md` when serial shows nothing, or the sketch runs but misbehaves. Still nothing, garbage, a panic or repeated resets: hand off to the `flashing-and-debugging` skill. Done when the user reports the board doing what the sketch should.

## Hand-offs

- `platformio.ini` configuration → use the `platformio` skill
- sdkconfig, IDF components, `idf.py` → use the `esp-idf` skill
- an upload still failing after one retry, no port, drivers → use the `flashing-and-debugging` skill
- panics, backtraces, boot loops, brownout → use the `flashing-and-debugging` skill
- "which board or revision do I have?" → use the `board-identification` skill
- a question that is about pins → use the `pinout-lookup` skill
- MicroPython / UIFlow2 → use the `uiflow2-micropython` skill
- general Arduino or M5Unified API questions → the official docs, or the `m5stack` MCP server with the answer labelled
