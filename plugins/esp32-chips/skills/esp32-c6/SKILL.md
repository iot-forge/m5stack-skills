---
name: esp32-c6
description: Chip-level ESP-IDF capability reference for the ESP32-C6 SoC (single-core RISC-V HP core + RISC-V LP core, WiFi 6 + BLE 5.3 + Thread/Zigbee) — what the chip can do, distinct from any board's wiring. Use when a user wants to exploit ESP32-C6 hardware — WiFi 6/BLE/802.15.4 radio coexistence (Thread Border Router, Zigbee gateway, Matter endpoints, why it's time-division not simultaneous), the LP core (a real always-available RISC-V coprocessor, not a restricted ULP-FSM), RMT/LEDC/I2S/ADC/PCNT/MCPWM/dual-TWAI peripherals, SD-SPI-only storage (no SDMMC host, no eMMC), deep sleep/wake sources, and why there's no PSRAM and no native USB OTG on this chip. Trigger on "how do I use WiFi 6/Thread/Zigbee/LP core/deep sleep on an ESP32-C6", radio-coexistence or Matter/Thread/Zigbee questions, or any M5Stack C6 board (NanoC6, Stamp C6LoRa, Tab5's C6 radio co-processor, Stamp-P4's AddOn C6) needing depth beyond its own SKILL.md. For pinouts/wiring use that board's skill — this is the shared chip layer it points into.
---

# ESP32-C6 chip capabilities

This skill is the **chip layer**, not a board layer. A board skill (e.g. a
future `m5stack-nanoc6`) tells you what's wired to what on one specific
product; this skill tells you what the ESP32-C6 silicon itself can do — the
peripherals, low-power modes, memory options, and (most distinctively)
three-radio behavior that are the same on every ESP32-C6 board regardless
of vendor. Read a board's own skill first for pin numbers and I2C
addresses, then come here when the user wants to go deeper on a capability
than "call the vendor's high-level library and move on" — e.g. diagnosing
WiFi+Thread coexistence packet loss, offloading an always-on task to the LP
core, or figuring out why SD card code ported from another ESP32 chip won't
compile.

## The one thing every ESP32-C6 user needs to know: three radios, one antenna, time-shared

The C6 is Espressif's first WiFi 6 chip, and it packs **three separate
wireless protocols — WiFi 6, Bluetooth LE 5.3, and 802.15.4 (Thread 1.3 +
Zigbee 3.0 certified) — behind a single shared RF front-end and antenna.**
They are **time-division multiplexed, not simultaneous**: per Espressif's
own coexistence docs, "a module cannot receive or transmit data while
another module is engaged in data transmission or reception." This is fine
for light, bursty use (WiFi telemetry plus occasional BLE provisioning) but
becomes a real design constraint for continuous-reception roles like a
Thread Border Router or Zigbee gateway sharing the radio with active WiFi —
see `references/memory-radio.md` for the practical coexistence behavior and
Espressif's own recommendation to use a **dual-SoC** design (e.g. an
ESP32-S3 or classic ESP32 for WiFi/BLE, paired with a separate ESP32-H2 or
this chip dedicated to 802.15.4) for a production WiFi-backed Border
Router/gateway rather than relying on one C6 doing all three at once.

This is also why M5Stack uses the C6 two different ways in its own catalog:
as a **standalone MCU** with its own application code (NanoC6, Stamp
C6LoRa), and as a **dedicated radio co-processor** for a separate,
radio-less main SoC (the ESP32-C6-MINI-1U on Tab5, talking to Tab5's
ESP32-P4 over SDIO; Stamp-P4's "AddOn C6 For P4" is the same pattern). Both
are the same chip and everything in this skill applies to either role — the
co-processor case just means the C6's own application code is usually
Espressif's `esp-hosted` firmware (or similar) rather than user logic, with
the *host* chip's skill (e.g. `esp32-p4`) being where a user's actual
WiFi/BLE application code lives.

## Not classic ESP32, not S2/S3, not C3/C5, not H2, not P4

M5Stack (and the ESP32 family generally) spans several very different chips
that are easy to conflate. Get this wrong and code silently targets the
wrong architecture or assumes a peripheral that doesn't exist.

| Chip | Cores / arch | Wireless | Native USB | Notable extras | Not on this chip |
|---|---|---|---|---|---|
| **ESP32-C6** (this skill) | 1× RISC-V (RV32IMAC) HP core @ up to 160MHz, 4-stage pipeline + 1× RISC-V LP core @ up to ~20MHz | WiFi 6 (802.11ax, 2.4GHz only) + BLE 5.3 + Thread/Zigbee (802.15.4) — one shared RF front-end, time-division multiplexed | No — USB-Serial-JTAG only (fixed-function console/flash/debug; no OTG, no custom device classes) | First ESP32 with WiFi 6, Matter-ready three-radio stack, LP core is a genuine RISC-V coprocessor usable *while the HP core is fully active*, 2 independent TWAI/CAN controllers | Second HP core, native USB OTG, PSRAM (none, ever — bare chip or any module variant), hardware FPU, SDMMC host (SD-SPI only, no eMMC), capacitive touch sensing |
| ESP32-S3 | 2× Xtensa LX7 @ up to 240MHz + 1 low-power coprocessor core | WiFi 4 + BLE 5 | Yes — OTG (full-speed) + separate USB-Serial-JTAG | SIMD/vector AI instructions, ULP-RISC-V *and* ULP-FSM | Thread/Zigbee/802.15.4, WiFi 6, MIPI-DSI/CSI, hardware video codecs |
| ESP32 (classic) | 2× Xtensa LX6 @ 240MHz | WiFi 4 + Bluetooth Classic + BLE 4.2 | No | Widest library/example coverage, oldest silicon, Bluetooth Classic | Native USB, SIMD extensions, ULP-RISC-V, WiFi 6, Thread/Zigbee |
| ESP32-S2 | 1× Xtensa LX7 @ 240MHz | WiFi 4 only, **no Bluetooth at all** | Yes — OTG | Very low deep-sleep current | Second core, Bluetooth |
| ESP32-C3 | 1× RISC-V @ 160MHz | WiFi 4 + BLE 5 | No | Cheapest/smallest | Second core, native USB, SIMD, Thread/Zigbee |
| ESP32-C5 | 1× RISC-V @ 240MHz + LP core | WiFi 6 **dual-band (2.4+5GHz)** + BLE 5 + 802.15.4 | No | Only dual-band-WiFi6 ESP32 variant | Second core, native USB |
| ESP32-H2 | 1× RISC-V @ 96MHz | **No WiFi** — BLE 5 + Thread/Zigbee only | No | Purpose-built low-power mesh/Matter radio; Espressif's other half of the "dual-SoC Border Router" recommendation | WiFi entirely, second core |
| ESP32-P4 | 2× RISC-V @ up to 400MHz + LP core | **None** — always pairs with a companion chip (M5Stack's Tab5/Stamp-P4 use this chip, the C6) | Yes — HS OTG + FS OTG | MIPI-DSI/CSI, H.264 encode, up to 32MB in-package PSRAM | Any wireless radio |

## Quick specs

- **HP (High-Performance) core**: 1× 32-bit RISC-V (RV32IMAC — integer,
  multiply/divide, atomic, compressed; **no hardware FPU**), 4-stage
  pipeline, up to 160MHz. Single core — there is no PRO_CPU/APP_CPU split
  the way S3/P4/classic ESP32 have; see `references/memory-radio.md` for
  what that means for concurrency.
- **LP (Low-Power) core**: 1× 32-bit RISC-V (same RV32IMAC ISA), 2-stage
  pipeline, up to ~20MHz — a genuine coprocessor that can run independently
  of, and *concurrently with*, the HP core, not just during sleep. See
  `references/power-sleep-lp.md`.
- **Memory**: 320KB ROM, 512KB HP SRAM, 16KB LP SRAM (retained in deep
  sleep, and the LP core's own working memory)
- **PSRAM: none.** Not on the bare chip, and no module variant embeds any —
  unlike ESP32-S3/P4, there is no in-package PSRAM option for this chip at
  all. Don't assume `ESP.getPsramSize()`/`esp_get_free_heap_size()` will
  ever return nonzero PSRAM on a C6 board. See `references/memory-radio.md`.
- **Flash**: in-package on the `ESP32-C6FH4` (4MB) / `ESP32-C6FH8` (8MB)
  chip variants (Quad SPI), or external up to 16MB via SPI on modules built
  around the bare `ESP32-C6` part. 6 GPIOs are dedicated to this flash
  connection and not available for general use.
- **Wireless**: WiFi 6 (802.11ax, 2.4GHz only, up to 150Mbps PHY, OFDMA +
  downlink MU-MIMO + Target Wake Time), Bluetooth LE 5.3 (coded PHY for
  extended range, 2Mbps high-throughput mode, up to +20dBm TX), and 802.15.4
  radio (Thread 1.3 and Zigbee 3.0 certified, 250kbps) — see "three radios,
  one antenna" above and `references/memory-radio.md` for coexistence
  behavior.
- **USB**: no native OTG — only the fixed-function USB-Serial-JTAG
  controller (serial console + flashing + JTAG debugging over one USB
  connection, entirely hardware-implemented and **not reconfigurable** into
  any other USB device class). If a user wants a board to present as a
  custom HID/MSC/composite USB device, that's not possible on this chip —
  point them at an S3 or P4 instead.
- **GPIO**: 30 pins (QFN40 package) or 22 pins (QFN32 package). 5 strapping
  pins (GPIO8, GPIO9, GPIO15, plus the MTMS/MTDI JTAG-shared pins) set boot
  mode at reset — check the current datasheet's strapping table before
  wiring anything to them at board-design time. GPIO0–7 (8 pins) are the
  RTC/LP-capable GPIOs, usable as deep-sleep wake sources and as the LP
  core's own `LP_IO` peripheral pins.
- **Storage**: no SDMMC host controller on this chip at all — SD cards are
  only reachable via SD-SPI (the SD protocol run over a regular SPI
  peripheral), and **no eMMC support** (eMMC requires the parallel SDMMC
  protocol this chip doesn't have). Also has a separate SDIO **slave**
  controller for acting as a co-processor to a host SoC (see "three radios"
  above) — don't confuse SDIO slave with an SD-card-host capability, they're
  unrelated peripherals. See `references/peripherals.md`.
- **Security**: AES-128/256, ECC (P-192/P-256), HMAC-SHA-256, RSA up to
  3072-bit + RSA Digital Signature, SHA-1/224/256, external-memory XTS-AES
  encryption, hardware TRNG, Secure Boot and Flash Encryption — not detailed
  further here, see ESP-IDF's security guides if the user needs this.
- **Package / operating range**: QFN40 (5×5mm) or QFN32 (5×5mm), –40°C to
  105°C (some module SKUs are rated to 85°C standard / 105°C extended —
  check the specific module datasheet).
- **Power modes**: Active, Modem-sleep, Light-sleep, Deep-sleep (~7µA) — see
  `references/power-sleep-lp.md`.

## Peripheral capability map

Full detail, with typical use cases and gotchas, is in
`references/peripherals.md`. Quick index of what's covered there:

| Peripheral | For |
|---|---|
| RMT | Precisely-timed signal generation/capture — IR remotes, WS2812/NeoPixel, custom one-wire-style protocols |
| LEDC | PWM — LED dimming, buzzers/tone generation, simple motor speed control |
| I2S | Digital audio in/out (mic, speaker, codec chips) — one controller only |
| ADC | Analog sensing — one SAR ADC unit, no ADC1/ADC2 split the way classic ESP32/S3 have |
| PCNT | Hardware pulse counting — rotary encoders, flow meters, tachometers |
| MCPWM | Motor control PWM — H-bridges, ESCs, servo-adjacent timing |
| TWAI | **Two** independent CAN 2.0-compatible controllers — more than any other chip in this family |
| SD-SPI / SDIO slave | SD card access (SPI-only, no SDMMC host, no eMMC) and acting as a radio co-processor to a host SoC — two unrelated peripherals, don't conflate them |
| PARLIO | General-purpose parallel I/O — not a display/camera peripheral, see below |
| SDM | Sigma-delta modulation — lightweight analog-ish PWM-density output |
| GPTimer / dedicated GPIO | General-purpose hardware timers; low-latency bit-banged GPIO |
| Temperature sensor | Internal die temperature (not ambient) |
| No LCD/camera hardware | No parallel (I80/RGB) LCD interface, no MIPI-DSI/CSI — displays are SPI/I2C only via the generic `esp_lcd` component |
| No capacitive touch | Unlike classic ESP32/S3/P4, this chip has no built-in touch-sensing peripheral |

## Power management: LP core is a real coprocessor, not a limited ULP-FSM

Light sleep, deep sleep, wake sources, and the LP core (a genuine RISC-V
core that runs normal compiled C, can access LP UART/LP I2C/LP GPIO/LP
Timer directly, and — unlike older chips' ULP-FSM — can run continuously
even while the HP core is fully active) are all in
`references/power-sleep-lp.md`. Because this chip has only one HP core,
offloading an always-on background task (a sensor poll loop, a
watchdog, a slow UART listener) to the LP core is especially valuable here —
it doesn't compete with the single HP core's FreeRTOS scheduler at all, not
even for a slice of time. Read this before telling a user "just call
`esp_deep_sleep_start()`" if they actually need something running in the
background.

## Memory and radio coexistence

Why there's no PSRAM (ever, on any variant), which GPIOs the in-package
flash costs, the mechanics of the WiFi 6/BLE/802.15.4 time-sharing
(including Espressif's own dual-SoC recommendation for Border
Router/gateway use cases), and pointers to the Zigbee/Thread/Matter
software stacks are all in `references/memory-radio.md`.

## Which M5Stack boards use this chip

**NanoC6** is confirmed ESP32-C6FH4-based (verified against M5Stack's own
product page). **Tab5** is confirmed to use this chip as its
ESP32-C6-MINI-1U wireless co-processor — see the `m5stack-tab5` skill; the
C6 itself is not Tab5's main application SoC, that's the ESP32-P4 (see the
`esp32-p4` skill). **Stamp C6LoRa** and **Stamp-P4's "AddOn C6 For P4"**
are likely matches by name, not yet independently verified.

## Official resources

- Datasheet: https://documentation.espressif.com/esp32-c6_datasheet_en.html
- Product page: https://www.espressif.com/en/products/socs/esp32-c6
- ESP32-C6-MINI-1 / MINI-1U module datasheet: https://documentation.espressif.com/esp32-c6-mini-1_mini-1u_datasheet_en.html
- ESP-IDF API reference (esp32c6 target): https://docs.espressif.com/projects/esp-idf/en/stable/esp32c6/api-reference/index.html
- Sleep modes: https://docs.espressif.com/projects/esp-idf/en/stable/esp32c6/api-reference/system/sleep_modes.html
- LP Core / ULP-LP-core programming: https://docs.espressif.com/projects/esp-idf/en/stable/esp32c6/api-reference/system/ulp-lp-core.html
- USB Serial/JTAG console: https://docs.espressif.com/projects/esp-idf/en/stable/esp32c6/api-guides/usb-serial-jtag-console.html
- RF coexistence (WiFi/BLE/802.15.4): https://docs.espressif.com/projects/esp-idf/en/stable/esp32c6/api-guides/coexist.html
- SD/SDIO/MMC driver (confirms SD-SPI-only, no SDMMC host): https://docs.espressif.com/projects/esp-idf/en/stable/esp32c6/api-reference/storage/sdmmc.html
- TWAI (confirms 2 independent controllers): https://docs.espressif.com/projects/esp-idf/en/stable/esp32c6/api-reference/peripherals/twai.html
- ESP-Zigbee SDK: https://github.com/espressif/esp-zigbee-sdk
- ESP Thread Border Router: https://github.com/espressif/esp-thread-br
- OpenThread's ESP32 Border Router guide: https://openthread.io/guides/border-router/espressif-esp32

## Working with the user

- If they're getting PSRAM-related errors or unexpectedly low free heap on
  code ported from an S3/P4 project, check "Quick specs" above first — this
  chip has no PSRAM on any variant, full stop, not a config flag to enable.
- If they're combining WiFi with Thread/Zigbee (a Border Router, a Zigbee
  gateway, or any continuous-reception 802.15.4 role) and seeing packet
  loss or instability, that's very likely the shared-antenna time-sharing
  described in `references/memory-radio.md`, not an application bug —
  Espressif's own guidance is a dual-SoC design for production use of that
  kind, not asking one C6 to do all three radios reliably at once.
- If they want a custom USB device (HID keyboard, MSC mass storage, a
  composite device) or ask why `TinyUSB`/`USB.begin()`-style code doesn't
  do what it did on their S3/P4 board, tell them plainly this chip has no
  native USB OTG — only the fixed-function Serial/JTAG controller.
- If they're trying to mount an SD card or (especially) an eMMC chip using
  SDMMC-host-style code from another ESP32 target, this chip has no SDMMC
  host peripheral — SD-SPI only, and eMMC isn't possible at all.
- If they want something to keep running in the background — not just
  during deep sleep, but genuinely alongside normal operation without
  spending the single HP core's FreeRTOS scheduler on it — point them at
  the LP core in `references/power-sleep-lp.md` rather than a
  low-priority FreeRTOS task.
- This is chip-level guidance, cross-checked against Espressif's own
  datasheet and ESP-IDF docs at time of writing — but ESP-IDF
  version-to-version API and coexistence-behavior changes happen. If the
  user hits a compile error on a specific function signature or a
  coexistence-behavior discrepancy, point them at the current ESP-IDF docs
  for their exact version rather than assuming this file is byte-exact.
