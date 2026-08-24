# esp32 (classic) — build notes

Last verified: 2026-08-24 (initial build 2026-08-17; 2026-08-24 pass
expanded `references/peripherals.md`'s I2S section with three items —
PDM RX being I2S_NUM_0-only, APLL required for the 44.1kHz sample-rate
family, and `auto_clear = true` clearing DMA buffers but not the
peripheral's internal FIFO — sourced from a user's Core2 ESP-IDF audio
bring-up session, see soft spots)
Sources:
- Espressif ESP32 Series datasheet (v5.3, PDF): https://documentation.espressif.com/esp32_datasheet_en.pdf
- Espressif ESP32 Chip Revision v3.0 User Guide (PDF): https://documentation.espressif.com/esp32_chip_revision_v3_0_user_guide_en.pdf
- Third-party mirror of the ESP32-D0WDQ6-V3-specific datasheet page (used to
  confirm package size / no-in-package-memory / operating temp range /
  SDMMC+SDIO-slave peripheral presence, cross-checked against the official
  PDF above): https://live-final.oss-us-west-1.aliyuncs.com/851977/ESP32D0WDQ6V3.pdf
- ESP-IDF docs (esp32 target) — ADC driver (ADC2/WiFi conflict), SDMMC host
  driver, SDIO slave driver: https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/
- ESP32-WROOM-32 module datasheet: https://documentation.espressif.com/esp32-wroom-32_datasheet_en.html
- Community/forum confirmation of Hall sensor deprecation in ESP-IDF 5.0+
  (esp32.com forum threads, Tasmota/ESPHome issue trackers) — official
  removal is also referenced in ESP-IDF's own 5.0 migration guide.
- Espressif esp-hosted project docs (SDIO slave / ESP32-as-radio-coprocessor
  pattern): https://github.com/espressif/esp-hosted-mcu

## Confidence / soft spots

- Core numbers (CPU/ROM/SRAM/RTC memory, GPIO count, wireless specs, power
  modes, package/temp range) came from Espressif's own datasheet and chip
  revision errata guide — high confidence.
- MCPWM unit/timer count (2 units × 3 timers/6 outputs) is standard
  ESP32-family knowledge cross-referenced against the datasheet's brief
  peripheral list, not independently re-verified line-by-line against the
  full register-level TRM — flag if a user hits a contradiction.
- Strapping pin list (GPIO0/2/5/12/15, five pins) matches the datasheet's
  own "five strapping GPIOs" count; some third-party tutorials also list
  GPIO4 as a strapping pin, which the official datasheet does not confirm
  for this die — went with the datasheet's five.
- The Controller-family "which M5Stack boards use this chip" list is
  carried over from `docs/catalog/chips.md` and is **not independently
  verified per board** — same caveat that file already documents.
  WROOM-vs-WROVER (and therefore D0WDQ6-vs-D0WDR2) mapping per board is an
  inference from "does this board advertise PSRAM," not confirmed against
  each board's actual schematic.
- SDIO slave section is real (ESP-IDF ships a documented SDIO slave driver
  for this chip) but M5Stack's actual use of it (if any) is unconfirmed —
  included as chip-capability context, not a claim about any specific
  M5Stack product using it.
- **The three 2026-08-24 I2S subsections are single-session-sourced** from
  the same user's Core2 ESP-IDF audio bring-up that produced the Core2
  skill's audio section (see `docs/notes/core2.md`). Each is
  chip-family-plausible — PDM RX being I2S_NUM_0-only is longstanding
  classic-ESP32 folklore; APLL for 44.1kHz is a known consequence of
  PLL_F160M's divisor structure; the `auto_clear`-vs-FIFO distinction
  matches how the ESP-IDF I2S driver is structured (driver-owned DMA
  memory vs. peripheral-internal FIFO). None re-verified this pass against
  Espressif's I2S driver source or TRM. Confirming each against
  Espressif's own docs would let the "Observed across current ESP-IDF
  v5.x" hedge be dropped.

## Open questions

- Per-board flash size (4/8/16MB) and exact module part number (WROOM-32
  vs -32D vs -32U vs -32E; WROVER vs -32E vs -32IE) for each M5Stack
  Controller in the "which boards use this chip" list — needs each board's
  own Controller-skill research pass to confirm rather than guessing from
  product naming.
- Whether any current M5Stack board pairs classic ESP32 with anything
  besides WROOM/WROVER modules (e.g. a bare-die custom design) — none
  known at time of writing, flag if one turns up.
- Exact hibernation-mode current draw and full RTC-GPIO wake-source list
  for hibernation specifically (vs. full deep-sleep) — datasheet has this
  in its power tables but wasn't transcribed verbatim into the skill since
  exact µA figures drift by exactly which peripherals are left enabled;
  pointed users at the datasheet directly instead.
- Whether ESP-IDF v5.x actually restricts PDM RX to I2S_NUM_0 on classic
  ESP32 by driver check, by hardware limitation, or by both. Stated as a
  restriction in the 2026-08-24 I2S subsection from field observation;
  Espressif's I2S driver source / TRM should say which layer enforces it.
- Whether `auto_clear`'s DMA-only behavior is documented in ESP-IDF's I2S
  driver docs or is purely a driver-implementation detail — worth a docs
  pass so the section can cite the doc rather than "observed in v5.x."
