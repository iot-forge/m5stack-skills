---
name: esp32-p4
description: Chip-level ESP-IDF capability reference for the ESP32-P4 SoC (dual-core RISC-V HP cores + a RISC-V LP core) — what the chip can do, distinct from any board's wiring. Use when a user wants to exploit ESP32-P4 hardware — MIPI-CSI/DSI with the on-chip ISP, hardware JPEG encode/decode, hardware H.264 encode, PPA/2D-DMA image acceleration, the LP core and its own peripherals, USB HS OTG vs FS OTG vs USB-Serial-JTAG, TWAI/CAN, Ethernet MAC, SDIO host, in-package PSRAM up to 32MB, HP-core task pinning, and the PIE instruction extensions behind on-device AI/DSP. Trigger on MIPI-CSI/MIPI-DSI/camera/ISP/JPEG/H.264/PPA/LP-core/deep-sleep/PSRAM/USB-HS-OTG questions on an ESP32-P4, or any M5Stack P4 board (Tab5, Stamp-P4) needing depth beyond its own SKILL.md. For pinouts/wiring use that board's skill. Also relevant when a user asks why their ESP32-P4 board has no WiFi/Bluetooth and needs a companion radio chip.
---

# ESP32-P4 chip capabilities

This skill is the **chip layer**, not a board layer. A board skill (e.g.
`m5stack-tab5`) tells you what's wired to what on one specific product; this
skill tells you what the ESP32-P4 silicon itself can do — the peripherals,
multimedia hardware, low-power modes, memory options, and concurrency model
that are the same on every ESP32-P4 board regardless of vendor. Read a
board's own skill first for pin numbers and I2C addresses, then come here
when the user wants to go deeper on a capability than "call the vendor's
high-level library and move on" — e.g. driving the MIPI camera pipeline,
encoding H.264 in hardware, using the LP core while the main system sleeps,
or getting real throughput out of USB HS OTG.

## The one thing every ESP32-P4 user needs to know: no radio, ever

Unlike every other current ESP32 variant, **the P4 has zero wireless
hardware** — no WiFi, no Bluetooth, no Thread/Zigbee/802.15.4. This isn't a
stripped-down SKU; the chip was designed as a high-performance
applications/HMI processor and pairs with a separate radio chip (an
ESP32-C6 on M5Stack's Tab5 and Stamp-P4, most commonly) over SDIO or SPI
when a project needs wireless. If a user asks "why won't `WiFi.begin()`
compile/link" or "how do I get WiFi on my P4 board," the answer is always
"it needs a companion radio chip and a host-side driver (ESP-Hosted or
similar) talking to it" — not a missing library or wrong board setting. See
that board's own skill (e.g. the `m5stack-tab5` skill's "WiFi needs pin
setup" section) for the actual wiring/init pattern on a specific product.

## Not classic ESP32, not S2/S3, not C3/C6/C5, not H2

M5Stack (and the ESP32 family generally) spans several very different chips
that are easy to conflate. Get this wrong and code silently targets the
wrong architecture or assumes a peripheral that doesn't exist.

| Chip | Cores / arch | Wireless | Native USB | Notable extras | Not on this chip |
|---|---|---|---|---|---|
| **ESP32-P4** (this skill) | 2× RISC-V HP cores @ up to 400MHz + 1× RISC-V LP core @ up to 40MHz | **None** — always pairs with a companion chip (M5Stack's Tab5/Stamp-P4 use a C6) | Yes — USB 2.0 **HS** OTG *and* a separate FS OTG, both with integrated PHY | MIPI-CSI+ISP, MIPI-DSI, hardware JPEG enc/dec, hardware H.264 encode, PPA + 2D-DMA, Ethernet MAC, PIE AI/DSP instruction extensions, up to 32MB in-package PSRAM | Any wireless radio, Xtensa SIMD (esp-dsp/ESP-DL use PIE instead, see below) |
| ESP32-S3 | 2× Xtensa LX7 @ up to 240MHz + 1 low-power coprocessor core | WiFi 4 + BLE 5 | Yes — OTG (full-speed only) + separate USB-Serial-JTAG | Xtensa SIMD/vector AI instructions, ULP-RISC-V *and* ULP-FSM | Thread/Zigbee/802.15.4, WiFi 6, MIPI-DSI/CSI, hardware video codecs |
| ESP32 (classic) | 2× Xtensa LX6 @ 240MHz | WiFi 4 + Bluetooth Classic + BLE 4.2 | No | Widest library/example coverage, oldest silicon | Native USB, SIMD extensions, ULP-RISC-V |
| ESP32-S2 | 1× Xtensa LX7 @ 240MHz | WiFi 4 only, **no Bluetooth at all** | Yes — OTG | Very low deep-sleep current | Second core, Bluetooth |
| ESP32-C3 | 1× RISC-V @ 160MHz | WiFi 4 + BLE 5 | No | Cheapest/smallest | Second core, native USB, SIMD |
| ESP32-C6 | 1× RISC-V @ 160MHz + LP core | WiFi 6 (2.4GHz) + BLE 5.3 + Thread/Zigbee (802.15.4) | No | First ESP32 with WiFi 6 + Matter-ready radio stack — this is the P4's usual wireless companion | Second core, native USB, hardware FPU |
| ESP32-C5 | 1× RISC-V @ 240MHz + LP core | WiFi 6 **dual-band (2.4+5GHz)** + BLE 5 + 802.15.4 | No | Only dual-band-WiFi6 ESP32 variant | Second core, native USB |
| ESP32-H2 | 1× RISC-V @ 96MHz | **No WiFi** — BLE 5 + Thread/Zigbee only | No | Purpose-built low-power mesh/Matter radio | WiFi entirely, second core |

If the user's board pairs an ESP32-P4 with a companion radio chip (the case
for every current M5Stack P4 board), that companion chip is out of this
skill's scope — for the ESP32-C6 specifically, see the `esp32-c6` skill in
this same plugin.

## Quick specs

- **HP (High-Performance) cores**: 2× 32-bit RISC-V, 5-stage pipeline, up to
  400MHz, single-precision FPU, PIE AI/DSP instruction extensions (see
  `references/memory-concurrency-ai.md`)
- **LP (Low-Power) core**: 1× 32-bit RISC-V, 2-stage pipeline, up to 40MHz —
  a real coprocessor that can run independently, including while the HP
  cores are active, not just during sleep (see `references/power-sleep-lp.md`)
- **On-chip memory**: 768KB HP L2 SRAM, 128KB HP ROM, 32KB LP SRAM, 16KB LP
  ROM, 8KB zero-wait-state TCM
- **PSRAM**: not on the bare die — many module variants embed it in-package
  (e.g. `ESP32-P4NRW16`/`ESP32-P4NRW32` = 16MB/32MB Octal, 1.8V); check the
  specific module before assuming a size. M5Stack's Tab5 uses the 32MB
  variant.
- **Flash**: external only, SPI/Dual/Quad/QPI, up to 64MB
- **GPIO**: up to 55 pins on the bare chip (5 are strapping pins); 15 are
  LP/RTC-capable (usable as deep-sleep wake sources and by the LP core) —
  how many are actually free depends on the module and the board, check
  that board's `references/pinout.md`
- **USB**: three independent USB-capable blocks sharing no pins with each
  other — a true USB 2.0 **High-Speed** OTG (480Mbps, integrated PHY), a
  separate USB 2.0 Full-Speed OTG (also integrated PHY), and a
  USB-Serial-JTAG controller. This is a bigger deal than it sounds — see
  `references/usb.md`, most USB confusion on this chip traces back to which
  of the three a board's connector(s) are wired to.
- **Display/camera**: MIPI-DSI (display out) and MIPI-CSI (camera in) with
  an integrated ISP, plus legacy parallel (DVP) display and camera
  interfaces for non-MIPI panels/sensors — up to 1080p on both. See
  `references/multimedia-vision.md`.
- **Hardware video/image codecs**: JPEG encode *and* decode (one at a time,
  not simultaneously), and H.264 **hardware encode** (software decode only)
  up to 1080p30 — plus a PPA (Pixel Processing Accelerator) and 2D-DMA for
  GPU-free image scaling/rotation/blending. See
  `references/multimedia-vision.md`.
- **Wireless**: none — see "no radio, ever" above
- **Ethernet**: one MAC (EMAC), RMII mode — needs an external PHY chip, the
  P4 doesn't have one built in
- **Storage interfaces**: SDIO/SD/MMC host controller, plus the usual SPI
  flash and (via GPIO) SD-SPI fallback
- **Other peripherals**: 5 UART + 1 LP UART, 4 SPI + 1 LP SPI, 2 I2C + 1 LP
  I2C + 1 analog I2C, 1 I3C controller, 3 I2S + 1 LP I2S, 1 TWAI/CAN, 1
  RMT, 1 LEDC, 1 MCPWM, 1 PCNT, 1 PARLIO (parallel IO), 1 BitScrambler, 14
  touch channels, 2 ADC controllers (8+6 channels), internal temperature
  sensor, VAD (voice activity detection) unit — full detail and typical use
  cases in `references/peripherals.md`
- **Security**: Secure Boot, Flash Encryption (XTS-AES), AES/ECC/HMAC/RSA/SHA
  accelerators, RSA/ECDSA digital-signature peripherals, TRNG, a Key
  Manager with SRAM-PUF-derived HUK, and permission-control (PMS) hardware
  access protection — not detailed further in this skill, see ESP-IDF's
  security guides if the user needs this
- **Package**: QFN104 (10×10mm), -40°C to 85°C

## Peripheral capability map

Full detail, with typical use cases and gotchas, is in
`references/peripherals.md`. Quick index of what's covered there: RMT,
LEDC, I2S, ADC, capacitive touch, PCNT, MCPWM, TWAI, SDMMC/SD-SPI/SDIO host,
GPTimer, Ethernet MAC, I3C, PARLIO, BitScrambler, and the multi-instance
UART/SPI/I2C story.

## Multimedia and vision: the P4's headline feature

MIPI-CSI camera input with an integrated ISP, MIPI-DSI display output,
hardware JPEG encode/decode, hardware H.264 encode, and the PPA/2D-DMA image
accelerators are what actually distinguish this chip from an ESP32-S3 for
most projects — this is why M5Stack picked it for the Tab5's 1280x720
display and camera. Full detail, including throughput numbers and the
encode/decode asymmetry (hardware JPEG both ways, but H.264 hardware-encode
/ software-decode only), is in `references/multimedia-vision.md`.

## Power management: two very different low-power stories

Light sleep / deep sleep and their wake sources work broadly like other
ESP32 chips, but the P4's **LP core is not a limited ULP-FSM-style
coprocessor** — it's a genuine RISC-V core with its own UART/I2C/SPI/I2S/GPIO
peripherals, a debug module, and an interrupt controller, and it's capable
of running **while the HP cores are fully active**, not just during sleep.
Full detail in `references/power-sleep-lp.md` — read this before telling a
user "just call `esp_deep_sleep_start()`" if they actually want an
always-on background task offloaded from the HP cores.

## USB: three controllers, not two

The P4 doubles down on USB relative to the S3 — see "Quick specs" above.
Full detail on which controller does what, default pin assignments, and the
current-firmware limitation that only one of the two OTG controllers can be
in Host mode at a time, is in `references/usb.md`.

## Memory, concurrency, and on-device AI

In-package PSRAM variants and flash config, HP-core task pinning, and the
PIE (Processor Instruction Extensions) SIMD instructions that back
esp-dsp/esp-dl/esp-tflite-micro on this chip (P4 doesn't share the S3's
Xtensa TIE-based SIMD — it's a different ISA extension with its own
instruction prefix) are in `references/memory-concurrency-ai.md`.

## Which M5Stack boards use this chip

**Tab5** is confirmed ESP32-P4-based (paired with an ESP32-C6 radio
co-processor — see the `m5stack-tab5` skill). **Stamp-P4** (with its
"AddOn C6 For P4") is a likely match by name, not yet independently
verified. No other current M5Stack Controller uses this chip.

## Official resources

- Datasheet: https://documentation.espressif.com/esp32-p4_datasheet_en.html
- Product page: https://www.espressif.com/en/products/socs/esp32-p4
- ESP-IDF API reference (esp32p4 target): https://docs.espressif.com/projects/esp-idf/en/stable/esp32p4/api-reference/index.html
- Sleep modes: https://docs.espressif.com/projects/esp-idf/en/stable/esp32p4/api-reference/system/sleep_modes.html
- LP Core / ULP programming: https://docs.espressif.com/projects/esp-idf/en/stable/esp32p4/api-reference/system/ulp.html
- USB Host (DWC_OTG, both OTG controllers): https://docs.espressif.com/projects/esp-idf/en/stable/esp32p4/api-reference/peripherals/usb_host.html
- USB Serial/JTAG console: https://docs.espressif.com/projects/esp-idf/en/stable/esp32p4/api-guides/usb-serial-jtag-console.html
- Camera controller / ISP driver: https://docs.espressif.com/projects/esp-idf/en/stable/esp32p4/api-reference/peripherals/camera_driver.html
- JPEG encoder/decoder: https://docs.espressif.com/projects/esp-idf/en/stable/esp32p4/api-reference/peripherals/jpeg.html
- H.264 component (esp-h264-component) usage guide: https://developer.espressif.com/blog/2025/07/esp-h264-use-tips/
- PIE (AI/DSP instruction extensions) introduction: https://developer.espressif.com/blog/2024/12/pie-introduction/
- Hardware design guidelines (schematic checklist, USB PHY/pin notes): https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32p4/schematic-checklist-esp32p4.html

## Working with the user

- If they're getting compile/link errors from WiFi/BLE code copy-pasted
  from an S3/C3/C6 project, the "no radio, ever" section above is almost
  certainly the cause — check whether their board has a companion radio
  chip and whether they're using its host-side driver, not a missing
  library.
- If they're getting compile/link errors from code copy-pasted for a
  different ESP32 variant otherwise, check the "Not classic ESP32..." table
  above first — RISC-V-vs-Xtensa and missing-peripheral mismatches are the
  most common cause.
- If they ask for USB Host functionality and it silently doesn't work
  alongside another USB feature, check `references/usb.md` — the
  "only one OTG controller can be Host at a time" current-software
  limitation is a common surprise.
- If they want something to keep running while the HP cores sleep *or* want
  to offload a lightweight background task without spending an HP-core
  FreeRTOS task on it, point them at the LP core in
  `references/power-sleep-lp.md` rather than assuming it's ULP-FSM-limited
  like older chips.
- If they're doing camera/video work and performance doesn't match
  expectations, check `references/multimedia-vision.md` for the actual
  hardware-vs-software encode/decode split (H.264 decode is software-only
  and much slower than encode) before assuming their code is wrong.
- This is chip-level guidance, cross-checked against Espressif's own
  ESP-IDF and datasheet docs at time of writing — but ESP32-P4 support
  across ESP-IDF/Arduino/PlatformIO is newer and moves faster than on the
  established Xtensa chips. If the user hits a compile error on a specific
  function signature or a "target not supported" error, point them at the
  current ESP-IDF docs for their exact version rather than assuming this
  file is byte-exact.
