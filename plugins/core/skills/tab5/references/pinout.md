# M5Stack Tab5 — pinout & address reference

Main SoC is ESP32-P4NRW32 (RISC-V). GPIO numbers below are ESP32-P4 GPIOs
unless noted otherwise. Sourced from M5Stack's official per-peripheral
Arduino docs (docs.m5stack.com/en/arduino/m5tab5/...), the official
Espressif `m5stack_tab5` BSP component, and community pinout references
cross-checked against each other. Where a value below is flagged as
lower-confidence, verify against the schematic PDF linked in SKILL.md.

## I2C system bus (shared)

| Signal | GPIO |
|---|---|
| SDA | G31 |
| SCL | G32 |
| Frequency | 100kHz (default) |

Touch controller, camera control, both audio codecs, IMU, RTC, power
monitor, and both IO expanders all sit on this one bus. A bus-level problem
(init order, missing pull-ups, wrong `Wire.begin()` pins) breaks everything
at once; a single wrong address only breaks one peripheral.

### I2C address table

| Device | Address | Notes |
|---|---|---|
| GT911 touch controller | 0x14 | early-production revision — see SKILL.md "Hardware revisions" |
| ST7123 display+touch (integrated) | 0x55 | current-production revision |
| ES8388 audio codec | 0x10 | speaker + headphone output |
| ES7210 AEC front-end | 0x40 | dual mic array |
| RX8130CE RTC | 0x32 | |
| BMI270 IMU | 0x68 | |
| INA226 power monitor | 0x41 | bus voltage/current |
| IO expander #1 (PI4IOE5V6408) | 0x43 | antenna switch, speaker enable, ext. 5V bus, display/touch/camera resets |
| IO expander #2 (PI4IOE5V6408) | 0x44 | ESP32-C6 power, USB-A 5V, charge IC control, charge status |

## Display / touch (MIPI)

| Signal | GPIO / bus |
|---|---|
| Display data | MIPI-DSI (dedicated lanes, not GPIO-addressable) |
| Backlight (PWM) | G22 — LEDC channel 0, 9-bit resolution |
| Touch interrupt | G23 (TP_INT) |
| Touch/display I2C | shared system bus (SDA=G31, SCL=G32) |
| Display/touch reset | via IO expander 0x43 (active-low) |

Default framebuffer orientation from cold boot is portrait (720x1280); call
`setRotation()` for the usual landscape 1280x720 layout.

## Camera (MIPI-CSI)

| Signal | GPIO |
|---|---|
| Data | MIPI-CSI 2-lane (dedicated lanes) |
| MCLK | G36 |
| Control I2C | shared system bus (SDA=G31, SCL=G32) |
| Reset | via IO expander 0x43 |

Sensor: SC2356, 2MP, 1600x1200 max.

## Audio

| Signal | GPIO |
|---|---|
| I2S MCLK | G30 |
| I2S SCLK (BCLK) | G27 |
| I2S LRCK | G29 |
| I2S data (codec ↔ AEC front-end) | G26 / G28 |
| Codec/AEC control I2C | shared system bus (SDA=G31, SCL=G32) |
| Speaker enable (NS4150B SPK_EN) | via IO expander 0x43 |

## Wireless co-processor link (ESP32-P4 ↔ ESP32-C6, SDIO)

| Signal | GPIO |
|---|---|
| CLK | G12 |
| CMD | G13 |
| D0 | G11 |
| D1 | G10 |
| D2 | G9 |
| D3 | G8 |
| C6 reset | G15 |

Arduino: pass these to `WiFi.setPins(CLK, CMD, D0, D1, D2, D3, RST)` before
`WiFi.begin()` unless using a board-package version with the M5Tab5 board
entry (>= 3.2.2), which wires them in by default. ESP32-C6 power itself is
gated through IO expander 0x44.

## microSD

Two wiring modes are broken out; which one active firmware uses depends on
the driver:

| Mode | Pins |
|---|---|
| SPI (used by official Arduino microSD example) | CS=G42, SCK=G43, MOSI=G44, MISO=G39 |
| SDIO | data/clk/cmd lines across G39-G44 (consult the BSP/factory-firmware source for the exact SDIO pin role assignment if you need SDIO rather than SPI mode) |

## RS485

| Signal | GPIO |
|---|---|
| RX | G21 |
| TX | G20 |
| DIR (direction/enable) | G34 |

Driver: SIT3088, switchable 120Ω terminating resistor. RS485 supply is 6-24V per M5Stack's port spec.

## Grove / M5-Bus / GPIO_EXT / Stamp pads

| Port | Pins / notes |
|---|---|
| HY2.0-4P Grove port | G53 (data), G54 (data) — check silkscreen for which is SDA/SCL vs generic GPIO depending on the connected Unit |
| M5-Bus | rear connector, exposes 5V/3.3V/GND + a subset of GPIO — consult the schematic PDF for exact pin assignment before wiring a HAT |
| GPIO_EXT header | general-purpose expansion, consult schematic for exact pins |
| Stamp pads | solder pads for add-on comms modules (Cat.M, NB-IoT, LoRaWAN, etc.) |

The Grove/M5-Bus/GPIO_EXT exact pin roster beyond what's listed above isn't
consistently documented across sources as of this writing — treat G53/G54
as confirmed Grove data pins and point the user at the schematic PDF
(link in SKILL.md) for anything more specific (e.g. "which M5-Bus pin is
GPIO 46").

## IO expander pin functions (PI4IOE5V6408, 8-bit each)

These gate power/reset lines that aren't wired directly to the ESP32-P4.
Control them via I2C (addresses 0x43 / 0x44 above), not `digitalWrite()`.

| Expander | Pin | Function |
|---|---|---|
| 0x43 | antenna switch | internal 3D antenna vs external MMCX select |
| 0x43 | speaker enable | NS4150B SPK_EN |
| 0x43 | ext. 5V bus control | M5-Bus / HY2.0-4P / GPIO_EXT 5V rail |
| 0x43 | display reset | active-low |
| 0x43 | touch reset | active-low |
| 0x43 | camera reset | active-low |
| 0x44 | ESP32-C6 power | co-processor power gate |
| 0x44 | USB-A 5V | host-mode power output enable |
| 0x44 | charge enable | IP2326 CHG_EN |
| 0x44 | charge status (input) | IP2326 CHG_STAT |

Exact bit/pin numbering within each expander varies slightly between the
sources this skill was built from — verify against the schematic or the BSP
source before writing raw register-level expander code; prefer M5Unified's
`M5.Power` API (see `references/arduino.md`) for anything it already covers
(ext 5V output, at minimum) instead of talking to the expanders directly.

## USB

| Port | Mode |
|---|---|
| USB-A | Host (power gated via IO expander 0x44) |
| USB-C | OTG (USB 2.0); also used for flashing — enumerates as native USB CDC serial, no external driver needed |

**Download/flash mode entry**: hold Reset ~2 seconds until the internal
green LED rapid-blinks, then release.
