# ESP-IDF (bare-metal / RTOS) development

Use this path when the user explicitly wants ESP-IDF rather than Arduino —
e.g. FreeRTOS task control, a smaller footprint, custom AWS IoT
provisioning, or building on M5Stack's own AWS IoT Kit BSP.

**Chip-level capabilities live in a separate skill.** For generic
classic-ESP32 capability questions that aren't about this board's specific
wiring — RMT, LEDC, I2S, ADC/touch, deep sleep and wake sources, the ULP-FSM
coprocessor, PSRAM/flash config, dual-core task pinning, WiFi/BT
coexistence — see the **`esp32` skill** (shipped in the `esp32-chips` plugin
of this same marketplace; `claude plugin install esp32-chips@m5stack` if
it isn't present). Espressif's own ESP-IDF docs for the `esp32` target are
the upstream source behind it:
https://docs.espressif.com/projects/esp-idf/en/stable/esp32/

## Official support differs sharply between the two product lines

- **Core2 For AWS** has real official ESP-IDF support: M5Stack publishes a
  full BSP, factory firmware, and several worked AWS IoT examples in
  https://github.com/m5stack/Core2-for-AWS-IoT-Kit (PlatformIO project
  layout, ESP-IDF v4.2-based at time of writing). Its
  `components/core2forAWS` component covers display/touch, IMU, RTC, the
  ATECC608 crypto chip (via a bundled `esp-cryptoauthlib` port), and the
  SK6812 RGB LED ring — start there instead of hand-rolling drivers.
  **One caveat before you do**: the BSP's IMU support is MPU6886-based and
  predates the v1.3 refresh — read the IMU section below before using it on
  a Core2 For AWS v1.3 board. Worked example projects in that repo:
  `Hardware-Features-Demo` (exercises every BSP API), `Factory-Firmware`,
  `Getting-Started` (ESP RainMaker), `Blinky-Hello-World` (AWS IoT
  provisioning), `Smart-Thermostat` and `Smart-Spaces` (AWS IoT device
  shadow), `Alexa-for-IoT-Intro` (beta).
- **Plain Core2** has no equivalent official M5Stack ESP-IDF repo. Point
  users at community references instead, flagged as community-sourced, not
  official: https://github.com/ropg/m5core2_esp-idf_demo and
  https://github.com/usedbytes/m5core2-basic-idf (both "Core2 basic example
  with plain ESP-IDF, no Arduino"). Cross-check anything from these against
  the schematic before treating it as authoritative.

## I2C bus

AXP192 (0x34), BM8563 (0x51), FT6336U (0x38), the IMU (0x68), and — AWS
line only — ATECC608B (0x35) all sit on one bus (SDA=G21, SCL=G22). Init it
once and share the bus handle/driver instance across all device drivers
rather than each one calling bus-init independently.

## AXP192 power management

There's no AXP192 driver in ESP-IDF core — use M5Stack's own driver from
the `core2forAWS` BSP component (works for plain Core2 too, since the
AXP192 usage is identical — just skip the AWS-only parts), or a standalone
AXP192 ESP-IDF component from the ESP Component Registry. Whichever you
use, route vibration motor, LED, and rail control through it rather than
issuing raw register writes unless you have a specific reason to — the
AXP192 also manages the ESP32's own core voltage rail, so a mistake here
can affect more than the peripheral you're trying to control.

## Display (ILI9342C) and touch (FT6336U)

Standard SPI TFT — pins are SCK=G18, MOSI=G23, MISO=G38, CS=G5, DC=G15
(see `references/pinout.md`). `esp_lcd` with an `esp_lcd_panel_ili9341`-family
driver component is the standard ESP-IDF path (ILI9342C is
register-compatible with the ILI9341 family for most basic init/draw
operations — verify against the panel's own datasheet for anything beyond
basic framebuffer writes). Touch is FT6336U over the shared I2C bus,
interrupt on G39; `esp_lcd_touch_ft5x06`-family components are commonly
compatible since FT6336U shares much of its register layout with the
FT5x06 family, but confirm against the actual chip's datasheet before
assuming full compatibility.

## RTC (BM8563)

I2C address 0x51. This is the same RTC chip family used elsewhere in the
M5Stack catalog; a generic BM8563/PCF8563-compatible ESP-IDF driver
component works (BM8563 is a footprint-and-register-compatible clone of
NXP's PCF8563).

## IMU (MPU6886 **or** BMI270 — revision-dependent, and ESP-IDF won't auto-detect)

The IMU sits at I2C 0x68 on the shared bus on all four revisions, but
**which chip answers there depends on the board revision**: MPU6886 on
Core2 (v1.0/v1.1) and Core2 For AWS, BMI270 on Core2 v1.3 and Core2 For
AWS v1.3 (see SKILL.md's hardware-revisions table). They are both 6-axis
accel+gyro parts with entirely different register maps.

On Arduino this is a non-issue — M5Unified's `M5.Imu` detects the chip at
runtime and normalizes the API. **ESP-IDF has no equivalent auto-detect
layer**: you compile against one driver or the other, and the wrong choice
fails in a confusing way, because the address still ACKs (something *is*
there at 0x68) while the data comes back as garbage, constant, or zero.

**So this is the one Core2 task where you should ask the user which
revision they have before writing code.** For most other Core2 work the
revision doesn't change the answer and asking is just friction — here it
does. Note that an I2C scan does **not** disambiguate, since both chips
answer at 0x68. The board's underside label is the reliable check. The
USB-serial bridge chip is a decent secondary signal (readable from the
user's OS device list, since CP2104 and CH9102F enumerate with different
USB VID/PID) but only in one direction: **CP2104 means pre-1.3**, while
CH9102F only proves v1.3 on the *AWS* line — M5Stack's docs leave the
plain line's pre-1.3 bridge chip unspecified, so a plain board showing
CH9102F is not conclusive.

| Chip | Revisions | ESP-IDF driver options |
|---|---|---|
| MPU6886 | Core2 (v1.0/v1.1), Core2 For AWS | M5Stack's own https://github.com/m5stack/MPU6886-idf; the `core2forAWS` BSP's bundled IMU driver |
| BMI270 | Core2 v1.3, Core2 For AWS v1.3 | `espressif/bmi270` or `espp/bmi270` from the ESP Component Registry (https://components.espressif.com/components/espressif/bmi270); Bosch's upstream https://github.com/boschsensortec/BMI270_SensorAPI |

**BSP gotcha**: `components/core2forAWS` was written for the original Core2
For AWS, so its IMU API targets the MPU6886. On a **Core2 For AWS v1.3**
board the rest of the BSP (display, touch, RTC, ATECC608, LED bar) still
applies, but its IMU calls won't work against the BMI270 — substitute a
BMI270 driver for that one peripheral and leave the rest of the BSP in
place. Check the repo's current state before telling a user this is
unfixed; the BSP may have gained BMI270 support since this was written.

Note also that BMI270 requires a config-file upload to the chip at init
before it will produce data (a Bosch design characteristic, not a Core2
quirk) — a BMI270 that reports zeros right after power-on is usually an
init-sequence problem, not a wiring problem. Any of the drivers above
handle this for you; hand-rolled register code frequently misses it.

## AWS-line-only: ATECC608B secure element

I2C address 0x35. M5Stack's `Core2-for-AWS-IoT-Kit` repo bundles an
`esp-cryptoauthlib` port specifically for this chip — use it rather than
writing ATECC I2C commands from scratch. Same certificate-format gotcha as
noted in `references/arduino.md` applies here: the factory certificate is
in Microchip's compressed format with an invalid date and won't pass AWS
IoT's standard registration API — generate a new X.509 cert from the
chip's public key and have the chip sign it, rather than trying to register
the factory cert directly.

## AWS-line-only: SK6812 RGB LED ring

G25, 10 LEDs. Use RMT-based `led_strip` (ESP-IDF's standard addressable-LED
driver component) or the `core2forAWS` BSP's own LED bar API.

---

# UIFlow2 (Blockly / MicroPython)

UIFlow2 is M5Stack's browser-based visual/MicroPython environment
(https://uiflow2.m5stack.com). Core2 support exposes display, touch, RTC,
IMU, and (AWS line) the RGB LED ring as high-level blocks/MicroPython
objects analogous to the Arduino M5Unified API — same peripherals,
friendlier but less granular surface. The IMU is abstracted the same way it
is in M5Unified, so the MPU6886/BMI270 split above does not surface here.
The ATECC608 crypto chip is not practically usable for AWS IoT provisioning
from UIFlow2 — steer users who need that to Arduino or ESP-IDF.

# UIFlow1 (legacy)

Core2 was one of the original UIFlow1-era boards, and M5Stack still
supports it there for users maintaining older projects. If a user has
UIFlow1-specific `.m5f`/Blockly project files or references the older
UIFlow1 web IDE, that's expected — don't assume it's a mistake for
"UIFlow2." New projects should default to UIFlow2 unless the user has a
specific reason to stay on UIFlow1. Authoritative docs for both live under
https://docs.m5stack.com/en/uiflow2/introduction (UIFlow2) and M5Stack's
UIFlow1 documentation linked from the Core2 docs index for the legacy
environment.

For anything needing precise timing (audio, fast interrupt-driven touch
handling, tight AXP192 sequencing), steer the user to Arduino or ESP-IDF
instead of either UIFlow generation — MicroPython/Blockly overhead makes
that class of task harder.
