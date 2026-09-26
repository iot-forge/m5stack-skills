# Acknowledgements

This plugin takes ideas from other M5Stack and embedded skill collections. It copies no text or code from any of them, and none of them is ever the cited source of a board fact. A fact they pointed us to was checked against a primary source (M5Stack's docs and schematics, `boards.txt`, M5Unified/M5GFX source, the board-ID registry, a datasheet), and that primary source is what `data/sources.json` cites. They are credited here for the ideas and the leads.

| Project | What we took from it |
|---|---|
| [`iot-forge/m5stack-skills`](https://github.com/iot-forge/m5stack-skills) | The CI ideas that every referenced path must resolve and that versions must be bumped, reimplemented rather than copied. The marketplace layout. The USB bridge chip as a revision hint. The rule that M5Unified detects the board at runtime while ESP-IDF must ask. |
| [`fxp/m5stack-embedded-dev-skill`](https://github.com/fxp/m5stack-embedded-dev-skill) | Per-file provenance in the style of its `SOURCES.md`. Its evals task format. Pin safety rules split by chip generation. Its open issue, as a warning that evals must reject spoofed passes. |
| [`cwc-makers`](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/cwc-makers) (Anthropic) | The shape of the UIFlow2 flashing playbook: detecting the USB vendor ID, native-USB esptool settings, no software path into download mode on native-USB ESP32-S3 boards, and identifying a board from I2C signatures. |
| [`charlesliang924/m5stack-dev-skill`](https://github.com/charlesliang924/m5stack-dev-skill) | Its board-ID table, as a lead checked against `boards.txt`. A provenance line with a live-refresh command. Refusing SKUs that don't exist. Pinning tested toolchain versions in skill metadata. |
| [`grapeot/m5stack-sticks3-skill`](https://github.com/grapeot/m5stack-sticks3-skill), [`cguldogan/m5papercolor-skill`](https://github.com/cguldogan/m5papercolor-skill) | Grading claims in three tiers (the verification tiers in `VERIFICATION.md`), marking what was and wasn't verified, and tables of acceptance criteria. |
| `m5stack-assistant` (yuyun2000) and M5Stack's knowledge server | The idea of a knowledge service behind the skills, and its retrieval strategy. The server is declared, not vendored. |
