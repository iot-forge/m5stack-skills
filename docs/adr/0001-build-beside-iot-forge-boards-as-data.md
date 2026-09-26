---
status: accepted
date: 2026-09-21
---

# Build a second M5Stack plugin beside iot-forge/m5stack-skills, with boards as data

The team already publishes [`iot-forge/m5stack-skills`](https://github.com/iot-forge/m5stack-skills), which has one skill per board family, board facts written as prose tables, and no revision axis. It states that every Core2 has an AXP192 PMIC. In fact Core2 v1.0 has an AXP192, v1.1 an AXP2101, and v1.3 goes back to an AXP192, a non-linear progression that no existing M5Stack skill models (as of 2026-09-21). We build a separate plugin instead of rewriting or evolving that one. Its skills are per-framework (Arduino + M5Unified, PlatformIO, ESP-IDF, UIFlow2/MicroPython) and per-capability. They all read one shared board dataset through a query script, and every fact in that dataset records its primary source and a `last_verified` date. Installing both plugins together is unsupported.

## Considered options

- **Adopt an existing third-party skill as a base.** Rejected: of about 15 M5Stack skill sources, none is structured as boards-as-data, none models revisions correctly, and all are single-author and mostly dormant.
- **Defer a framework to an existing skill** (e.g. hand UIFlow2 to another repo). Rejected: it breaks cross-framework revision identity, which is the plugin's reason to exist. The UIFlow2 skill still points to M5Stack's official `uiflow2-coder` for API detail. It owns the workflow, not the API reference.
- **Evolve iot-forge in place.** Rejected: its per-board architecture is exactly what is being replaced, and changing it would break its existing users.

## Consequences

- Two M5Stack plugins from one team, with different answers on Core2. The README states the relationship and that installing both is unsupported.
- Plugin and skill names must not collide with iot-forge's (`core`, `cardputer`, `esp32-chips`).
- Ideas from other skills are absorbed and credited in `ACKNOWLEDGEMENTS.md`. Facts are cited only from primary sources. Nothing is copied verbatim, including from iot-forge.
