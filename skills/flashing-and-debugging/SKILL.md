---
name: flashing-and-debugging
description: M5Stack Core flashing, recovery and crash diagnosis — flashes .bin images with esptool, erases flash and NVS, fixes serial ports, drivers and download mode, and decodes panics, backtraces, boot loops and brownout resets. Use when an upload keeps failing ("Failed to connect", "No serial data received"), no serial port appears, the monitor shows a Guru Meditation Error or repeated resets, or the user has a .bin to flash. Not for UIFlow2 firmware — use uiflow2-micropython.
license: MIT
allowed-tools:
  - Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/board.py" *)
  - Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py" *)
  - Read(${CLAUDE_PLUGIN_ROOT}/references/**)
  - Read(${CLAUDE_SKILL_DIR}/references/**)
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
- [ ] Detect the project: a .bin to flash, or serial output showing a panic, backtrace or reset loop
```

## Flash a .bin with esptool

1. Read `doctor.py`'s `esptool` line. Missing: tell the user how to get it and stop. Version 5 is `esptool` with hyphens (`write-flash`); version 4 is `esptool.py` with underscores (`write_flash`). Use the installed spelling below, and put global options (`--port`, `-b`, `--after`) before the command name. Done when esptool is found.
2. Take each file's offset from where the file came from, never from a guess. A merged image from `esptool merge-bin` goes at `0x0`. For several files, take the offset and file pairs from their release notes, an ESP-IDF build's `build/flash_args`, or the toolchain's verbose upload. A UIFlow2 image goes to `uiflow2-micropython`; an app from the user's own project, to its framework skill. Nothing gives the offset: ask. Done when every file has an offset with a named source.
3. Run `doctor.py --ports` and `board.py facts "<user's words>" usb_bridge soc_part flash`. Read `${CLAUDE_PLUGIN_ROOT}/references/serial-ports.md` unless exactly one port has a `<-` marker that fits that bridge. No port: use the Fix section. Done when one port is named.
4. Run `esptool --port <port> flash-id`: read-only, but it resets the board. On a USB-bridge board, esptool enters download mode by itself *(untested on hardware: open-question.auto-download.core2@v1.3)*. A chip family (ESP32, ESP32-S3) unlike `soc_part`'s: another board or port; stop and ask. Where `flash` diverges, re-run `facts` with `--seen flash-size=<n>MB`. Read `${CLAUDE_PLUGIN_ROOT}/references/identifying-a-revision.md` when the user offers the board's own report as evidence. Fails: the Fix section. Done when the chip and flash size fit a revision in play.
5. Name the port, the board, and each file's range (offset to offset plus size), all of which is replaced. An app, or an image at `0x0`, is a routine flash: confirm once per port per session. A bootloader or partition table without its app: confirm every time. Done when the user has said to go ahead, or already has for a routine flash on this port.
6. Run `esptool --port <port> write-flash <offset> <file> [<offset> <file> ...]`. If the board went into download mode by hand, run `esptool --port <port> --after watchdog-reset write-flash ...` instead. If esptool stops because the image doesn't suit the chip, the image is for another chip: never add `--force`. Done when it exits 0 and esptool reports the hash verified.
7. A failure while connecting or part way through: apply the Fix section, then retry once. Done when the retry succeeds or the user has the Fix section's report.
8. Ask the user what the screen and serial output show (standing rule 4). A panic or repeated resets: use the Decode section. Done when the user reports the new firmware running.

## Erase flash or NVS

1. Ask what the erase should fix. An NVS erase clears saved settings (Wi-Fi credentials, preferences) and keeps the firmware; a full erase also removes firmware and files, leaving nothing to run until the next flash. Suggest NVS when settings are the problem. Done when the user has picked one.
2. Check esptool, choose the port and check the chip, as in the flash section's steps 1, 3 and 4. Done when `flash-id`'s chip and flash size fit a revision in play.
3. NVS: read `${CLAUDE_SKILL_DIR}/references/finding-nvs.md`. Done when you have its offset and size in hex bytes from the board's partition table, or have offered a full erase instead.
4. Name the port, the board and what is destroyed (for NVS, offset to offset plus size). Confirm every time. Done when the user has said to go ahead with this erase.
5. Run `esptool --port <port> erase-region <offset> <size>` or `esptool --port <port> erase-flash`. Done when it exits 0.
6. After a full erase the board needs firmware: the flash section, or the framework skill's upload. After an NVS erase, ask the user what the board does now. Done when the user reports it.

## Fix ports, drivers and download mode

1. Take the `doctor.py` output and exact error text from the framework skill's hand-off, or run `doctor.py` and ask for the error. Run `board.py facts "<user's words>" usb_bridge`. Done when you have all three.
2. No port: read `${CLAUDE_PLUGIN_ROOT}/references/serial-ports.md` and apply its "None" case. If `usb_bridge` reads `native USB`, read `${CLAUDE_PLUGIN_ROOT}/references/download-mode.md` and walk the user through entering download mode by hand *(untested on hardware: open-question.manual-download.cores3@v1.0)* *(untested on hardware: open-question.manual-download.cores3-se@v1.0)*. Done when `doctor.py --ports` lists a port that fits the bridge, or the user has the report.
3. A `driver problem` line, or a `driver:` link under the port: the user installs the driver from that link and replugs the board (standing rule 5). Done when a fresh `doctor.py --ports` shows the port's driver as ok.
4. The port is listed but esptool can't connect, or a write stops part way through. Read `${CLAUDE_PLUGIN_ROOT}/references/serial-ports.md` ("A port that won't open") and `${CLAUDE_PLUGIN_ROOT}/references/download-mode.md`, and apply the case that matches the error. Then read `${CLAUDE_SKILL_DIR}/references/no-connection.md` and work through it. Done when `esptool --port <port> flash-id` names the chip, or the user has the report.
5. Once `flash-id` works, a project's upload goes back to its framework skill; a `.bin` or an erase resumes at its confirmation step. A native-USB board that loses its port after every reset runs firmware that turns USB off: enter download mode by hand, run a full erase through the Erase section, and the framework skill fixes the app. Done when the user knows where to go next.

## Decode panics, backtraces and reset loops

1. Take the serial output the user pasted, or ask for it: unedited, from one `rst:` line to the next, with any `ELF file SHA256:` line. Run `board.py facts "<user's words>" soc_part psram flash`; if the user named no board, ask which. Done when you have both.
2. Read `${CLAUDE_SKILL_DIR}/references/decoding-crashes.md` when you have both, and work the case that matches the output. Done when the user has the decoded frames or the named cause, and a fault in their own code has gone to the framework skill.

## Hand-offs

- UIFlow2 firmware and REPL → use the `uiflow2-micropython` skill
- a project's normal build and upload → use the framework skill for the project (`arduino-m5unified`, `platformio`, `esp-idf` or `uiflow2-micropython`)
- bugs in the user's own code → use the framework skill for the project (`arduino-m5unified`, `platformio`, `esp-idf` or `uiflow2-micropython`)
- "which board or revision do I have?" → use the `board-identification` skill
- JTAG / OpenOCD → declined: not covered in this version of the plugin
