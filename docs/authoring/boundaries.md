# Skill boundaries

What each skill owns, where it stops, and what it uses. The job paragraph, description and hand-offs of each skill are in its own SKILL.md; this file holds the rules behind them, so an author can extend a skill without moving its boundary. Changing a boundary means changing every SKILL.md it touches and the trigger rows in `VERIFICATION.md` section 4.

## Contents

- [Boundary rules](#boundary-rules)
- [Shared procedures](#shared-procedures)
- [What each skill uses](#what-each-skill-uses)
- [Known trigger weak spots](#known-trigger-weak-spots)

## Boundary rules

These cut across all seven skills. Each SKILL.md applies them without restating them; its Hand-offs section is where they show.

1. **Upload belongs to the toolchain.** Each framework skill runs its own toolchain's normal upload: `arduino-cli upload`, `pio run -t upload`, `idf.py flash`, and `esptool write_flash 0x0` for a UIFlow2 image. `flashing-and-debugging` takes the toolchain-neutral cases: flashing a `.bin` with esptool directly, erasing, NVS erase, recovery, drivers and cables.
2. **A failed upload gets one retry.** A non-code upload failure means the framework skill reads `serial-ports.md` and `download-mode.md`, retries once, then hands off to `flashing-and-debugging`. From `doctor.py` output, a framework skill reports its own toolchain's gaps; drivers, ports and cables belong to `flashing-and-debugging`.
3. **Any skill looks up board facts itself.** Every skill runs `board.py` whenever it needs a fact, pins included. It hands off to `board-identification` or `pinout-lookup` only when **the user's question is** the board or the pinout. When revisions diverge, the skill passes on `board.py`'s branches and tell-apart line exactly as printed.
4. **The M5Unified/M5GFX API has one owner**: `arduino-m5unified`, whatever the build system. `platformio` owns `platformio.ini` and the `pio` CLI. `esp-idf` owns sdkconfig, components and `idf.py`. In a `framework = espidf` PlatformIO project, `platformio` owns the config and `esp-idf` owns the IDF concepts.
5. **Board level and pin level.** `board-identification` answers at board level: components, memory, features, comparisons, which board to buy. `pinout-lookup` answers at GPIO level: which pin, free, conflicting, connector exposure, shared-bus addresses. "Can I run a servo on Port B while using SD?" is a pin-level question.
6. **Framework skills send general questions elsewhere.** They keep only the M5-specific and version-specific parts: M5Unified init and config, the right build target per revision and a recommended target's gaps, pitfalls that differ between revisions, and versions read from the project. General framework questions go to the official docs, or to the `m5stack` MCP server with the answer labelled (standing rule 7).
7. **Debugging stops at the firmware boundary.** `flashing-and-debugging` covers the serial monitor when its output is wrong, panic and backtrace decoding, reset reasons, boot loops, brownout and USB enumeration. Bugs in the user's own code stay with the framework skill. A framework skill uses its own monitor to confirm success (standing rule 4), and hands off on garbage output, a panic or repeated resets.

## Shared procedures

Plugin-root `references/`, reached by `Read ${CLAUDE_PLUGIN_ROOT}/references/<file> when <condition>` at the step that needs it.

| File | Holds | Read by |
|---|---|---|
| `serial-ports.md` | Listing ports; recognising the USB bridge by VID (`0x1A86` CH9102, `0x10C4` CP210x, `0x303A` native USB); choosing a port; a busy port | the four framework skills, `flashing-and-debugging` |
| `download-mode.md` | Auto-reset through the USB bridge vs native USB; the manual RESET long-press on the native-USB boards (M5's procedure); leaving a manually entered download mode (`--after watchdog-reset`); the esptool options native USB needs, from Espressif's docs only | the four framework skills, `flashing-and-debugging` |
| `identifying-a-revision.md` | Why a board's self-report is not evidence (cached in NVS across reflashes, made up by a fallback on failure); walking the user through `tell-apart` and `--seen`, cheapest signal first | all seven |

## What each skill uses

`board.py` subcommands, what `doctor.py` must detect for the skill, shared procedures, and outside sources.

- **`arduino-m5unified`** (framework tier): `board.py facts`, `targets --toolchain arduino`, `frameworks`, `pins --use` (inline, rule 3); `doctor.py` (arduino-cli, the esp32 and m5stack cores); `serial-ports.md`, `download-mode.md`, `identifying-a-revision.md`; the `m5stack` MCP server for general API questions.
- **`platformio`** (framework tier): `board.py targets --toolchain platformio`, `facts` (flash, PSRAM), `frameworks`, `pins --use` (inline); `doctor.py` (pio); `serial-ports.md`, `download-mode.md`, `identifying-a-revision.md`.
- **`esp-idf`** (framework tier): `board.py facts` (soc, flash, PSRAM), `targets --toolchain esp-idf`, `frameworks`, `pins --use` (inline); `doctor.py` (`idf.py`, `IDF_PATH`); `serial-ports.md`, `download-mode.md`, `identifying-a-revision.md`.
- **`uiflow2-micropython`** (framework tier): `board.py targets --toolchain uiflow2`, `facts`, `pins --use` (inline); `doctor.py` (esptool, mpremote); `serial-ports.md`, `download-mode.md`, `identifying-a-revision.md`; `uiflow2-coder`, else the `m5stack` MCP server.
- **`board-identification`** (capability tier, the exemplar): `board.py list`, `find`, `facts`, `tell-apart`, `--seen`, `frameworks`; `identifying-a-revision.md`. There's no `doctor.py` step and no project detection (template "Start here" rule).
- **`pinout-lookup`** (capability tier): `board.py pins --use`, `pins --gpio`, `facts`, `--seen`; `identifying-a-revision.md` when `pins` refuses because the revisions in play have different pin maps. There's no `doctor.py` step and no project detection.
- **`flashing-and-debugging`** (capability tier): `doctor.py` (serial ports with VID/PID, drivers, esptool, decoder tools); `board.py facts` (USB bridge, flash size, SoC); `serial-ports.md`, `download-mode.md`, `identifying-a-revision.md`. Every write goes through standing rule 2.

## Known trigger weak spots

Accepted when the skills' scope was settled, and listed here so verification tests them rather than rediscovering them.

- **`main.py` is a generic filename.** `uiflow2-micropython` names `boot.py` / `main.py` as project files, and `main.py` exists in countless plain-Python projects. The description's `M5Stack Core` opening is expected to hold it back outside M5 work, but that is untested. If it misfires, narrow the trigger to `boot.py` plus a UIFlow2 import (`import M5`) rather than dropping the file signal.
- **Row 11 can fire `arduino-m5unified`**, because the request mentions `M5.getBoard()`. That's acceptable: standing rule 1 and `identifying-a-revision.md` give the same answer from either skill.
- **`uiflow2-coder` can't appear in a deferral clause**, because CI requires the clause to name a sibling skill. The pointer to it lives in the `uiflow2-micropython` body.
