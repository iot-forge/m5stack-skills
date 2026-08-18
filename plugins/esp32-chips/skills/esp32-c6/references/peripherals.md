# ESP32-C6 peripheral drivers

Chip-level capabilities exposed by ESP-IDF's `peripherals` API (the same
surface Arduino-ESP32's higher-level APIs are built on top of). This is the
"what can this chip actually do at the hardware level" reference — use it
when the user needs more than what a board's high-level library exposes, or
is doing bare-metal ESP-IDF work. All counts below are for the bare
ESP32-C6 die; a specific board may expose fewer if pins are already claimed
by in-package flash or the board's own routing — check that board's own
`references/pinout.md`.

## RMT (Remote Control Transceiver)

Generates and captures precisely-timed pulse trains in hardware, same
peripheral family and driver model as every other current ESP32 chip. Most
common modern use is driving WS2812/NeoPixel-style addressable LEDs (the
`led_strip` component built on RMT); also used for genuine IR transmit/
receive and any other protocol needing exact pulse widths. Check the
current ESP-IDF version's docs for the exact channel count — it's grown
across ESP-IDF releases on other chips and wasn't independently pinned down
for this chip.

## LEDC (LED Control / PWM)

Hardware PWM generator, up to 6 channels per the datasheet. Used for LED
brightness/dimming, simple tone/buzzer output, and non-precision motor
speed control. For anything needing closed-loop motor control or
complementary/dead-time PWM pairs for H-bridges, use MCPWM instead.

## I2S (Inter-IC Sound)

One I2S controller (fewer than S3's multiple instances) — digital audio
I/O for codec chips, microphones, and speaker amps. If a board needs
simultaneous, independent audio in and out paths, check whether one shared
I2S controller (in full-duplex mode, if the driver supports it for the
use case) is sufficient before assuming two independent buses are
available the way they might be on a bigger chip.

## ADC (Analog-to-Digital Converter)

One 12-bit SAR ADC unit, up to 7 channels — unlike classic ESP32/ESP32-S3,
this chip does **not** split ADC into two separate units (no "ADC1 vs
ADC2" distinction), so the classic-ESP32 "ADC2 can't be read while WiFi is
active" gotcha does not apply in the same form here. This wasn't
independently stress-tested against active radio use, though — if a user
reports noisy/unavailable ADC readings specifically while the
WiFi/BLE/802.15.4 radio is transmitting, don't rule out some radio-related
interaction without checking current ESP-IDF errata first, but don't assume
the classic-ESP32 ADC2 restriction carries over either.

## PCNT (Pulse Counter)

Hardware pulse counting for rotary encoders, flow meters, and tachometers,
same driver model as other ESP32 chips. Exact channel/unit count for this
chip wasn't independently verified — check current ESP-IDF docs if the user
needs more channels than a single quick test confirms.

## MCPWM (Motor Control PWM)

Purpose-built for motor control — complementary PWM outputs with dead-time
insertion for H-bridge/BLDC driving, capture inputs, fault handling. Reach
for this instead of LEDC whenever the user is actually driving a motor.

## TWAI (Two-Wire Automotive Interface) — two independent controllers

This chip has **2 independent TWAI/CAN 2.0-compatible controllers** —
notably more than the single controller on ESP32-S3, ESP32-P4, or classic
ESP32. That means a C6-based board can genuinely run two separate CAN buses
at once without needing an external CAN controller chip for the second
one — though each bus still needs its own external CAN transceiver chip,
the C6 only provides the controller logic, not the differential bus
driver. Relevant for M5Stack CAN-related Units/boards more than typical
handheld firmware.

## Storage: SD-SPI only — no SDMMC host, no eMMC

This is a real capability gap versus classic ESP32/S3/P4, worth stating
plainly: **ESP32-C6 has no SDMMC host controller at all.** Per Espressif's
own driver docs: "ESP32-C6 does not have an SDMMC Host controller, and can
only use SPI protocol for communication with cards." Practical
consequences:

- SD cards are reachable only via **SD-SPI** (the SD protocol run over a
  regular SPI peripheral) — slower than a native 1-bit/4-bit SDMMC bus, but
  works over whatever pins the board's SPI wiring uses.
- **eMMC is not possible at all** on this chip — eMMC requires the parallel
  SDMMC protocol, which doesn't exist here.
- If a user pastes SDMMC-host-style init code (`sdmmc_host_t`,
  `SDMMC_HOST_DEFAULT()` configured for the dedicated SDMMC peripheral)
  from an S3/P4/classic-ESP32 project, it will not compile/link against
  this target — point them at the SD-SPI driver path instead.

## SDIO slave — the radio-co-processor mechanism

Separately from the storage story above, this chip also has an **SDIO
slave** controller — the mechanism that lets a C6 act as a WiFi/BLE/
802.15.4 co-processor *to* a separate host SoC that has no radio of its
own. This is exactly the pattern M5Stack's Tab5 uses: the ESP32-C6-MINI-1U
sits on Tab5's board as an SDIO slave, with the main ESP32-P4 as the SDIO
host, running Espressif's `esp-hosted`-style firmware on the C6 side. Don't
confuse this with the SD-card-host capability above — SDIO slave and
SD-SPI/no-SDMMC-host are unrelated peripherals that happen to share the
"SD" name family.

## PARLIO (Parallel IO)

A general-purpose parallel input/output peripheral for moving multiple
bits per clock — not a display or camera peripheral (this chip has neither,
see below). Useful for things like driving an external parallel-latch
device or capturing multi-bit sensor data faster than bit-banged GPIO
could.

## SDM (Sigma-Delta Modulation)

A lightweight peripheral for generating a pulse-density-modulated output —
useful for a simple analog-ish signal (dimming, basic analog audio/control
voltage) using far fewer resources than a full LEDC PWM channel when the
use case tolerates the different output characteristics. Not commonly
needed for typical M5Stack application firmware, but available if the user
specifically asks about it.

## GPTimer and dedicated GPIO

Two general-purpose hardware timers (54-bit) plus a dedicated 52-bit system
timer, for precise periodic interrupts, one-shot delays, or timestamp
capture without burning a FreeRTOS task on `vTaskDelay` polling. "Dedicated
GPIO" is the usual lower-latency, instruction-level GPIO access path for
very tight, jitter-free bit-banging timing needs.

## Temperature sensor

Reads the die's internal temperature, not ambient room temperature — same
caveat as every other current ESP32 chip with this peripheral. Useful for
thermal-throttling logic or a rough sanity check, not as an environmental
sensor (M5Stack's ENV Unit family covers that use case instead).

## No capacitive touch sensing

Unlike classic ESP32, ESP32-S3, and ESP32-P4 (all of which have a built-in
capacitive touch peripheral), **ESP32-C6 has no touch-sensing hardware** —
this wasn't found in any peripheral list or datasheet section checked when
this skill was built, consistent across three independent source fetches.
If a user wants touch-button input on a C6 board, they need an external
touch controller chip, not the chip's own GPIO.

## No LCD/camera hardware

This chip has no dedicated parallel LCD interface (no I80/RGB timing
generator the way S2/S3/P4 have) and no MIPI-DSI/CSI or DVP camera
controller. ESP-IDF's `esp_lcd` component documentation page exists for
this target, but only backs SPI- and I2C-interfaced displays through it —
there's no parallel/RGB/MIPI hardware underneath for this chip to expose.
If a user wants a fast parallel display or a camera, they need a chip like
ESP32-S3 (I2S-as-parallel-bus trick) or ESP32-P4 (real MIPI-DSI/CSI), not
this one.

## SPI, UART, I2C — fewer general-purpose instances than S3/P4

Worth flagging explicitly since it's easy to assume parity with bigger
chips: this chip has **3 SPI controllers total, but only one
(SPI2) is general-purpose** — SPI0 and SPI1 are dedicated to the flash
connection and not available for peripherals. So a board can have at most
one general-purpose SPI bus without resorting to bit-banging or an I2C/SPI
expander, unlike S3/P4 which support multiple independent general-purpose
SPI instances. UART is 2 (plus a separate LP UART accessible to the LP
core), and I2C is 2 (plus a separate LP I2C, also LP-core-accessible) — check
current ESP-IDF docs for exact behavior since these numbers can shift
across releases.

## Security: HMAC and Digital Signature (DS) peripherals

Hardware-accelerated HMAC computation and a Digital Signature peripheral
for TLS client-certificate-style authentication without exposing the
private key to application code — niche, only relevant for device-identity/
secure-provisioning work. Not covered in depth here; see ESP-IDF's security
guides if this comes up.
