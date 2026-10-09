# esp32 (classic) — build notes

Last verified: 2026-08-24 (initial build 2026-08-17; 2026-08-24 first
pass added three chip-level I2S subsections — PDM RX being I2S_NUM_0-only,
APLL required for 44.1 kHz sample-rate family, and `auto_clear = true`
clearing DMA buffers but not the peripheral's internal FIFO — from a
Core2 audio bring-up; 2026-08-24 second pass added a fourth subsection
covering the classic-ESP32-only 8/16-bit MONO STD pair-swap quirk,
with a direct quote from ESP-IDF v6.0.2's I2S API reference and a
worked pre-swap fix example, alongside the note that PDM RX does not
have the swap; 2026-08-24 third pass narrowed the APLL-for-44.1-kHz
subsection to STD-mode audio out specifically and added an "APLL vs
PLL_160M choice for I2S" subsection stating the empirical rule that
PDM RX often works better with `PLL_160M`, citing M5Unified's
`Mic_Class.cpp` as the reference implementation)
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

- **"Frame buffers and DMA" (2026-10-09, `references/memory-radio.md`)**:
  the DMA-can't-read-PSRAM rule is quoted from ESP-IDF's heap-allocation
  docs (`MALLOC_CAP_DMA` "excludes any external PSRAM"). The fps figures
  come from one Core2 in one user session and are labelled that way inline.

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
- **The 2026-08-24 I2S subsections have mixed sourcing:**
  - **8/16-bit MONO STD pair-swap** (added in the second pass) is
    directly quoted from ESP-IDF v6.0.2's I2S API reference
    (`docs/en/api-reference/peripherals/i2s.rst`, `.only:: esp32` STD
    TX and RX subsections) with the ESP32-specific sample-transposition
    table cited. Highest confidence of the four. The main risk is that
    Espressif has been rewording driver docs across v5→v6; re-check the
    paragraph if the docs URL 404s or the wording changes materially.
  - **PDM RX only on I2S_NUM_0** is longstanding classic-ESP32 folklore
    and consistent with the M5Stack reference driver's use of
    `I2S_NUM_0` for the SPM1423, but not re-verified against the TRM
    this pass. If Espressif documents this restriction anywhere in the
    I2S driver reference, a citation would be worth adding.
  - **APLL for 44.1 kHz** is a known consequence of PLL_F160M's
    divisor structure; matches Espressif's clock-source guidance in
    the I2S driver docs but not quoted directly.
  - **`auto_clear` vs peripheral FIFO** matches the ESP-IDF I2S
    driver's structural split between driver-owned DMA memory and
    peripheral-internal FIFO, and was reproducible in field bring-up.
    Not documented as such in ESP-IDF; still hedged as "observed
    across current ESP-IDF v5.x."
  - **APLL-for-STD-TX / PLL_160M-for-PDM-RX rule of thumb** (added
    third pass) is sourced from M5Unified's `src/utility/Mic_Class.cpp`
    — M5Stack's own library, which has to work across their whole
    classic-ESP32 lineup, ships `PLL_160M` + `mclk_multiple = 128` for
    PDM RX. That's a strong empirical signal but not a chip-level
    mechanism explanation; the subsection deliberately frames it as
    empirical rather than trying to derive from clock-tree math (which
    would suggest APLL is always cleaner — and it isn't, for this
    path). Espressif's own I2S driver docs don't spell this out;
    stating anything more concrete would need TRM-level analysis of
    how the PDM downsampler interacts with the two clock sources.

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
