---
name: esp-idf
description: M5Stack Core boards under ESP-IDF — creates, configures and builds idf.py projects, sets sdkconfig options (flash size, PSRAM, partitions) and adds M5Unified or esp-bsp as IDF components. Use when the project has sdkconfig, idf_component.yml, a top-level CMakeLists.txt calling project(), or a platformio.ini with framework = espidf, or the user runs idf.py or menuconfig. Not for M5Unified or M5GFX API code — use arduino-m5unified.
license: MIT
allowed-tools:
  - Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/board.py" *)
  - Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py" *)
  - Read(${CLAUDE_PLUGIN_ROOT}/references/**)
  - Read(${CLAUDE_SKILL_DIR}/references/**)
metadata:
  tested-with: "esp-idf v6.1, claude-code 2.1.289"
  verification: "partial 2026-10-04: tab5@2026.04"
---

# ESP-IDF on M5Stack Core

Creates, configures and builds ESP-IDF projects for M5Stack Core boards with `idf.py`. It sets the sdkconfig options that depend on the board (flash size, PSRAM, partitions) and adds M5Unified or an esp-bsp component. Bare ESP-IDF knows only the SoC, so the build target comes from `board.py`.

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
- [ ] Detect the project: sdkconfig, idf_component.yml, a top-level CMakeLists.txt calling project(), or platformio.ini with framework = espidf
```

## Create or configure an idf.py project

1. Run `idf.py --version`. Read `${CLAUDE_SKILL_DIR}/references/idf-environment.md` when it fails, prints no `ESP-IDF v…`, or the host is Windows. In an existing project, read `sdkconfig` (`CONFIG_IDF_TARGET`), `sdkconfig.defaults` and `main/idf_component.yml`. Done when you have the ESP-IDF version and the project's target and dependencies.
2. In a `framework = espidf` PlatformIO project, this skill writes only `sdkconfig.defaults` (step 4) and `src/idf_component.yml` (the next section, by hand, since `idf.py add-dependency` needs an idf.py project); `platformio.ini`, build and upload go to the `platformio` skill. Done when you know which kind of project this is.
3. Run `board.py frameworks "<user's words>"`; if its `esp-idf` line doesn't start with `yes`, give the user what it prints. Run `board.py targets "<user's words>" --toolchain esp-idf`: its `bare ESP-IDF` line names the SoC (`idf.py set-target <soc>`). Done when you have one SoC.
4. Run `board.py facts "<user's words>" flash psram` and write `sdkconfig.defaults`, keeping any other lines:
   - `flash: <n>MB`: `CONFIG_ESPTOOLPY_FLASHSIZE_<n>MB=y`. On `DIVERGES`, run `board.py tell-apart "<user's words>"`, ask for the cheapest observation and re-run `facts` with `--seen`. Read `${CLAUDE_PLUGIN_ROOT}/references/identifying-a-revision.md` when only host or probe signals remain. If the user can observe nothing, use the printed `safe choice` and pass on what it gives up; with none, stop.
   - PSRAM on every revision in play (sizes may differ): `CONFIG_SPIRAM=y`, and on `esp32s3` `CONFIG_SPIRAM_MODE_QUAD=y` or `CONFIG_SPIRAM_MODE_OCT=y`, as `facts` prints `quad` or `octal`. When it prints a size with neither, write no mode line (ESP-IDF keeps its default), say the data has no mode, and ask the user which their module is. Any revision with `none` or `not documented`: leave PSRAM off and say why.
   - An `erratum` line naming `CONFIG_` lines: read `${CLAUDE_SKILL_DIR}/references/sdkconfig.md` ("An ESP32-P4's chip revision") first.
   - Read `${CLAUDE_SKILL_DIR}/references/sdkconfig.md` when the user wants OTA, a data partition or a bigger app.

   Done when `sdkconfig.defaults` has a line for each fact that applies.
5. New project: run `idf.py create-project <name>` (`--cpp` for M5Unified), put step 4's `sdkconfig.defaults` in its folder, then run `idf.py -C <folder> set-target <soc>`. Existing project with another `CONFIG_IDF_TARGET`: `set-target` replaces its `sdkconfig`; say so and wait for the go-ahead. Otherwise run `idf.py reconfigure`. M5Unified or M5GFX code, in `app_main`, comes from the `arduino-m5unified` skill; a GPIO in the user's IDF code comes from `board.py pins "<user's words>" --use <features>`. Done when it exits 0 and `sdkconfig` has `CONFIG_IDF_TARGET="<soc>"` and each line from step 4. Read `${CLAUDE_SKILL_DIR}/references/sdkconfig.md` when a line is missing.

## Add M5Unified or an esp-bsp component

1. Run `board.py targets "<user's words>" --toolchain esp-idf` and read its `esp-bsp` line. Choose one component, not both (M5Unified brings M5GFX, an esp-bsp component its own panel and touch drivers): the one the manifest lists or the user asks for; with neither, ask which, or take M5Unified when the line says `NO target`. When it says `NO target` and the user wants esp-bsp, tell them there is none and offer M5Unified. Done when one is chosen.
2. M5Unified: run `idf.py add-dependency "m5stack/m5unified"`. Run `board.py facts "<user's words>" display`; for each `erratum` line naming an M5GFX version, run `idf.py add-dependency "m5stack/m5gfx>=<that version>"`. If `m5stack/m5gfx` is already listed, it refuses (`already exists`): raise its lower bound in the file and tell the user why. Done when the manifest lists `m5stack/m5unified`, and each M5GFX version an erratum names as a lower bound.
3. esp-bsp: its per-revision `menuconfig` lines are compile-time choices. When they differ, narrow the revisions as for `flash` above, re-running `targets` with `--seen`. If the user can observe nothing, use the printed `safe default` and pass on what it gives up; on `no safe default`, write none: offer M5Unified, which settles the PMIC at runtime, or stop until the revision is known. Then read `${CLAUDE_SKILL_DIR}/references/esp-bsp.md`. Done when it is followed through, or the user has chosen.
4. Run `idf.py reconfigure`, which downloads the components; read `${CLAUDE_SKILL_DIR}/references/idf-environment.md` when it fails. Done when it exits 0 and `sdkconfig` has each setting from step 3; read `${CLAUDE_SKILL_DIR}/references/sdkconfig.md` when one is missing.

## Build and flash with idf.py

1. Run `idf.py build`. Fix errors in `sdkconfig`, the manifest and the user's IDF code here; errors in M5Unified or M5GFX code go to the `arduino-m5unified` skill. Read `${CLAUDE_SKILL_DIR}/references/sdkconfig.md` when it reports a partition `too small for binary`. Done when it exits 0.
2. Run `doctor.py --ports` and `board.py facts "<user's words>" usb_bridge`. Read `${CLAUDE_PLUGIN_ROOT}/references/serial-ports.md` unless exactly one port has a `<-` marker that fits that bridge. No port: hand off to the `flashing-and-debugging` skill with what `doctor.py` found. Done when one port is named, or the hand-off is made.
3. Name the port, the board and what the flash replaces (the bootloader, the partition table and the application on it); wait for the go-ahead, once per port per session (standing rule 2). Done when the user has said to go ahead.
4. Run `idf.py -p <port> flash`. Done when it exits 0 and esptool reports the hash verified.
5. If the flash fails for a reason other than the code (`Failed to connect`, `Wrong boot mode detected`, a port that won't open, a write that stops part way):
   1. Read `${CLAUDE_PLUGIN_ROOT}/references/serial-ports.md` and `${CLAUDE_PLUGIN_ROOT}/references/download-mode.md`, and apply the case that matches the error.
   2. Retry the flash exactly once.
   3. If it fails again, stop and hand off to the `flashing-and-debugging` skill with the `doctor.py` output and the exact error text.

   Done when the retry succeeds, or the hand-off is made.
6. Ask the user to run `idf.py -p <port> monitor` (it runs until Ctrl+]) and report the screen and serial output. Read `${CLAUDE_SKILL_DIR}/references/sdkconfig.md` when serial shows nothing and step 2's `usb_bridge` reads `native USB`. Still nothing, garbage, a panic or repeated resets: hand off to the `flashing-and-debugging` skill. The program misbehaves: fix it here, handing M5Unified or M5GFX code to the `arduino-m5unified` skill. Done when the user reports the board doing what the program should.

## Hand-offs

- M5Unified / M5GFX API code → use the `arduino-m5unified` skill
- `platformio.ini`, and building and uploading a `framework = espidf` PlatformIO project → use the `platformio` skill
- an upload still failing after one retry, no port, drivers → use the `flashing-and-debugging` skill
- panics, backtraces, boot loops, brownout → use the `flashing-and-debugging` skill
- "which board or revision do I have?" → use the `board-identification` skill
- a question that is about pins → use the `pinout-lookup` skill
