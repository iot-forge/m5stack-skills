# m5core-skills

Claude Code skills for **M5Stack Core controllers**: Basic, Gray, Fire, M5GO, Core2, Core2 for AWS, Tough, CoreS3, CoreS3-SE and CoreS3-Lite. They cover four frameworks (Arduino with M5Unified/M5GFX, PlatformIO, ESP-IDF, and UIFlow2 MicroPython on the device) and three jobs that cut across them (identifying a board, looking up pins, flashing and debugging).

What makes it different: **boards are data, and revisions are real.** A "Core2" is four hardware revisions with different PMICs, IMUs, USB bridges and RTC backup cells, and the PMIC goes AXP192 → AXP2101 → AXP192 again. Every skill answers board questions from bundled per-revision data through one query script. Every fact cites its primary source and the date it was last checked. Where revisions disagree, a skill gives every branch and tells you the cheapest way to find out which one you have. It never trusts the board's own report of itself.

> **Status: 2.0.0, not yet verified on hardware.** All seven skills are written and pass the data, query and trigger checks, which need no board. No board has been run yet, so every skill is `unverified` and every fact comes from documentation (see [Verification](#verification)).

## Requirements

- **Claude Code.**
- **[uv](https://docs.astral.sh/uv/getting-started/installation/)** on your PATH. Every bundled script runs through `uv run`, so this is the one prerequisite no script can check for you. The scripts use only the Python standard library; uv supplies a Python if you don't have one.
- The toolchain for your framework (arduino-cli, PlatformIO, ESP-IDF, esptool/mpremote). The skills detect what's missing and tell you where to get it; they never install anything.

## Install

Install the whole plugin. A single skill folder copied on its own is **unsupported**: every skill reads the shared `data/` and `scripts/` at the plugin root and cannot reach them from anywhere else.

The plugin lives on the `m5core-skills-v2` branch of [`iot-forge/m5stack-skills`](https://github.com/iot-forge/m5stack-skills), so add that branch as a marketplace:

```
/plugin marketplace add iot-forge/m5stack-skills#m5core-skills-v2
/plugin install m5core-skills@m5core-skills
```

Updates arrive with each new version; [`CHANGELOG.md`](CHANGELOG.md) lists them. For development, load a clone for one session: `claude --plugin-dir <path-to-your-clone>`.

**Do not install alongside the `core` plugin from that repository's `main` branch** (`core@m5stack`). That is unsupported. Both plugins have Core2 skills whose descriptions compete for the same requests, and they answer board questions differently (`core` records one PMIC for every Core2). Pick one.

## The skills

| Skill | Use it for |
|---|---|
| `board-identification` | Which product and revision you have, what chips and memory it carries, comparing boards, choosing one |
| `pinout-lookup` | Which GPIO is free, taken or conflicting; what the Grove ports and M-Bus expose; who is on the I2C bus |
| `arduino-m5unified` | M5Unified/M5GFX code in any build system; arduino-cli builds and the FQBN for each revision |
| `platformio` | `platformio.ini` and the `pio` CLI |
| `esp-idf` | `idf.py` projects, sdkconfig, M5Unified or esp-bsp as components |
| `uiflow2-micropython` | Flashing the UIFlow2 image, getting a REPL, running and deploying with mpremote |
| `flashing-and-debugging` | Flashing a `.bin`, erasing, ports and drivers, download mode, decoding panics and boot loops |

You can also query the data directly:

```
uv run scripts/board.py facts "Core2" pmic imu
uv run scripts/board.py tell-apart "Core2"
uv run scripts/board.py pins "core2@v1.3" --use sd,speaker,mic
uv run scripts/board.py targets "K010-V13" --toolchain platformio
```

## Permissions

Each skill pre-approves its two read-only scripts, `board.py` and `doctor.py`, and reading the plugin's own reference files, for the turn the skill is invoked, so the first lookup runs without a prompt. On later turns Claude Code asks as usual. Approve them there: they only read.

Anything that writes to a board (flashing, erasing) always runs with the normal permission prompt, and the skills name the port, the board and what will be overwritten before asking.

We don't suggest a permanent allow rule. Claude Code's patterns accept a wildcard only at the end, and the plugin's install path includes its version, so any exact rule stops matching at the next update.

## The M5Stack MCP server

The plugin declares M5Stack's knowledge server (`m5stack`, `https://mcp.m5stack.com/mcp`), which starts with the plugin and is listed on the install screen. Skills use it only as a **secondary** source for general API questions and label what comes from it. Where it disagrees with the bundled data, the data wins and the disagreement is reported. Every skill works without it. Turn it off in `/mcp`.

## Alternatives

Other M5Stack skills exist. As of 2026-09-21 there were about fifteen sources; none modelled Core2 revisions correctly, which is why this one exists. A web search on 2026-10-04 turned up two more, listed last; neither tells Core2 revisions apart. The main ones:

- The `m5stack` marketplace on the [`main` branch of this repository](https://github.com/iot-forge/m5stack-skills): per-family plugins (`core`, `cardputer`, `esp32-chips`) from the same team. Don't install `core` together with this plugin (see above).
- M5Stack's official **uiflow2-coder** and **uiflow2-ui-designer** skills ([`m5stack/uiflow-micropython`, `tools/knowledge-base/`](https://github.com/m5stack/uiflow-micropython/tree/master/tools/knowledge-base)): the UIFlow2 API reference. This plugin's `uiflow2-micropython` skill points to uiflow2-coder for API detail.
- Anthropic's [`cwc-makers`](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/cwc-makers) plugin: a UIFlow2 flashing playbook.
- `m5stack-assistant` (yuyun2000, on ClawHub): the client for the same M5 knowledge server this plugin declares.
- Single-board skills: [`charlesliang924/m5stack-dev-skill`](https://github.com/charlesliang924/m5stack-dev-skill) (Arduino), [`fxp/m5stack-embedded-dev-skill`](https://github.com/fxp/m5stack-embedded-dev-skill), [`ishamehra/m5stack-uiflow-skill`](https://github.com/ishamehra/m5stack-uiflow-skill), [`grapeot/m5stack-sticks3-skill`](https://github.com/grapeot/m5stack-sticks3-skill), [`cguldogan/m5papercolor-skill`](https://github.com/cguldogan/m5papercolor-skill).
- Found 2026-10-04: [`Sunwood-ai-labs/m5stack-arduino-cli-skill`](https://github.com/Sunwood-ai-labs/m5stack-arduino-cli-skill), a Codex skill for arduino-cli on Windows with Core2 defaults, and the CoreS3 bring-up skill inside [`houxiaomu/m5stack-coding-toys`](https://github.com/houxiaomu/m5stack-coding-toys), which covers CoreS3 and CoreS3 SE only.

## Roadmap

Not in this version. Until each exists, its questions go to the skill named here.

| Later | Covers | Until then |
|---|---|---|
| `display-graphics` skill | M5GFX and LVGL in depth | `arduino-m5unified` for the display API |
| `power-and-battery` skill | the AXP192/AXP2101 PMIC split across Core2 revisions, battery and charging | `board-identification` for PMIC and battery facts |
| `units-and-peripherals` skill | a catalogue of Grove and M-Bus units | `pinout-lookup` for the port's pins; a unit's own wiring or driver is pointed at the `m5stack` MCP server |
| JTAG / OpenOCD debugging | on-chip debugging; only the ESP32-S3 boards have USB-JTAG built in, the ESP32 boards need an external probe | declined by `flashing-and-debugging` |
| CoreS3 Thread BR, Tab5 | boards whose data is a `roadmap` stub: a second radio SoC, and an ESP32-P4 | `board.py` refuses them and gives the reason |
| Other M5 families | Stick, Atom, Cardputer, Stamp, E-Paper and others; the data schema already accepts them | not covered |

Work still to do on v1 is in [`backlog/`](backlog/README.md).

## Verification

How the skills are checked against real hardware is in [`VERIFICATION.md`](VERIFICATION.md), which stands on its own.

| Revision | Last run | Toolchains | Result |
|---|---|---|---|
| — | none yet | — | every skill is `unverified`; every fact is `sourced` (documentation only) |

This table is regenerated from the latest report in `verification/runs/`. The latest, 2026-09-29, ran no board: its data, query and trigger checks passed, and its build checks were not run.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Terms are defined in [`CONTEXT.md`](CONTEXT.md), and design decisions are in [`docs/adr/`](docs/adr/).

## Licence

MIT, © 2026 IoT Forge. See [`LICENSE`](LICENSE) and [`ACKNOWLEDGEMENTS.md`](ACKNOWLEDGEMENTS.md).
