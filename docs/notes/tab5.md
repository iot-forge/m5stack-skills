# tab5 — build notes

Last verified: 2026-08-17
Sources:
- https://docs.m5stack.com/en/core/Tab5 (official product page)
- https://docs.m5stack.com/en/arduino/m5tab5/program, /wifi, /imu, /power, /microsd (official per-peripheral Arduino docs)
- https://docs.m5stack.com/en/esp_idf/m5tab5/userdemo (official ESP-IDF factory firmware guide)
- https://docs.m5stack.com/en/uiflow2/Tab5/program (official UIFlow2 flashing guide)
- https://docs.m5stack.com/en/arduino/arduino_board (board manager URL)
- https://shop.m5stack.com/products/m5stack-tab5-iot-development-kit-esp32-p4 (product page specs)
- https://shop.m5stack.com/blogs/news/m5stack-unveils-tab5-... (launch announcement)
- https://components.espressif.com/components/espressif/m5stack_tab5 (official Espressif BSP component readme)
- https://github.com/m5stack/M5Tab5-UserDemo (factory firmware source repo)
- https://github.com/XueshiQiao/M5Dashboard/blob/main/docs/M5Stack-Tab5-Reference.md (third-party pinout reference, cross-checked against official sources)
- https://esp-cpp.github.io/espp/m5stack_tab5.html (espp community BSP docs, cross-checked)
- https://www.cnx-software.com/2025/05/14/... and /05/18/... (CNX Software two-part hands-on review: teardown + firmware bring-up)

## Confidence / soft spots

- **CPU clock speed**: sources disagree. M5Stack's own boot-log output and
  Arduino IDE default config (per CNX Software's hands-on) show **360MHz**;
  M5Stack's launch blog post and one shop-page fetch said 400MHz (ESP32-P4
  silicon's rated max). Documented as 360MHz-as-shipped-default in the
  skill, with the discrepancy flagged. Worth re-checking if the user
  reports a different value from `esp_clk_cpu_freq()`.
- **Display/touch driver revision**: two different chip sets exist across
  production (GT911+ILI9881C, I2C 0x14, targeted by the official Espressif
  BSP component as of v1.0.0 — vs. current-production ST7123/ST7121
  integrated display+touch, I2C 0x55). This is inferred from the official
  BSP targeting GT911/ILI9881C while other/newer community sources
  describe ST7123/ST7121 as current production. Not independently confirmed
  against an M5Stack changelog or revision announcement — flagged as
  "current production" based on source recency, not a dated cutover point.
  If a future session can find an official M5Stack revision announcement,
  update this with dates/serial ranges.
- **IO expander bit/pin-level mapping** (which of the 8 pins on each
  PI4IOE5V6408 maps to which function): came from a third-party pinout
  reference (XueshiQiao/M5Dashboard) and an espp community doc, not from
  M5Stack's own schematic text extraction (schematic is a PDF, not fetched
  page-by-page this pass). The functions themselves (antenna switch,
  speaker enable, resets, C6 power, USB-A 5V, charge control) are
  corroborated across both third-party sources, but exact bit numbers
  weren't independently verified against the schematic PDF. Flagged in
  pinout.md as needing schematic verification before writing raw register
  code against them.
- **M5-Bus / GPIO_EXT exact pin roster**: not found broken out anywhere
  consulted this pass beyond "Grove HY2.0-4P = G53/G54." The schematic PDF
  (linked in SKILL.md) almost certainly has this; wasn't opened/parsed this
  pass since it's a PDF and the text sources available were sufficient for
  everything else. Worth a follow-up pass if a user asks for exact M5-Bus
  pin assignments.
- **SDIO-mode microSD pin roles**: only the SPI-mode pinout (CS/SCK/MOSI/
  MISO) is confirmed from official Arduino example code. A first-pass
  fetch mentioned "SDIO mode pins G39-G44" without a per-signal breakdown;
  documented as-is in pinout.md rather than guessing which pin is CLK vs
  CMD vs D0-D3 in SDIO mode.
- **RS485 supply voltage (6-24V)**: from a third-party source, not
  independently confirmed against M5Stack's own RS485 port spec page.

## Open questions

- Exact production-date/serial cutover between the GT911+ILI9881C and
  ST7123/ST7121 hardware revisions.
- IO expander bit-level pin map, verified against the schematic PDF rather
  than third-party reverse-engineering docs.
- Full M5-Bus and GPIO_EXT pin assignment tables.
- Whether a newer BSP component version (> 1.0.0) has since added GPIO
  button / rotary knob / LED / battery-monitor / IMU support that v1.0.0
  lacked at last check.
- PlatformIO `platform-espressif32` version that first added solid ESP32-P4
  support, so a specific version pin can be recommended instead of "check
  it supports P4."
