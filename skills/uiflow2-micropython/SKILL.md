---
name: uiflow2-micropython
description: M5Stack Core boards running UIFlow2 MicroPython — picks and flashes the right UIFlow2 firmware image, gets past the launcher to a REPL, and runs and deploys scripts with mpremote. Use when the project has boot.py or main.py, or the user mentions UIFlow2, MicroPython, mpremote or a REPL on a Core board. Not for flashing any other firmware image — use flashing-and-debugging.
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

# UIFlow2 MicroPython on M5Stack Core

Runs the whole UIFlow2 MicroPython loop on M5Stack Core boards. It picks the release image for the revision, flashes it with `esptool write_flash 0x0`, gets past the launcher to a REPL, then runs and deploys scripts with `mpremote`. For UIFlow2 API detail it points to M5Stack's `uiflow2-coder` skill, or to the `m5stack` MCP server when that skill isn't installed. It writes no API reference of its own.

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
- [ ] Detect the project: boot.py or main.py that imports M5
```

## Pick and flash the UIFlow2 image

1. On a Core board, "MicroPython" means UIFlow2: offer it. Hand off to the `flashing-and-debugging` skill only when the user wants another image (micropython.org's, their own `.bin`). Done when `doctor.py` finds esptool; if not, tell the user how to get it and stop.
2. Run `board.py targets "<user's words>" --toolchain uiflow2`; pass on its `covers only`, `Recommended` and `Gaps` text as printed. Revisions in play needing different images: run `board.py tell-apart "<user's words>"`, ask for the cheapest observation and re-run `targets` with `--seen`; read `${CLAUDE_PLUGIN_ROOT}/references/identifying-a-revision.md` when only host or probe signals remain. Never pick the likelier image. A `Gaps` line: pass it on and wait for the go-ahead (Core2 v1.3 on the Core2 image *(untested on hardware: open-question.uiflow2-image-v1.3.core2@v1.3)*, CoreS3-Lite on the CoreS3 image *(untested on hardware: open-question.lite-image.cores3-lite@v1.0)*). Done when one image id remains and the user has accepted its gaps.
3. Read `${CLAUDE_SKILL_DIR}/references/images.md` and download the file for that id, from a release no older than the output allows ("use <version> or later"). Done when the file is on disk at the asset's size.
4. Run `doctor.py --ports` and `board.py facts "<user's words>" usb_bridge`. Read `${CLAUDE_PLUGIN_ROOT}/references/serial-ports.md` unless exactly one port has a `<-` marker that fits that bridge. No port: hand off to the `flashing-and-debugging` skill with what `doctor.py` found. Done when one port is named, or the hand-off is made.
5. Name the port, the board and what the write destroys: the image, written at `0x0`, replaces the firmware, every file on the device and the saved Wi-Fi settings. It deletes files on the device, so confirm every time (standing rule 2). Done when the user has said to go ahead.
6. Run `esptool --port <port> write-flash 0x0 <file>` (esptool v4, `esptool.py`: `write_flash`). Done when it exits 0 and esptool reports the hash verified.
7. If the flash fails for a reason other than the file (`Failed to connect`, `Wrong boot mode detected`, a port that won't open, a write that stops part way):
   1. Read `${CLAUDE_PLUGIN_ROOT}/references/serial-ports.md` and `${CLAUDE_PLUGIN_ROOT}/references/download-mode.md`, and apply the case that matches the error.
   2. Retry the flash exactly once.
   3. If it fails again, stop and hand off to the `flashing-and-debugging` skill with the `doctor.py` output and the exact error text.

   Done when the retry succeeds, or the hand-off is made.
8. Ask the user what the screen shows: after a flash, UIFlow2's boot screen, then the launcher. A blank screen, garbage or repeated resets: hand off to the `flashing-and-debugging` skill. Done when the user reports the launcher.

## Get a REPL past the launcher

1. Read `doctor.py`'s `mpremote` line. Missing: the user installs it (`pipx install mpremote`). Done when it is found.
2. Use the flash's port, or find one as in its step 4. Run `mpremote connect <port> resume exec "import sys; print(sys.implementation)"`. Its Ctrl-C stops the launcher, and `resume` stops mpremote soft-resetting the board, which would restart it *(untested on hardware: open-question.mpremote-launcher.core2@v1.3)*. Put `resume` straight after the port in every mpremote command. Done when it prints `(name='micropython', …)`.
3. If an mpremote command fails for a reason other than the script (the port won't open, `could not enter raw repl`, no response):
   1. Read `${CLAUDE_SKILL_DIR}/references/boot-option.md` and work through its "mpremote can't reach a REPL" list. At its port step, read `${CLAUDE_PLUGIN_ROOT}/references/serial-ports.md` and `${CLAUDE_PLUGIN_ROOT}/references/download-mode.md` (a board left in download mode runs no MicroPython).
   2. Retry the command exactly once.
   3. If it fails again, hand off to the `flashing-and-debugging` skill with the `doctor.py` output and the exact error text. On a CoreS3-SE (`board.py find` names `cores3-se`), where a third-party report says mpremote fails, give the user the full command and output too *(untested on hardware: open-question.mpremote.cores3-se@v1.0)*.

   Done when the retry succeeds, or the hand-off is made.
4. For an interactive prompt, the user runs `mpremote connect <port> repl` in their own terminal and presses Ctrl-C to stop the launcher; Ctrl-] leaves it. Done when the user reports a `>>>` prompt.

## Run and deploy scripts with mpremote

1. Work on the project's `main.py`. UIFlow2 API code: M5Stack's `uiflow2-coder` skill if installed, else the `m5stack` MCP server, labelled (standing rule 7). A GPIO in the script comes from `board.py pins "<user's words>" --use <features>`. Done when the script is written.
2. Run it without saving: `mpremote connect <port> resume run main.py`. It prints the script's output until the script ends *(untested on hardware: open-question.stdout-raw-repl.core2@v1.3)*. For a script that never ends, use `run --no-follow main.py` and rely on the screen. A traceback: fix the script here. Done when the output, and the screen as the user reports it, show what the script should.
3. To keep it on the board, run `mpremote connect <port> resume fs ls :`. Name the port, the board and the files the copy writes, marking those it overwrites (a new `boot.py` removes the launcher), and wait for the go-ahead, every time. Then run `mpremote connect <port> resume fs cp main.py :main.py` (`fs cp -r <folder> :` for a folder). Done when `fs ls :` lists each file at its local size.
4. `main.py` runs at power-up only with boot option `0` or `2`; the default, `1`, shows the launcher. Read "Changing the boot option" in `${CLAUDE_SKILL_DIR}/references/boot-option.md` when the user wants it at power-up; it is a write to the board. Done when its check prints the new option.
5. Run `mpremote connect <port> resume reset` and ask the user what the board does; with boot option `1`, the launcher's Run app starts `main.py`. A traceback: fix it here. A panic or repeated resets: hand off to the `flashing-and-debugging` skill. Done when the user reports the program running.

An mpremote failure here that isn't the script's: the REPL section's step 3.

## Hand-offs

- UIFlow2 API reference → M5Stack's uiflow2-coder skill if it is installed, else the `m5stack` MCP server with the answer labelled (standing rule 7)
- flashing an image other than UIFlow2 → use the `flashing-and-debugging` skill
- no port, drivers, or a flash that still fails after the download-mode procedure → use the `flashing-and-debugging` skill
- a firmware-level panic or boot loop, as opposed to a Python traceback → use the `flashing-and-debugging` skill
- "which board or revision do I have?" → use the `board-identification` skill
- a question that is about pins → use the `pinout-lookup` skill
