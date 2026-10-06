# Changelog

One entry per released version, newest first. A release is the tag `m5core-skills--v<version>` on the `m5core-skills-v2` branch.

## 2.0.0

The first release. It is numbered 2 as the second generation of IoT Forge's M5Stack skills; the first is the per-family plugins on this repository's `main` branch.

- Seven skills: `board-identification`, `pinout-lookup`, `arduino-m5unified`, `platformio`, `esp-idf`, `uiflow2-micropython` and `flashing-and-debugging`.
- Per-revision board data for Basic, Gray, Fire, M5GO, Core2, Core2 for AWS, Tough, CoreS3, CoreS3-SE, CoreS3-Lite and Tab5. Every fact cites a primary source.
- Tab5 is the first ESP32-P4 board: three revisions by display and touch generation, the chip-revision choice an ESP-IDF build has to make, RISC-V crash decoding, and M5's own download-mode procedure. PlatformIO has no Tab5 target; the data gives M5's pioarduino example instead.
- Checked on hardware on one unit, a Tab5 (`tab5@2026.04`), in Arduino and ESP-IDF. `board-identification`, `arduino-m5unified`, `esp-idf` and `flashing-and-debugging` are `partial` on that revision; `pinout-lookup`, `platformio` and `uiflow2-micropython` are `unverified`.
