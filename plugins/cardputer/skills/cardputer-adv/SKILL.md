---
name: m5stack-cardputer-adv
description: Hardware reference and development helper for the M5Stack Cardputer Adv (also written Cardputer-ADV, product code K132-Adv) — a pocket ESP32-S3 computer with a 56-key keyboard, 1.14" screen, BMI270 IMU, and ES8311 audio codec. Use this skill whenever the user is writing, debugging, or planning firmware for a Cardputer Adv, or asks about its pinout, keyboard (TCA8418), IMU (BMI270), audio codec (ES8311), display (ST7789V2), Grove/EXT ports, battery behavior, or how to set it up in Arduino IDE, PlatformIO, UIFlow2, or ESP-IDF. Also trigger on the plain "Cardputer" name if context (TCA8418, BMI270, ES8311, or "Adv"/"ADV") makes clear it's the Adv variant rather than the original Cardputer, since the two boards differ in keyboard and audio hardware and are easy to mix up.
---

# M5Stack Cardputer Adv development

The Cardputer Adv is an ESP32-S3-based pocket computer from M5Stack: a 56-key
keyboard, 1.14" IPS screen, IMU, mic/speaker, Grove and EXT expansion ports,
microSD, and a 1750mAh battery, all in an 84 x 54 x 19.6mm shell. Official
docs: https://docs.m5stack.com/en/core/Cardputer-Adv

Use this skill to write correct firmware for it (Arduino, PlatformIO,
ESP-IDF, or UIFlow2/MicroPython), to explain what a pin or peripheral does,
or to debug hardware-facing code (wrong I2C address, keyboard not
responding, display not initializing, etc).

## Important: this is not the original Cardputer

M5Stack sells two boards with very similar names and the same enclosure
shape. Don't assume code for one works unmodified on the other.

| Subsystem | Cardputer (original) | Cardputer Adv |
|---|---|---|
| Keyboard | GPIO scan matrix, no I2C | **TCA8418 I2C keypad controller** + interrupt on G11 |
| Audio | NS4168 I2S amp + SPM1423 PDM mic | **ES8311 codec** (I2C control + I2S data) + NS4150B amp |
| IMU | none | **BMI270** (I2C, 6-axis) |
| Module | Stamp-S3 | Stamp-S3A |

If the user's code touches raw GPIO pin numbers for the keyboard or mic,
double-check which board it targets — a sketch written for the original
Cardputer's GPIO matrix keyboard will not read keys correctly on the Adv,
which exposes its keyboard only through the TCA8418 over I2C.

The good news: **if you use the official `M5Cardputer` Arduino library (which
wraps M5Unified/M5GFX), the same high-level API (`M5Cardputer.Keyboard`,
`.Display`, `.Speaker`, `.Mic`, `.Imu`) works on both boards** — the library
detects which hardware is present and talks to the right chip underneath.
Prefer that library over hand-rolled register access unless the user is
specifically doing bare-metal ESP-IDF work or needs something the library
doesn't expose.

## Quick specs

- **SoC**: ESP32-S3FN8, dual-core Xtensa LX7 @ 240MHz, 8MB flash
- **Display**: 1.14", 240x135px, ST7789V2 driver, SPI
- **Keyboard**: 56 keys (4 rows x 14 cols), TCA8418 I2C controller, 160gf keypress
- **IMU**: BMI270, 6-axis, I2C
- **Audio**: ES8311 codec, MEMS mic (65dB SNR), NS4150B amp + 8Ω/1W speaker, 3.5mm jack
- **Storage**: microSD slot
- **Expansion**: Grove port (HY2.0-4P), EXT 2.54-14P header (SPI/I2C/UART)
- **Connectivity**: WiFi + BLE (integrated in ESP32-S3)
- **Battery**: 1750mAh Li-po; ~120-155mA active draw depending on radio use; 0.23µA standby (power switch off)
- **Other**: IR emitter, magnetic back, LEGO-compatible mounting holes, lanyard hole
- **Size / weight**: 84.0 x 54.0 x 19.6mm, 81.0g

Full pin-by-pin map (display, keyboard/IMU I2C, audio, SD, Grove, EXT,
IR, battery ADC) is in `references/pinout.md` — read it whenever you need
an exact GPIO number rather than re-deriving it.

## Picking a development platform

The board officially supports four workflows. Ask the user which one they're
using if it's not obvious from their code or request; default to Arduino/C++
with the `M5Cardputer` library if they don't have a preference, since that's
the most common path and has the broadest example coverage.

| Platform | When to use | Details |
|---|---|---|
| **Arduino IDE** | Most user sketches, quickest to get running | `references/arduino.md` |
| **PlatformIO** | VS Code users, CI builds, multi-file projects | `references/arduino.md` (same library, different build config) |
| **ESP-IDF** | Bare-metal/RTOS work, squeezing performance, no Arduino overhead | `references/espidf.md` |
| **UIFlow2** | Blockly or MicroPython, fastest prototyping, less flexible | `references/espidf.md` (brief section at the end) |

Read the relevant reference file before writing code for that platform —
each one has the actual include/init pattern and the gotchas specific to
that toolchain, rather than generic advice.

## Compatible caps

Caps snap onto the 14-pin EXT header. When a user mentions one by name,
point them at the dedicated skill for register-level detail and pin
mapping — the EXT header carries SPI/I2C/UART, so multiple caps reuse the
same physical pins for different purposes and mis-mapping is easy.

| Cap | SKU | Adds | Skill |
|---|---|---|---|
| Cap LoRa-1262 | U214 | SX1262 LoRa (868–923 MHz) + ATGM336H GNSS | `plugins/cardputer/skills/cap-lora-1262/` |

Note: **the LoRa cap's SPI bus shares MOSI/MISO/CLK with the microSD slot**
(G14/G39/G40) — separate CS pins (G5 vs G12), so both can coexist on one
`SPIClass`, but two independently configured buses to the same pins will
fight. The cap skill covers this in detail.

## Official resources

- Docs page: https://docs.m5stack.com/en/core/Cardputer-Adv
- Arduino library: https://github.com/m5stack/M5Cardputer (supports both Cardputer and Cardputer Adv)
- ESP-IDF factory firmware (reference implementation): https://github.com/m5stack/M5Cardputer-UserDemo/tree/CardputerADV
- Schematic (PDF): https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/1178/Sch_M5CardputerAdv_v1.0_2025_06_20_17_19_58.pdf
- 3D model / mechanical drawing (PDF): https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/1178/K132-Adv-cardputer-ADV.pdf
- Structure files: https://github.com/m5stack/M5_Hardware/tree/master/Products/K132-Adv_Cardputer-Adv/Structures

## Working with the user

- If they paste an error, check whether it's an I2C problem first (wrong
  address, bus not initialized, or `M5Cardputer.begin()` missing/misordered)
  — most Cardputer Adv bring-up issues on this board are I2C-related because
  keyboard, IMU, and audio codec all share one bus (SDA=G8, SCL=G9).
- If they ask "why doesn't my keyboard code from my old Cardputer work",
  point them at the table above — it's almost always the GPIO-matrix vs
  TCA8418 difference.
- Library APIs move; treat the code patterns in the reference files as
  representative of the current M5Unified/M5Cardputer API shape, but if the
  user hits a compile error on a specific method name, check
  https://github.com/m5stack/M5Cardputer for the current signature rather
  than assuming the reference file is exactly up to date.
