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

1. Read `platformio.ini` if there is one: each `[env:…]` with its `platform`, `board`, `framework`, `build_flags` and `lib_deps`. Run `pio pkg list -g --only-platforms` for the installed `espressif32` version; on Windows, if it fails with `UnicodeEncodeError`, run it again prefixed with `PYTHONIOENCODING=utf-8`. Done when you have the project's `platform` pin, if any, and the installed version, or `pio` is reported missing (standing rule 5).
2. Run `board.py frameworks "<user's words>"`; when its `platformio` line is `no`, or `differs by revision` with a `no` among the revisions in play, give the user what it prints. Then run `board.py targets "<user's words>" --toolchain platformio`:
   - `<id>  (covers all in play)`: `board = <id>`. Its per-revision lines are M5's own settings: a `board_build.…` setting goes into the env as printed, a `-D…` flag into `build_flags`.
   - `has no target of its own. Recommended: <id>. Gaps: ...`: use `<id>`, and give the user the gaps as printed, once; never fill a gap from memory.
   - Several ids that each cover only some revisions, or per-revision lines that differ: step 3.
   - Pass on `note:` lines and `[medium confidence]` as printed. Read `${CLAUDE_SKILL_DIR}/references/board-ids.md` when the user wants a board id that a `note:` line, a `Gaps:` text or an erratum names in place of the recommended one.

   Done when you have one board id, with its settings, that is right for every revision still in play.
3. When the revisions in play disagree, run `board.py tell-apart "<user's words>"` and ask for the cheapest observation, then re-run `targets` with `--seen`. Read `${CLAUDE_PLUGIN_ROOT}/references/identifying-a-revision.md` when only host or probe signals remain. If the user can observe nothing, use the id every revision in play can run (for flash size, the smaller) and say what the others give up. Done when the lines agree for the revisions left, or the fallback is told.
4. PSRAM: run `board.py facts "<user's words>" psram flash`. When every revision in play has PSRAM, `build_flags` carries `-DBOARD_HAS_PSRAM` (add it unless step 2 already did). When one has none, or the data has none (`not documented`), leave it out and say why. In a `framework = espidf` project PSRAM is an sdkconfig option: hand that part to the `esp-idf` skill. Done when `build_flags` has the flag exactly when every revision in play has PSRAM, or the hand-off is made.
5. Libraries: when the code uses M5Unified or M5GFX (and in a new project), `lib_deps` lists `m5stack/M5Unified`. Run `board.py facts "<user's words>" display`; for each `erratum` line that names an M5GFX version, add `m5stack/M5GFX@>=<that version>`, and when the project pins a lower one, raise it and tell the user why. Done when `lib_deps` lists `m5stack/M5Unified` and every version an erratum names is a lower bound in it.
6. Write the env: `platform = espressif32` (keep a pin the project has), `board`, `framework = arduino` unless the project says otherwise, `monitor_speed` equal to the rate the code passes to `Serial.begin()` (in a new project, pick one and have the code use it), then the settings from steps 2–5. A build flag that names a pin takes it from `board.py pins "<user's words>" --use <features>`, never from memory. A new project gets `src/`; its code comes from the `arduino-m5unified` skill. Done when the file holds every setting from steps 2–5.
7. Run `pio boards <id>`. Read `${CLAUDE_SKILL_DIR}/references/board-ids.md` when it prints no table row for the id, or `pio` reports `UnknownBoard: Unknown board ID`. Compare its `Flash` column with the `flash` from step 4: when the id's is smaller, the build uses only that much; tell the user, and read `board-ids.md` if they want all of it. Done when `pio boards` lists every board id in the file, and the user has the gaps, notes and any flash shortfall.

## Build, upload and monitor with pio

1. Run `pio run -e <env>` in the project folder. Fix errors in `platformio.ini` here (`UnknownBoard`: step 7 above). Errors in the code go to the `arduino-m5unified` skill, or the `esp-idf` skill in a `framework = espidf` project. Done when it exits 0.
2. Run `doctor.py --ports` and `board.py facts "<user's words>" usb_bridge`. Read `${CLAUDE_PLUGIN_ROOT}/references/serial-ports.md` unless exactly one port has a `<-` marker that fits that bridge. No port: hand off to the `flashing-and-debugging` skill with what `doctor.py` found. Done when one port is named, or the hand-off is made.
3. Name the port, the board and what the upload replaces (the application on it); wait for the go-ahead, once per port per session (standing rule 2). Done when the user has said to go ahead.
4. Run `pio run -e <env> -t upload --upload-port <port>`. Done when it exits 0 and esptool reports the hash verified.
5. If the upload fails for a reason other than the code (`Failed to connect`, `Wrong boot mode detected`, a port that won't open, a write that stops part way):
   1. Read `${CLAUDE_PLUGIN_ROOT}/references/serial-ports.md` and `${CLAUDE_PLUGIN_ROOT}/references/download-mode.md`, and apply the case that matches the error.
   2. Retry the upload exactly once.
   3. If it fails again, stop and hand off to the `flashing-and-debugging` skill with the `doctor.py` output and the exact error text.

   Done when the retry succeeds, or the hand-off is made.
6. Ask the user to run `pio device monitor -p <port> -b <monitor_speed>` themselves (it runs until stopped) and report the screen and serial output. If serial shows nothing, step 2's `usb_bridge` reads `native USB` and `build_flags` lacks `-DARDUINO_USB_CDC_ON_BOOT=1`, add it (without it `Serial` may be on UART0), then build and upload again. Still nothing, garbage, a panic or repeated resets: hand off to the `flashing-and-debugging` skill. The code runs but misbehaves: hand off to the `arduino-m5unified` skill. Done when the user reports the board doing what the code should.

## Hand-offs

- M5Unified / M5GFX code → use the `arduino-m5unified` skill
- sdkconfig and component questions in a `framework = espidf` project → use the `esp-idf` skill
- an upload still failing after one retry, no port, drivers → use the `flashing-and-debugging` skill
- panics, backtraces, boot loops, brownout → use the `flashing-and-debugging` skill
- "which board or revision do I have?" → use the `board-identification` skill
- a question that is about pins → use the `pinout-lookup` skill
