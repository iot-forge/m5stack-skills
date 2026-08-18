---
name: m5stack-core2
description: Hardware reference and development helper for the M5Stack Core2 family — a 2.0" touchscreen ESP32 (classic, Xtensa LX6) Controller built around an AXP192 power management IC, ILI9342C display, FT6336U capacitive touch, BM8563 RTC, and (on original/1.1/1.3 revisions) an MPU6886 or BMI270 IMU. Covers the plain Core2 (v1.0/v1.1, v1.3) and the Core2 For AWS variants (For AWS, For AWS v1.3), which add an ATECC608B hardware crypto chip for AWS IoT device authentication, a 10-LED SK6812 RGB ring, and a larger antenna. Use this skill whenever the user is writing, debugging, or planning firmware for any Core2 board, or asks about its pinout, power management (AXP192 — battery, vibration motor, LED, DCDC rails), display/touch, RTC, audio (NS4168/SPM1423), IMU, the ATECC608 secure element and AWS IoT provisioning, or how to set it up in Arduino IDE, PlatformIO, ESP-IDF, or UIFlow1/2. Also trigger on "Core2", "Core2 For AWS", "AWS IoT EduKit", "AWS IoT Kit v1.3", "K010-AWS", "Core2-for-AWS-IoT-EduKit", or "M5Core2" in an M5Stack context.
---

# M5Stack Core2 family development

Core2 is M5Stack's 2.0" touchscreen ESP32 (classic) Controller family. Every
member shares the same core: ESP32-D0WDQ6-V3 (dual-core Xtensa LX6 @
240MHz), 16MB flash, 8MB PSRAM, an AXP192 power management IC, a 2.0"
320x240 ILI9342C IPS display with FT6336U capacitive touch, a BM8563 RTC, an
NS4168 I2S amp + SPM1423 PDM mic, and a 500mAh 3.7V battery charged over a
magnetic pogo-pin base. Official docs index: https://docs.m5stack.com/en/core/core2

This skill folds M5Stack's several Core2 hardware revisions into one skill
rather than near-duplicate skills per revision — read "Hardware revisions"
below before writing code, since the differences (which IMU chip, whether an
ATECC608 crypto chip and RGB LED ring are present, physical dimensions)
matter for correctness.

## Important: this is classic ESP32, not S3/P4

Unlike the other M5Stack Controller skills in this marketplace (Cardputer
Adv, Tab5), Core2 runs on a **classic ESP32** (`ESP32-D0WDQ6-V3`) — Xtensa
LX6, not LX7, **no native USB** (programming/serial goes through an onboard
USB-UART bridge chip, not a USB-CDC peripheral on the SoC itself), no
ULP-RISC-V coprocessor, and Bluetooth Classic + BLE 4.2 rather than BLE 5.

For chip-level capability questions that aren't about this board's specific
wiring — RMT, LEDC, I2S, ADC/touch, deep sleep and wake sources, the ULP-FSM
coprocessor, PSRAM/flash config, WiFi/BT coexistence — see the **`esp32`
skill** (classic ESP32), shipped in the `esp32-chips` plugin of this same
marketplace. Install it with `claude plugin install esp32-chips@m5stack` if
it isn't present. Do **not** assume ESP32-S3 or ESP32-P4 chip-skill content
applies to this board; the classic part differs substantially.

## Hardware revisions

M5Stack has shipped several Core2 revisions under two product lines — plain
Core2 and Core2 For AWS. The AWS line adds hardware the plain line doesn't
have; within each line, "v1.3" denotes a component refresh (IMU and
USB-serial bridge chip swapped) rather than a peripheral change.

| Revision | Product line | IMU | USB-serial bridge | ATECC608B crypto | SK6812 RGB ring | Dimensions | Weight | Docs |
|---|---|---|---|---|---|---|---|---|
| Core2 (v1.0/v1.1) | Plain | MPU6886 (0x68) | not specified in official spec table | no | no | 54.0 x 54.0 x 16.5mm | 54.9g | https://docs.m5stack.com/en/core/core2 |
| Core2 v1.3 | Plain | BMI270 (0x68) | CH9102F | no | no | 54.0 x 54.0 x 16.5mm | 58.8g | https://docs.m5stack.com/en/core/Core2_v1.3 |
| Core2 For AWS | AWS | MPU6886 (0x68) | CP2104 | **yes**, 0x35 | **yes**, 10x, G25 | 54.0 x 54.0 x 23.5mm | 69.5g | https://docs.m5stack.com/en/core/core2_for_aws |
| Core2 For AWS v1.3 | AWS | BMI270 (0x68) | CH9102F | **yes**, 0x35 | **yes**, 10x, G25 | 54.0 x 54.0 x 23.7mm | 72.1g | https://docs.m5stack.com/en/core/Core2_For_AWS_v1.3 |

Notes:

- **When the revision actually matters — and when to ask.** For most Core2
  work it doesn't change the answer, and asking is just friction. The one
  place it reliably does is **IMU code**: MPU6886 and BMI270 are both
  6-axis accel+gyro parts at 0x68 with entirely different register maps,
  and this fork exists on **both** product lines (plain v1.0/v1.1 vs v1.3
  splits exactly the same way the AWS line does — this is not an
  AWS-specific concern). Which way to handle it depends on the toolchain:
  - **Arduino/PlatformIO**: don't ask. M5Unified's `M5.Imu` auto-detects
    the chip at runtime and normalizes the API, so one sketch works on all
    four revisions. See `references/arduino.md`.
  - **ESP-IDF**: ask first. There is no auto-detect layer — you compile
    against an MPU6886 driver or a BMI270 driver, and the wrong one fails
    confusingly (the address still ACKs, the data is garbage). See
    `references/espidf.md`.
  - **UIFlow1/2**: don't ask; the IMU is abstracted the same way it is in
    M5Unified.
- **How to disambiguate a revision** when it matters: an I2C scan will
  *not* do it, since MPU6886 and BMI270 both answer at 0x68. The label on
  the underside of the board is the only fully reliable check. The
  USB-serial bridge chip is a useful secondary signal the user can read off
  their OS device list without opening anything — but it's only reliable in
  one direction: **CP2104 means pre-1.3**. The reverse does not hold
  cleanly, because M5Stack's docs leave the plain line's pre-1.3 bridge
  chip unspecified (their v1.3 page says only "CP2104/CH9102" for the
  earlier version), so seeing CH9102F does not by itself prove a *plain*
  board is v1.3. On the AWS line both endpoints are documented (CP2104 →
  original, CH9102F → v1.3), so the check is solid there.
- **If the user says "Core2 For AWS" or "AWS IoT Kit/EduKit" without a
  version**, assume it could be either AWS revision — the
  ATECC608/RGB-ring/AWS-IoT-provisioning content in this skill applies to
  both, and only the IMU and USB-serial bridge chip differ between them.
- **The AWS-specific hardware is what makes "For AWS" a different product,
  not just a revision** — ATECC608B (hardware secure element for AWS IoT
  X.509 device auth), the SK6812 RGB LED ring, and a larger 3D antenna are
  present on both AWS revisions and absent on both plain revisions. This is
  why the AWS line gets its own column values throughout this skill rather
  than being a footnote.
- **Naming and availability of the original AWS board.** It shipped as SKU
  **K010-AWS** under AWS's "AWS IoT EduKit" program branding, and the
  official repo and workshop material carried the `Core2-for-AWS-IoT-EduKit`
  name before M5Stack's current `Core2-for-AWS-IoT-Kit`. A user with an
  original board is therefore likely to call it an "EduKit," and most
  surviving third-party tutorials and GitHub forks still use that name —
  treat those as referring to this same hardware, not a different product.
  The original appears to be end-of-life at retail (v1.3 is what's sold
  now), but that comes from a retail listing rather than an official
  M5Stack EOL notice, so hedge it if it comes up. It affects buy-advice
  only, not support advice: everything in this skill applies to an original
  board the user already owns.
- Vibration motor, power/RST buttons, microSD slot, and the pogo-pin
  magnetic charging base are common to **all four** revisions — don't treat
  them as AWS-specific.
- The "Core2 (v1.0/v1.1)" row above is sourced from M5Stack's current
  `core2` docs page, which likely documents whichever non-v1.3 hardware is
  currently shipping (probably v1.1) rather than the original v1.0 — treat
  minor spec drift between v1.0 and v1.1 specifically as unconfirmed.

## Quick specs (shared across the family)

- **SoC**: ESP32-D0WDQ6-V3, dual-core Xtensa LX6 @ 240MHz, ~600 DMIPS
- **SRAM**: 520KB on-chip
- **Flash**: 16MB
- **PSRAM**: 8MB
- **Wireless**: WiFi 4 (802.11b/g/n, 2.4GHz only) + Bluetooth Classic + BLE 4.2
- **Power management**: AXP192 (I2C 0x34) — battery charge/monitor, all
  onboard voltage rails, vibration motor drive, status LED, power button
  long-press/short-press handling
- **Display**: 2.0", 320x240, ILI9342C driver, IPS, SPI
- **Touch**: FT6336U capacitive controller, I2C 0x38, interrupt on G39;
  three software-defined "virtual button" zones at the bottom of the screen
- **RTC**: BM8563, I2C 0x51
- **Audio**: NS4168 I2S amp + 1W speaker, SPM1423 PDM digital microphone
- **Battery**: 500mAh @ 3.7V Li-ion, magnetic pogo-pin charging, TP4057
  charging IC; charging ~0.219A, idle-off ~0.055A, idle-on ~0.147A
- **Storage**: microSD slot (SPI, shares the display's bus — CS on a
  separate pin, see `references/pinout.md`)
- **Expansion**: HY2.0-4P Grove-style ports (labeled PORT.A/B/C on the AWS
  line's base), M5-Bus socket
- **USB**: Type-C, routed through an onboard USB-UART bridge (CP2104 or
  CH9102F depending on revision — see table above) for
  flashing/programming/serial, **not** native USB-CDC on the SoC
- **Input voltage**: 5V @ 500mA
- **Operating temperature**: 0-40°C (AWS line) / 0-60°C (plain line, per
  official spec pages — plain Core2's higher rating is as published, not
  independently re-verified)
- **Material / mounting**: plastic (PC) shell, built-in magnets, LEGO-compatible mounting holes

Full pin-by-pin map (I2C addresses, display/touch/audio/SD SPI pins,
AWS-only ATECC608/SK6812 pins, expansion port pinout, per-revision physical
dimensions) is in `references/pinout.md` — read it whenever you need an
exact GPIO number or I2C address rather than re-deriving it.

## AWS-line-specific hardware

Only present on Core2 For AWS and Core2 For AWS v1.3:

- **ATECC608B-TNGTLSU-G** hardware crypto chip, I2C 0x35. Holds a factory
  device certificate/private key for AWS IoT Core mutual-TLS device
  authentication; the private key never leaves the chip. **Gotcha**: the
  factory-programmed certificate is stored in Microchip's compressed
  format with placeholder issuer/subject fields and an invalid date
  (2005-08-28), which AWS IoT's standard registration API rejects with a
  `CertificateValidationException` if you try to register it as-is. The
  community-verified fix is to read the chip's public key, generate a
  proper X.509 certificate locally, and have the ATECC608 sign it
  internally (private key stays on-chip) rather than trying to register
  Microchip's raw factory cert or reach for Microchip's 800+ line Python
  helper script. See `references/arduino.md` and `references/espidf.md`
  for the library-level pointers.
- **SK6812 RGB LED ring**, 10 LEDs, single data line on G25 (standard
  NeoPixel-compatible timing) — drive with `Adafruit_NeoPixel`/`FastLED`
  (Arduino) or `led_strip`/RMT (ESP-IDF); M5Stack's own
  `components/core2forAWS` BSP also wraps this.
- Larger "2.4G 3D antenna" than the plain line (both are still 2.4GHz-only,
  single-band).

## Picking a development platform

The Core2 family officially supports five workflows — more than most other
M5Stack boards, since UIFlow1 (the original, MicroPython/Blockly) predates
UIFlow2 and Core2 is old/popular enough that M5Stack never dropped support
for it. Ask the user which they're using if it's not obvious from their
code; default to Arduino/C++ with M5Unified if they don't have a preference.

| Platform | When to use | Details |
|---|---|---|
| **Arduino IDE** | Most user sketches, quickest to get running | `references/arduino.md` |
| **PlatformIO** | VS Code users, CI builds, multi-file projects | `references/arduino.md` |
| **ESP-IDF** | Bare-metal/RTOS work, the official AWS IoT Kit BSP, custom AWS IoT provisioning | `references/espidf.md` |
| **UIFlow2** | Blockly or MicroPython, fastest prototyping | `references/espidf.md` (brief section at the end) |
| **UIFlow1** | Legacy Blockly/MicroPython projects still targeting it | `references/espidf.md` (brief section at the end) |

Read the relevant reference file before writing code for that platform —
each has the actual include/init pattern and gotchas specific to that
toolchain rather than generic advice.

## Official resources

- Docs index: https://docs.m5stack.com/en/core/core2
- Plain Core2: https://docs.m5stack.com/en/core/core2 · v1.3: https://docs.m5stack.com/en/core/Core2_v1.3 · SKU page (v1.1): https://docs.m5stack.com/en/products/sku/K010-V11
- Core2 For AWS: https://docs.m5stack.com/en/core/core2_for_aws · v1.3: https://docs.m5stack.com/en/core/Core2_For_AWS_v1.3
- AWS IoT Kit documentation portal: https://core2-for-aws-iot-kit.m5stack.com/en/
- Arduino IDE quick start: https://docs.m5stack.com/en/quick_start/core2/arduino
- Arduino library (legacy, board-specific): https://github.com/m5stack/M5Core2
- Arduino library (modern, recommended): https://github.com/m5stack/M5Unified (+ https://github.com/m5stack/M5GFX)
- Official AWS IoT Kit ESP-IDF/PlatformIO repo (BSP, factory firmware, AWS IoT examples): https://github.com/m5stack/Core2-for-AWS-IoT-Kit
- **Legacy "EduKit" naming**: the original board (SKU K010-AWS) was sold under AWS's "AWS IoT EduKit" program, and its repo/workshop material used the `Core2-for-AWS-IoT-EduKit` name — surviving community forks and third-party tutorials still do (e.g. https://github.com/sbstjn/Core2-for-AWS-IoT-EduKit). Same hardware as `Core2-for-AWS-IoT-Kit` above; prefer the current repo for new work. AWS's original launch announcement: https://aws.amazon.com/about-aws/whats-new/2020/12/introducing-aws-iot-edukit
- ESP-IDF IMU drivers (revision-dependent, see `references/espidf.md`): MPU6886 https://github.com/m5stack/MPU6886-idf · BMI270 https://components.espressif.com/components/espressif/bmi270
- Schematics: Core2 main board https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/644/CORE2_V1.0_SCH.pdf · AWS v1.3 base https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/1226/SCH_M5GO_Bottom2_SCH_Main_V1.3_AWS_Version_2026_01_30_10_06_42.pdf
- Structure files (AWS v1.3): https://github.com/m5stack/M5_Hardware/tree/master/Products/K010-AWS-V13_Core2_For_AWS_v1.3/Structures
- ATECC608 community writeup on the AWS IoT cert-registration gotcha: https://community.m5stack.com/topic/8058/how-to-actually-use-the-core2-aws-atecc608-with-aws-iot

## Working with the user

- If they paste an I2C error, check the address against
  `references/pinout.md`'s table first — AXP192, BM8563, FT6336U, the IMU,
  and (AWS line) ATECC608 all share one internal I2C bus, so a bus-level
  fault breaks all of them at once while a single wrong address only
  breaks one peripheral.
- If they're asking for **IMU code in ESP-IDF**, ask which revision the
  board is before writing it (see the hardware-revisions notes above) —
  this is the one Core2 task where guessing produces code that compiles,
  runs, ACKs on the bus, and returns wrong numbers. In Arduino, don't ask:
  `M5.Imu` handles it.
- If they're trying to register the ATECC608's factory certificate with AWS
  IoT and hitting `CertificateValidationException`, don't debug their AWS
  IoT policy/permissions first — point them at the cert-format gotcha above,
  it's the far more common cause.
- If their code assumes a peripheral that doesn't exist on their actual
  board (RGB LEDs or ATECC608 on plain Core2, or IMU register behavior that
  differs between MPU6886 and BMI270), check the hardware-revisions table
  above before assuming the code itself is buggy.
- If they mention native USB / USB-CDC behavior, remind them Core2 has no
  native USB peripheral on the ESP32 — the Type-C port goes through a
  USB-UART bridge chip, so there's no USB HID/MSC/CDC-from-the-SoC the way
  there is on ESP32-S3 boards.
- If they refer to an "EduKit" or link to `Core2-for-AWS-IoT-EduKit`
  material, that's the original Core2 For AWS under its old name — not a
  different board, and not a mistake to correct. Their tutorial may be
  pinned to an older ESP-IDF version than the current repo, though, which
  is worth checking if a build fails.
- Official ESP-IDF support is much richer for the AWS line (the
  `Core2-for-AWS-IoT-Kit` repo) than for plain Core2, which has no official
  M5Stack ESP-IDF factory-firmware repo — see `references/espidf.md` for
  the community alternatives and their caveats.
- Library APIs move; treat the code patterns in the reference files as
  representative of the current M5Unified/M5Core2 API shape, but if the
  user hits a compile error on a specific method name, check
  https://github.com/m5stack/M5Unified or https://github.com/m5stack/M5Core2
  for the current signature rather than assuming the reference file is
  exactly up to date.
