---
name: esp32
description: Chip-level ESP-IDF capability reference for the classic ESP32 SoC (dual-core Xtensa LX6) — what the chip can do, distinct from board wiring. Covers the ESP32-D0WDQ6-V3 / ESP32-D0WD-V3 / ESP32-D0WDR2-V3 die family used in ESP32-WROOM-32 and ESP32-WROVER modules. Use for RMT (IR/WS2812), LEDC (PWM), I2S (audio/parallel camera), ADC/DAC/touch (incl. ADC2-vs-WiFi conflict), PCNT, MCPWM, TWAI/CAN, SDMMC host + SDIO slave, the deprecated Hall sensor, ULP-FSM, deep sleep/hibernation, dual-core task pinning, WiFi/Bluetooth Classic+BLE coexistence, and what "V3" silicon changed vs older revisions. Trigger on RMT/LEDC/I2S/ULP/deep-sleep/ADC2 questions on a classic ESP32, D0WDQ6/D0WD/D0WDR2/WROOM/WROVER, or any M5Stack classic-ESP32 board (Core2, Basic, Fire, Tough, StickC-Plus, Atom-Lite/Matrix, Stamp-Pico, CoreInk, Paper) needing depth beyond its own SKILL.md. For pinouts/wiring use that board's skill — this is the shared chip layer it points into.
---

# ESP32 (classic) chip capabilities

This skill is the **chip layer**, not a board layer. A board skill (e.g.
`m5stack-core2`) tells you what's wired to what on one specific product;
this skill tells you what the classic ESP32 silicon itself can do — the
peripherals, low-power modes, memory options, and concurrency model that
are the same on every classic-ESP32 board regardless of vendor. Read a
board's own skill first for pin numbers and I2C addresses, then come here
when the user wants to go deeper on a capability than "call the vendor's
high-level library and move on" — e.g. writing a custom RMT-based protocol,
understanding why an ADC read returns garbage once WiFi turns on, tuning
deep-sleep/hibernation wake behavior, or pinning tasks to cores.

## What "ESP32-D0WDQ6-V3" actually names

This is the oldest and most fragmented naming scheme in the family, worth
untangling explicitly:

- **D0WD / D0WDQ6 / D0WDR2** identify the *die + package*, not a firmware
  target — all three are the same dual-core Xtensa LX6 silicon, differing
  only in package size and whether flash/PSRAM is bonded into the same
  package:
  - **ESP32-D0WD-V3** — QFN 5×5mm, no in-package flash or PSRAM (external
    only).
  - **ESP32-D0WDQ6-V3** — QFN 6×6mm (larger, more pins broken out for
    external QSPI), no in-package flash or PSRAM (external only). This is
    the die used inside **ESP32-WROOM-32** modules, which add the external
    flash chip inside the module's own metal can — the bare D0WDQ6 chip
    itself still has no embedded memory.
  - **ESP32-D0WDR2-V3** (EOL, superseded by ESP32-D0WDR2-V3→D0WDRH2-V3) —
    same die family with 2MB of PSRAM bonded into the package. This is the
    die used inside **ESP32-WROVER** modules (which add external flash on
    top, same as WROOM).
  - There's also a single-core sibling (S0WD, used in ESP32-SOLO-1
    modules) and a dual-core-with-more-GPIO sibling (D2WD) — not covered
    here since no M5Stack board is known to use them; flag it if one
    turns up.
- **"-V3"** is the *chip revision* (silicon stepping), not part of the
  package family. It means this specific die incorporates the v3.0 errata
  fixes Espressif shipped starting ~2019 — see "Why the V3 revision
  matters" below. Essentially all ESP32 chips manufactured since then
  (which is to say, essentially every ESP32-based M5Stack product
  currently sold) are V3 or later; V1/V0 silicon mostly only turns up in
  old stock or secondhand boards.
- **Practical takeaway**: "ESP32-D0WDQ6-V3" and "classic ESP32" mean the
  same thing for firmware purposes on any current M5Stack board — the
  package/revision suffix mostly matters for hardware design (which module
  to buy) and for the one or two errata-driven firmware differences noted
  below, not for which peripherals or APIs are available.

## Not ESP32-S3, not P4, not C3/C6/C5, not H2

M5Stack (and the ESP32 family generally) spans several very different chips
that are easy to conflate. Get this wrong and code silently targets the
wrong architecture or assumes a peripheral that doesn't exist.

| Chip | Cores / arch | Wireless | Native USB | Notable extras | Not on this chip |
|---|---|---|---|---|---|
| **ESP32 (classic, this skill)** | 2× Xtensa LX6 @ up to 240MHz | WiFi 4 (2.4GHz only) + Bluetooth **Classic (BR/EDR) v4.2** + BLE 4.2 | No — UART only, via an external USB-to-serial bridge chip on dev boards | Widest library/example coverage, oldest/most mature silicon, SDIO **slave** mode (can act as a co-processor to a host SoC), Hall sensor (deprecated) | Native USB, SIMD/vector extensions, ULP-RISC-V, internal temp sensor, BLE 5 |
| ESP32-S3 | 2× Xtensa LX7 @ up to 240MHz + 1 low-power coprocessor core | WiFi 4 + BLE 5 (no Classic) | Yes — OTG + separate USB-Serial-JTAG | SIMD/vector AI instructions, ULP-RISC-V *and* ULP-FSM | Bluetooth Classic, Thread/Zigbee, WiFi 6 |
| ESP32-P4 | 2× RISC-V @ up to 400MHz + LP core | **None** — needs a companion radio chip | Yes — HS OTG + FS OTG | MIPI-DSI/CSI, H.264 encode, up to 32MB in-package PSRAM | Any wireless radio |
| ESP32-C3 | 1× RISC-V @ 160MHz | WiFi 4 + BLE 5 (no Classic) | No | Cheapest/smallest | Second core, native USB, SIMD |
| ESP32-C6 | 1× RISC-V @ 160MHz + LP core | WiFi 6 + BLE 5.3 + Thread/Zigbee | No | Matter-ready radio stack | Second core, native USB, Bluetooth Classic |
| ESP32-C5 | 1× RISC-V @ 240MHz + LP core | WiFi 6 dual-band + BLE 5 + 802.15.4 | No | Only dual-band-WiFi6 variant | Second core, native USB |
| ESP32-H2 | 1× RISC-V @ 96MHz | No WiFi — BLE 5 + Thread/Zigbee only | No | Purpose-built low-power mesh radio | WiFi, second core |

If the user is debugging code copy-pasted from an S3/C-series project, the
most common silent-breakage causes are: Bluetooth Classic APIs that don't
exist on S3/C-series (BLE-only there), and native-USB code (`TinyUSB`,
`USB.begin()` in Arduino) that has nothing to attach to on classic ESP32 —
see "No native USB" below.

## Quick specs

- **CPU**: dual-core Xtensa LX6, up to 240MHz (D0WDQ6/D0WD/D0WDR2 dies —
  single-core S0WD and higher-GPIO D2WD variants exist but aren't known to
  be used by any current M5Stack board)
- **ROM**: 448KB · **SRAM**: 520KB on-chip · **RTC memory**: 16KB (8KB RTC
  FAST + 8KB RTC SLOW), survives deep sleep and hibernation
- **Flash / PSRAM**: not on the bare D0WDQ6/D0WD die — external only, via
  SPI/QSPI/QPI, up to 16MB directly memory-mapped. Boards built on WROVER
  modules (D0WDR2 die) get 2MB of PSRAM bonded into the module package
  instead. See `references/memory-radio.md` for the module-to-die mapping
  and which GPIOs get consumed by external flash/PSRAM wiring.
- **Wireless**: WiFi 4 (802.11b/g/n, 2.4GHz only, up to 150Mbps PHY,
  +20.5dBm TX on 11b / +18dBm on 11n), **Bluetooth v4.2 dual-mode — BR/EDR
  Classic *and* BLE** (the only chip in this family with Bluetooth Classic
  at all; every newer ESP32 variant is BLE-only)
- **USB**: none — see "No native USB" below
- **GPIO**: 34 pins on the bare chip. 6 are input-only (GPIO34–39, no
  internal pull-up/down, can't drive output); 5 are strapping pins that set
  boot mode at reset (GPIO0, GPIO2, GPIO5, GPIO12, GPIO15 — see
  `references/memory-radio.md` for what to avoid wiring to them). How many
  are actually free on a given board depends on the module (external
  flash/PSRAM SPI wiring reserves several) and the board's own routing —
  check that board's `references/pinout.md`.
- **ADC / DAC / touch**: two 12-bit SAR ADC units (18 channels combined);
  **ADC2 cannot be read while WiFi is active** — a very common "why does my
  analog read return -1 / garbage once I call `WiFi.begin()`" report, see
  `references/peripherals.md`. Two 8-bit DAC channels (GPIO25/26). 10
  capacitive touch channels (T0–T9), overlapping several ADC2 pins.
- **AI acceleration**: none — no SIMD/vector extensions and no
  esp-dsp-accelerated instruction set the way S3/P4 have. Software-only
  DSP/ML on this chip is meaningfully slower per clock than on an S3.
- **Security**: Secure Boot, Flash Encryption (AES), 1024-bit OTP (768
  customer-usable bits), AES/SHA/RSA hardware accelerators, plus (V3-and-later
  only) a `UART_DOWNLOAD_DIS` eFuse to permanently disable UART download
  mode. See "Why the V3 revision matters" below and
  `references/memory-radio.md`.
- **Package / operating range**: QFN48 6×6mm (D0WDQ6) or 5×5mm (D0WD),
  –40°C to 125°C ambient (bare-die rating for the no-in-package-memory
  variants), 2.3V–3.6V supply.

## No native USB

Unlike every S3/P4/S2 board, classic ESP32 has **no USB peripheral at
all** — no OTG, no USB-Serial-JTAG. Every M5Stack classic-ESP32 board's USB
connector goes through a separate USB-to-UART bridge chip (commonly a
CP2104/CP2102N or CH9102) wired to the ESP32's UART0, plus a small
auto-reset circuit (DTR/RTS driving EN and GPIO0) that's what makes
`esptool`/Arduino uploads "just work" without a manual boot-button press.
If a user pastes `USB.begin()`, TinyUSB, or any native-USB Arduino/ESP-IDF
code onto a classic-ESP32 board, it will not compile against this target
(or will silently no-op on some porting shims) — there is no hardware for
it to talk to. Point them at the board's own UART/Serial APIs instead.

## Peripheral capability map

Full detail, with typical use cases and gotchas, is in
`references/peripherals.md`. Quick index of what's covered there:

| Peripheral | For |
|---|---|
| RMT | Precisely-timed signal generation/capture — IR remotes, WS2812/NeoPixel, custom one-wire-style protocols |
| LEDC | PWM — LED dimming, buzzers/tone generation, simple motor speed control |
| I2S | Digital audio in/out, and (distinctively on this chip) parallel 8/16-bit camera input — the mechanism ESP32-CAM-style modules use |
| ADC / DAC / touch | Analog in/out and touch sensing — including the ADC2-vs-WiFi conflict |
| PCNT | Hardware pulse counting — rotary encoders, flow meters, tachometers |
| MCPWM | Motor control PWM — H-bridges, ESCs, servo-adjacent timing |
| TWAI | CAN bus (automotive/industrial protocols) |
| SDMMC host / SD-SPI | SD card access as a host |
| SDIO slave | The ESP32 acting as a WiFi/BT co-processor *to* another host SoC over SDIO — a niche but real use case unique to this chip in the family |
| Hall sensor | Built in, but **deprecated and removed from ESP-IDF 5.0+ APIs** — don't build new designs around it |
| GPTimer / dedicated GPIO | General-purpose hardware timers; low-latency bit-banged GPIO |

## Power management

Five power modes (Active, Modem-sleep, Light-sleep, Deep-sleep,
**Hibernation** — this chip has a lower-power state below deep sleep that
S3/P4 don't expose the same way), wake sources, and the single ULP-FSM
coprocessor (this chip does **not** have ULP-RISC-V — that was introduced
starting with S2/S3) are in `references/power-sleep-ulp.md`. Read this
before telling a user "just call `esp_deep_sleep_start()`" if they actually
need something to keep running (a sensor poll, a timer) while the main
cores are off, or if they're trying to squeeze below deep-sleep current and
don't need any wake logic smarter than a timer or a couple of RTC GPIOs.

## Memory, module variants, radio coexistence, and security/errata

Which module (WROOM vs. WROVER) maps to which bare die, what external
flash/PSRAM wiring costs in GPIOs, WiFi/Bluetooth Classic/BLE coexistence
behavior, and the V3-revision errata fixes/security hardening are all in
`references/memory-radio.md`.

## Why the V3 chip revision matters

If a user's part number or `esp_chip_info()` output says anything with
`-V3` (as in ESP32-D0WDQ6-**V3**), or ESP-IDF logs a chip revision of
`v3.0`/`v3.1` at boot, that silicon includes fixes over v1.0 for: spurious
watchdog resets around power-up/deep-sleep wake, PSRAM cache read/write
errors under certain access sequences, simultaneous-multi-CPU
cross-address-space read errors, crystal oscillator startup stability, a
lowered TWAI minimum baud rate (12.5kHz vs. 25kHz on v1.0), and secure
boot/flash-encryption fault-injection vulnerabilities (CVE-2019-17391,
CVE-2019-15894). Firmware built for v1.0 silicon still runs on v3.0 boards
without recompiling, but ESP-IDF's "Minimum Supported ESP32 Revision"
menuconfig option lets a project target v3.0-and-up exclusively to use the
fixes/lowered-baud-rate behavior unconditionally. Practically: essentially
every classic-ESP32 M5Stack board sold today ships V3 (or later) silicon,
since it's been in mass production since ~2019 — this mostly matters for
someone debugging old stock, a secondhand board, or a very specific errata
symptom, not for day-to-day firmware work.

## Which M5Stack boards use this chip

Core2 (incl. v1.1, v1.3, For AWS) is **confirmed** classic ESP32
(`ESP32-D0WDQ6-V3`). The following are likely but not independently
verified against a schematic — treat as "probable" until a Controller skill
for that specific board confirms it: Basic (v2.7), Fire (v2.7), M5GO IoT
Kit (v2.7), Tough, StickC-Plus (incl. SE), Atom-Lite, Atom-Matrix (v1.1),
the base Atom Voice, Stamp-Pico (incl. Mate, DIY Kit), CoreInk, Paper
(v1.1), and PowerHub. Boards with PSRAM (Core2, Fire, Tough, and similar)
are almost certainly built on WROVER modules (D0WDR2 die); boards without
likely use WROOM modules (D0WDQ6 die) — confirm per-board when that
Controller's own skill gets built.

## Official resources

- Datasheet (PDF): https://documentation.espressif.com/esp32_datasheet_en.pdf
- Chip Revision v3.0 errata/user guide (PDF): https://documentation.espressif.com/esp32_chip_revision_v3_0_user_guide_en.pdf
- Product page: https://www.espressif.com/en/products/socs/esp32
- ESP32-WROOM-32 module datasheet: https://documentation.espressif.com/esp32-wroom-32_datasheet_en.html
- ESP-IDF peripherals API reference (esp32 target): https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/index.html
- Sleep modes: https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/system/sleep_modes.html
- ULP-FSM coprocessor programming: https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/system/ulp.html
- ADC driver (incl. ADC2/WiFi note): https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/adc_oneshot.html
- SDMMC host driver: https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/sdmmc_host.html
- SDIO slave driver: https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/sdio_slave.html
- RF coexistence (WiFi/Bluetooth): https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-guides/coexist.html
- Flash/PSRAM configuration: https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-guides/flash_psram_config.html

## Working with the user

- If they're getting compile/link errors from Bluetooth Classic (BR/EDR)
  code on an S3/C-series board, or from native-USB code on *this* chip,
  the "Not ESP32-S3..." table and "No native USB" section above are almost
  certainly the cause.
- If an ADC reading is stuck, noisy, or returns an error only after WiFi
  connects, check whether that pin is on ADC2 before assuming the sensor
  or wiring is bad — see `references/peripherals.md`.
- If they mention the Hall sensor (`hallRead()` or similar), tell them it's
  deprecated and removed from ESP-IDF 5.0+'s public API — steer them to an
  external magnetic sensor for anything beyond a legacy codebase.
- If they want something to keep running during sleep (a timer, a sensor
  poll) rather than just "wake up periodically and do work," point them at
  the ULP-FSM coprocessor in `references/power-sleep-ulp.md` — and note it
  only supports a restricted assembly-like language, not full C, unlike the
  ULP-RISC-V on S2/S3.
- If they're combining WiFi and Bluetooth Classic/BLE and seeing flaky
  behavior, check `references/memory-radio.md`'s coexistence section
  before assuming it's an application bug.
- If the user cites a chip revision (V1/V3, or `esp_chip_info()` output),
  see "Why the V3 chip revision matters" above before assuming a bug report
  applies to their specific board.
- This is chip-level guidance, cross-checked against Espressif's own
  datasheet, chip-revision errata guide, and ESP-IDF docs at time of
  writing — but ESP-IDF version-to-version API changes happen (the Hall
  sensor removal in 5.0 is a good example). If the user hits a compile
  error on a specific function signature, point them at the current
  ESP-IDF docs for their target version rather than assuming this file is
  byte-exact.
