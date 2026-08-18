---
name: m5stack-tab5
description: Hardware reference and development helper for the M5Stack Tab5 (product code C145) — an ESP32-P4-based 5" touchscreen IoT/industrial terminal with an ESP32-C6 wireless co-processor, MIPI-DSI display, MIPI-CSI camera, ES8388 audio codec, BMI270 IMU, RX8130CE RTC, RS485, and a removable NP-F550 battery. Use this skill whenever the user is writing, debugging, or planning firmware for a Tab5, or asks about its pinout, display/touch (GT911/ILI9881C or ST7123/ST7121), camera (SC2356), audio (ES8388/ES7210), IMU, RTC, power management (IP2326/INA226/IO expanders), RS485, Grove/M5-Bus/GPIO_EXT ports, or how to set it up in Arduino IDE, PlatformIO, UIFlow2, or ESP-IDF. Also trigger on "M5Tab5" or the bare word "Tab5" in an M5Stack/ESP32-P4 context.
---

# M5Stack Tab5 development

The Tab5 is M5Stack's ESP32-P4-based touchscreen terminal: a 5" 1280x720
MIPI-DSI display, MIPI-CSI camera, ES8388 audio codec with AEC front-end,
BMI270 IMU, RX8130CE RTC, RS485 port, and a removable 2000mAh NP-F550
battery, with an ESP32-C6-MINI-1U handling WiFi 6 / BLE / Thread / Zigbee as
a co-processor over SDIO. It targets industrial HMI, kiosk, and IoT-gateway
use cases rather than being a general "big Core2" — expect RS485, camera,
and multi-protocol wireless to matter more here than on other M5Stack
Controllers. Official docs: https://docs.m5stack.com/en/core/Tab5

Use this skill to write correct firmware for it (Arduino, PlatformIO,
ESP-IDF, or UIFlow2/MicroPython), to explain what a pin or peripheral does,
or to debug hardware-facing code (wrong I2C address, WiFi not connecting,
touch not responding, display not initializing, etc).

## Important: this is an ESP32-P4, not an ESP32/ESP32-S3

Most M5Stack Controllers (Cardputer Adv, Core2, CoreS3, AtomS3, ...) run on
an ESP32 or ESP32-S3 — Xtensa cores. The Tab5's main SoC is an
**ESP32-P4**, which is **RISC-V**, has **no built-in WiFi/Bluetooth radio**,
and needs its own toolchain target (`esp32p4`)/board entry. WiFi and BLE
come from a *separate* ESP32-C6 co-processor on the board, bridged over
SDIO — this is why WiFi init code looks different from every other M5Stack
board (see "WiFi needs pin setup" below). Don't reuse ESP32/ESP32-S3-specific
assumptions (Xtensa intrinsics, single-chip WiFi init, etc.) when writing
Tab5 firmware.

For chip-level capability questions about either SoC that aren't about this
board's specific wiring, see the **`esp32-p4`** and **`esp32-c6`** skills,
shipped in the `esp32-chips` plugin of this same marketplace
(`claude plugin install esp32-chips@m5stack` if they aren't present).

## Hardware revisions: two different display/touch chip sets exist

M5Stack changed the integrated display/touch driver partway through
production. Both revisions expose the same 5" 1280x720 panel and the same
touch behavior at the application level (M5GFX/M5Unified abstracts it), but
if the user is doing low-level LCD/touch driver work, check which one they
have:

| Revision | Display driver | Touch controller | Touch I2C addr | Seen in |
|---|---|---|---|---|
| Early production | ILI9881C | GT911 (separate chip) | 0x14 | Official Espressif BSP component (`espressif/m5stack_tab5`), most 2025-era teardowns |
| Current production | ST7121 | ST7123 (integrated display+touch) | 0x55 | Newer units |

If the user's code references `esp_lcd_touch_gt911` / GT911 and it isn't
detecting touch, or references ST7123/ST7121 registers on an older unit,
suspect a revision mismatch. When in doubt, the M5Unified/M5GFX high-level
API (`M5.Display`, `M5.Touch`) handles both automatically — recommend it
over hand-rolled panel driver code unless the user specifically needs
bare-metal LCD/touch access.

## Quick specs

- **Main SoC**: ESP32-P4NRW32, dual-core RISC-V @ 360MHz (M5Stack's own boot
  logs and Arduino config show 360MHz; ESP32-P4 silicon is rated up to
  400MHz and some M5Stack marketing copy says 400MHz — treat 360MHz as the
  as-shipped default and don't be surprised if the user has overclocked)
  + LP core @ 40MHz
- **Flash**: 16MB
- **PSRAM**: 32MB Octal — **must be enabled** in Arduino IDE build settings
  or you'll hit memory issues fast (the display framebuffer alone is large)
- **Wireless co-processor**: ESP32-C6-MINI-1U (WiFi 6 2.4GHz, BLE 5, Thread,
  Zigbee), connected to the P4 over SDIO, not a shared die
- **Antenna**: built-in 3D antenna + 2x external MMCX ports, switchable via
  IO expander (see pinout.md)
- **Display**: 5", 1280x720 (720p), MIPI-DSI — see "Hardware revisions"
  above for driver chip
- **Touch**: capacitive multi-touch, I2C — see "Hardware revisions" above
- **Camera**: SC2356, 2MP (1600x1200), MIPI-CSI 2-lane (community testing
  notes full-screen preview runs only ~1-2 FPS — don't promise smooth video
  without checking the user's actual use case/resolution)
- **Audio**: ES8388 codec (I2C 0x10, speaker/headphone output) + ES7210 AEC
  front-end (I2C 0x40, dual mic array), NS4150B 1W/8Ω speaker amp, 3.5mm jack
- **IMU**: BMI270, 6-axis accel+gyro, I2C 0x68, interrupt wake-up capable
- **RTC**: RX8130CE, I2C 0x32, timed interrupt wake-up capable
- **Power monitor**: INA226, I2C 0x41, bus voltage/current
- **Charge IC**: IP2326 (device must be powered on to charge); **buck-boost**: MP4560
- **IO expanders**: 2x PI4IOE5V6408 (I2C 0x43 and 0x44) — antenna switching,
  speaker enable, external 5V bus control, display/touch/camera resets,
  ESP32-C6 power, USB-A 5V, charge control (full pin map in pinout.md)
- **Battery**: NP-F550 removable Li-ion, 7.4V/2000mAh (14.8Wh), ~6h typical
  use (50% brightness, WiFi on)
- **Storage**: microSD slot (Arduino examples default to SPI mode; SDIO mode
  pins also broken out — see pinout.md)
- **Expansion**: RS485 (SIT3088, switchable 120Ω terminator), M5-Bus,
  HY2.0-4P Grove port, GPIO_EXT header, Stamp pads
- **USB**: Type-A (Host) + Type-C (USB 2.0 OTG, also used for
  flashing/download — enumerates as native USB CDC serial)
- **Size / weight**: 128.0 x 80.0 x 12.0mm (26.7mm with battery attached), ~118g device / ~99g battery
- **Mount**: 1/4"-20 tripod nut on the back
- **Operating temp**: 0-40°C

Full pin-by-pin map (I2C system bus, SDIO link to the C6, display/touch,
camera, audio, IMU/RTC/power-monitor addresses, SD card, RS485, Grove/M5-Bus/
GPIO_EXT, IO expander pin functions) is in `references/pinout.md` — read it
whenever you need an exact GPIO number or I2C address rather than
re-deriving it.

## WiFi needs pin setup (unlike other M5Stack boards)

Because WiFi lives on the separate ESP32-C6 co-processor over SDIO, plain
`WiFi.begin()` isn't enough on raw Arduino-ESP32 — you must tell the driver
which pins carry the SDIO link first:

```cpp
#include <WiFi.h>

WiFi.setPins(GPIO_NUM_12 /*CLK*/, GPIO_NUM_13 /*CMD*/, GPIO_NUM_11 /*D0*/,
             GPIO_NUM_10 /*D1*/, GPIO_NUM_9 /*D2*/, GPIO_NUM_8 /*D3*/,
             GPIO_NUM_15 /*RST*/);
WiFi.begin(ssid, password);
```

If the user selected the dedicated **M5Tab5** board entry (not the generic
"ESP32P4 Dev Module") in a recent-enough M5Stack board package (>= 3.2.2),
these pins are wired in by default and `WiFi.setPins()` can be skipped —
but it's harmless to call explicitly either way, and doing so removes a
whole class of "WiFi won't connect" bug reports. See `references/pinout.md`
for the full SDIO pin table and `references/arduino.md` for the board
setup that makes the defaults kick in.

## Picking a development platform

The board officially supports four workflows. Ask the user which one
they're using if it's not obvious from their code or request; default to
Arduino/C++ with M5Unified if they don't have a preference — it's the path
with the most example coverage for Tab5 specifically. Note that
Tab5/ESP32-P4 support is newer and less mature across all four platforms
than on the ESP32-S3 boards — expect more version-pinning and rougher edges.

| Platform | When to use | Details |
|---|---|---|
| **Arduino IDE** | Most user sketches, quickest to get running | `references/arduino.md` |
| **PlatformIO** | VS Code users, CI builds, multi-file projects | `references/arduino.md` (same library, ESP32-P4 platform-support caveats noted there) |
| **ESP-IDF** | Bare-metal/RTOS work, using the official BSP component or the factory firmware source | `references/espidf.md` |
| **UIFlow2** | Blockly or MicroPython, fastest prototyping, less flexible | `references/espidf.md` (brief section at the end) |

Read the relevant reference file before writing code for that platform —
each one has the actual include/init pattern and the gotchas specific to
that toolchain, rather than generic advice.

## Official resources

- Docs page: https://docs.m5stack.com/en/core/Tab5
- Arduino subsection (per-peripheral pages): https://docs.m5stack.com/en/arduino/m5tab5/program (and sibling pages under `/arduino/m5tab5/`)
- UIFlow2 subsection: https://docs.m5stack.com/en/uiflow2/Tab5/program
- ESP-IDF factory firmware guide: https://docs.m5stack.com/en/esp_idf/m5tab5/userdemo
- Arduino library: https://github.com/m5stack/M5Unified (and https://github.com/m5stack/M5GFX)
- Official ESP-IDF BSP component: https://components.espressif.com/components/espressif/m5stack_tab5
- Factory firmware source (reference implementation, LVGL-based): https://github.com/m5stack/M5Tab5-UserDemo
- Schematic (PDF): https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/1132/Tab5_Schematics_PDF.pdf
- Block diagram (PDF): https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/1132/Tab5_Overall_Design_Block_Diagram.pdf
- Structure files: https://github.com/m5stack/M5_Hardware/tree/master/Products/C145_Tab5/Structures
- Product page: https://shop.m5stack.com/products/m5stack-tab5-iot-development-kit-esp32-p4

## Working with the user

- If they paste a WiFi-won't-connect error first, check for missing
  `WiFi.setPins()` (or an old M5Stack board package that predates the
  dedicated M5Tab5 board entry) before anything else — see "WiFi needs pin
  setup" above.
- If they paste an I2C error, check the address against
  `references/pinout.md`'s address table — touch, audio codec, AEC
  front-end, IMU, RTC, power monitor, and both IO expanders all share the
  same I2C bus (SDA=G31, SCL=G32), so a bus-level fault (missing pull-ups,
  wrong bus init) breaks all of them at once, while a single wrong address
  only breaks one peripheral.
- If PSRAM isn't enabled in the Arduino build, expect crashes/reboots under
  anything display- or camera-heavy rather than a clean out-of-memory error
  — this is the single most common Tab5 bring-up complaint in community
  reports.
- Camera FPS complaints in full-resolution preview are a known limitation
  reported in community testing (~1-2 FPS at 1600x1200 in some
  configurations), not necessarily a bug in the user's code — suggest a
  lower preview resolution before assuming their code is wrong.
- Library APIs and ESP32-P4 platform support move fast right now; treat the
  code patterns in the reference files as representative of the current
  shape, but if the user hits a compile error on a specific method/board
  name, check https://github.com/m5stack/M5Unified or the linked BSP/repo
  for the current signature rather than assuming the reference file is
  exactly up to date.
