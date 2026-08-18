# ESP32-P4 peripheral drivers

Chip-level capabilities exposed by ESP-IDF's `peripherals` API (the same
surface Arduino-ESP32's higher-level APIs are built on top of, where
Arduino-ESP32 support exists — ESP32-P4 Arduino coverage is newer and
thinner than on the S3, check board-specific reference files for current
status). This is the "what can this chip actually do at the hardware
level" reference — for MIPI-CSI/DSI, the ISP, JPEG/H.264 codecs, and PPA/
2D-DMA, see `multimedia-vision.md` instead; those are covered separately
given how much depth they warrant.

## RMT (Remote Control Transceiver)

Same role as on other ESP32 chips: generates and captures precisely-timed
pulse trains in hardware. Most common modern use is driving WS2812/
NeoPixel-style addressable LEDs (the `led_strip` component) and genuine IR
transmit/receive, plus any other protocol needing exact pulse widths. The
P4 has one RMT peripheral (vs. potentially more channels on some other
chips) — check the current ESP-IDF version's channel count before assuming
parity with an S3 project being ported over.

## LEDC (LED Control / PWM)

Hardware PWM generator — LED brightness/dimming, tone/buzzer output, simple
motor speed control. One LEDC peripheral on the P4. For anything needing
closed-loop motor control (current sensing, complementary/dead-time PWM
pairs for H-bridges), use MCPWM instead.

## I2S (Inter-IC Sound)

Digital audio I/O for codec chips, microphones, and speaker amps. The P4
has **three HP I2S instances plus one LP I2S** — the LP I2S can keep an
audio path alive (e.g. a low-power wake-word listener feeding samples to
the LP core) without spinning up an HP core, which is new relative to the
S3's single-domain I2S. Also usable as a general fast parallel/serial DMA
data bus beyond audio, same as on other ESP32 chips.

## ADC (Analog-to-Digital Converter)

Two ADC controllers: ADC1 with 8 channels, ADC2 with 6 channels. Same
non-linearity/reference-drift caveats as other ESP32-series ADCs apply —
point users reporting noisy/inconsistent readings at ESP-IDF's ADC
calibration API (`esp_adc/adc_cali`) before assuming a wiring/sensor fault.

## Capacitive touch sensor

14 touch channels — touch-button input using the chip's built-in
capacitive sensing, no extra components needed. Not a replacement for a
real touchscreen controller (that's a separate chip on boards with a touch
display, e.g. Tab5's GT911/ST7123 — see that board's SKILL.md).

## PCNT (Pulse Counter)

Hardware pulse counting with configurable edge detection, glitch
filtering, and up/down counting — rotary encoders, flow meters,
tachometers. One PCNT controller on the P4.

## MCPWM (Motor Control PWM)

Purpose-built for motor control: complementary PWM outputs with dead-time
insertion (H-bridge/BLDC driving), capture inputs for feedback, fault
handling. One MCPWM controller. Reach for this instead of LEDC whenever the
user is actually driving a motor rather than dimming an LED.

## TWAI (Two-Wire Automotive Interface)

ESP-IDF's name for a CAN bus controller (CAN 2.0B compatible). The P4 has
one TWAI controller and, like other ESP32 chips, needs an external CAN
transceiver — the chip only provides the controller logic, not the
differential bus driver.

## Ethernet MAC (EMAC)

The P4 has a built-in Ethernet MAC operating in **RMII mode** — it needs an
external PHY chip (the MAC alone isn't a complete Ethernet interface).
There's no RGMII option on this chip, so don't expect gigabit Ethernet;
RMII tops out at 100Mbps. This is a genuine differentiator from the S3/C-series
chips, none of which have a hardware EMAC at all (they rely on external
SPI-Ethernet controllers instead) — if a user wants wired Ethernet and
picked a P4 board specifically for it, the built-in EMAC + external PHY is
the intended path rather than an SPI Ethernet chip.

## SDMMC / SD-SPI / SDIO host

The P4 has a dedicated SDIO/SD/MMC host controller (SD 3.0-class), usable
for SD cards, eMMC, or — notably — as the link to a companion radio chip.
On M5Stack's Tab5, this exact peripheral is what carries WiFi/BLE traffic
to the onboard ESP32-C6 over SDIO (see the `m5stack-tab5` skill's
`WiFi.setPins()` section for the pin roles in that specific application).
SD-SPI (reusing a regular SPI peripheral in slower single-bit mode) remains
available as a fallback on boards that don't wire up the dedicated host
controller for a given card slot — check the specific board's pinout.

## GPTimer

General-purpose hardware timer/counter for precise periodic interrupts,
one-shot delays, or timestamp capture without burning a FreeRTOS task on
`vTaskDelay` polling. HP system provides 2× 52-bit system timers and 4×
54-bit general-purpose timers, plus 2× 32-bit main watchdogs (MWDT); the LP
domain adds its own 32-bit watchdog (RWDT) and a 48-bit RTC timer.

## I3C

The P4 adds one I3C controller — a newer, faster, backward-compatible
successor to I2C (higher throughput, in-band interrupts, dynamic addressing)
that isn't present on M5Stack's S3-based boards. Relevant mainly if the
user is integrating a newer sensor/peripheral that specifically targets
I3C rather than I2C; most existing M5Stack peripheral ICs (IMUs, RTCs, I/O
expanders) are I2C-only and don't need this.

## PARLIO (Parallel IO)

A general-purpose parallel data peripheral — send or receive multiple bits
per clock cycle over a group of GPIOs. Useful for high-throughput
non-MIPI, non-SDIO interfaces (e.g. driving parallel LCDs without going
through the LCD_CAM/legacy DVP path, or bit-banging wide buses in
hardware). One controller on the P4; niche relative to the peripherals
above, but worth knowing exists if a user has an unusual high-bandwidth
GPIO requirement.

## BitScrambler

A small, programmable DMA-adjacent peripheral for arbitrary bit-level
reordering/manipulation of data streams in hardware. Niche — mainly useful
for driving unusual LED matrix/panel formats or custom serial protocols
where the bit ordering doesn't match any standard peripheral's output
format. Not detailed further here; check ESP-IDF's BitScrambler docs if a
user's specific use case needs it.

## Temperature sensor

Reads the **die's internal temperature**, not ambient room temperature —
same caveat as every other ESP32 chip. For ambient sensing, point the user
at an external sensor (M5Stack's ENV Unit family, for instance).

## VAD (Voice Activity Detection)

A dedicated hardware unit that flags when incoming audio (via I2S) looks
like speech versus silence/noise, without spending CPU cycles on it.
Intended for always-on "is someone talking" gating ahead of a full
wake-word/ASR pipeline — pairs naturally with the LP core and LP I2S (see
`power-sleep-lp.md`) for an always-listening path that barely touches the
HP cores' power budget.

## SPI, UART, and I2C: multiple independent instances

4 SPI + 1 LP SPI, 5 UART + 1 LP UART, 2 I2C + 1 LP I2C + 1 dedicated analog
I2C. More instances than the S3 across the board — a P4 board can
legitimately have several independent SPI/UART/I2C buses without sharing,
which matters when planning pin budgets for a design with many peripherals
(e.g. Tab5's camera, display-adjacent ICs, RS485, and Grove/M5-Bus all
wanting their own bus). Don't assume a single shared bus without checking
the specific board's pinout reference — and note the LP-domain UART/SPI/I2C
instances are accessible from the LP core independently of the HP cores
(see `power-sleep-lp.md`).

## Security peripherals

Hardware AES/ECC/HMAC/RSA/SHA accelerators, RSA/ECDSA digital-signature
peripherals, a Key Manager with SRAM-PUF-derived hardware unique key, TRNG,
and permission-control (PMS) access protection. Not detailed further in
this skill — niche relative to typical hobbyist/M5Stack firmware work,
check ESP-IDF's security guides if a user is doing device-identity or
secure-provisioning work.
