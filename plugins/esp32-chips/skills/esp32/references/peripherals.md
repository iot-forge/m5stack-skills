# ESP32 (classic) peripherals

Detail and gotchas for each peripheral block. All channel/unit counts below
are for the bare D0WD/D0WDQ6/D0WDR2 die — a specific board may expose fewer
if pins are already claimed by on-board flash/PSRAM, a display, or other
fixed-purpose hardware. Check that board's own `references/pinout.md`.

## RMT (Remote Control Transceiver)

8 channels, each independently configurable as TX or RX, with a dedicated
64×32-bit memory block per channel (expandable by borrowing adjacent idle
channels' memory). Built for generating/capturing precisely-timed digital
waveforms in hardware, off the CPU:

- IR remote encode/decode (NEC, RC5, and similar protocols)
- WS2812/NeoPixel and other single-wire addressable LED protocols
- Arbitrary custom one-wire-style protocols where bit-banging in software
  would jitter

Same peripheral family and driver model as later chips (S3/P4); nothing
classic-ESP32-specific to watch for here beyond the 8-channel limit (S3 has
the same 8; don't assume a P4-class channel count if porting code down).

## LEDC (LED PWM Controller)

16 channels total, split into two groups of 8 (traditionally called
"high-speed" and "low-speed" groups — the split exists on this chip
specifically; check ESP-IDF's version-specific docs if porting old code,
since the high/low-speed distinction was simplified away on some newer
chips). Up to 20-bit resolution per channel, shared among a pool of
timers. Common uses: LED dimming, piezo buzzer tone generation, and simple
DC motor speed control where you don't need MCPWM's extra features.

## I2S

2 I2S controllers. Beyond standard stereo digital audio in/out (I2S
mic/codec, speaker), the classic ESP32's I2S peripheral can also run in a
parallel-bus mode — this is the mechanism ESP32-CAM-style modules (and any
board pairing this chip with an OV2640/OV3660-class camera over an 8-bit or
16-bit parallel interface) use to capture camera data, since this chip has
no dedicated MIPI-CSI or DVP-specific camera controller the way P4 does.
If a user is bringing up a parallel camera on a classic-ESP32 board, this
is the peripheral to point them at (typically via the `esp32-camera`
component rather than hand-rolling the I2S config).

## ADC, DAC, and touch — the ADC2/WiFi conflict

Two SAR ADC units, 18 channels combined, 12-bit resolution:

- **ADC1** (8 channels, GPIO32–39): safe to use regardless of WiFi state.
- **ADC2** (10 channels, GPIO0/2/4/12–15/25–27): **shares underlying RF
  hardware with the WiFi radio and cannot be read while WiFi is active**
  (`adc2_get_raw()` returns an error, or the Arduino-layer `analogRead()`
  on an ADC2 pin returns a stale/garbage value, once `WiFi.begin()` or
  softAP mode has been called). This is one of the most common "my analog
  sensor stopped working" reports on classic ESP32 — always check whether
  the pin in question is on ADC2 before assuming a wiring or sensor fault.
  There is no clean fix short of moving the sensor to an ADC1 pin, or
  disabling WiFi during the reads (`WiFi.mode(WIFI_OFF)`, then re-enabling)
  if the application can tolerate the radio dropping. This limitation does
  **not** exist the same way on S3/P4 (S3 also splits ADC1/ADC2 with a
  similar restriction; P4 has no radio to conflict with).
- **DAC**: 2 channels, 8-bit, fixed to GPIO25 (DAC1) and GPIO26 (DAC2).
  Analog audio-out or simple analog signal generation; note the low 8-bit
  resolution is genuinely coarse for anything audio-quality — most
  M5Stack audio boards use an external I2S DAC/codec chip instead and
  don't rely on this peripheral.
- **Touch**: 10 capacitive touch channels (T0–T9), several of which
  overlap ADC2 pins (they're the same physical GPIOs, different peripheral
  muxed onto them) — can't use a pin as both simultaneously. Touch-based
  wake from sleep is covered in `references/power-sleep-ulp.md`.
- **No internal temperature sensor.** Unlike S2/S3/C3/P4, classic ESP32
  has no on-die temperature sensor peripheral exposed via ESP-IDF's
  `temperature_sensor` API — don't assume it exists if porting code down
  from a newer chip's example.

## PCNT (Pulse Counter)

8 independent units, each with 2 channels supporting quadrature decoding
with configurable edge/level filtering. Hardware pulse counting for rotary
encoders, flow meters, and tachometers without burning CPU cycles on
interrupt-driven counting.

## MCPWM (Motor Control PWM)

2 units, each with 3 timers/6 PWM outputs plus capture inputs and
fault-handling logic. Built for H-bridge motor drivers, ESCs, and
servo-adjacent timing needs beyond what LEDC's simpler PWM offers —
reach for this instead of LEDC when the user needs synchronized multi-phase
outputs, dead-time insertion, or hardware fault shutdown.

## TWAI (CAN 2.0-compatible)

1 controller, ISO 11898-1-compatible (CAN 2.0). On V1.0 silicon the
minimum supported baud rate was 25kHz; V3.0-and-later silicon lowers that
floor to 12.5kHz (see the main `SKILL.md`'s "Why the V3 chip revision
matters"). Espressif's naming is TWAI (Two-Wire Automotive Interface);
older docs and some libraries still call it "CAN" — same peripheral.

## SDMMC host and SD-SPI

A dedicated SD/MMC host controller supporting the SD Memory Card v3.01
standard, usable in 1-bit or 4-bit SDIO/SD modes — this is the
higher-throughput path for SD card access. A generic SD-SPI fallback (SD
card protocol over any general-purpose SPI peripheral, slower but usable
on boards that didn't route the dedicated SDMMC pins to the card slot) is
also available, same as on other ESP32 variants.

## SDIO slave — a mode unique to this chip in the family

Beyond the SDMMC *host* controller above, classic ESP32 can also run its
SDIO interface in **slave** mode — i.e., the ESP32 acts as an SDIO
peripheral device that a separate host SoC (a Linux SBC, another MCU with
an SDIO host controller) talks to. This is the mechanism behind
Espressif's `esp-hosted` project, where an ESP32 serves as a WiFi/Bluetooth
co-processor for a host that has no radio of its own — conceptually the
same pattern M5Stack's Tab5 uses pairing an ESP32-P4 (no radio) with an
ESP32-C6 (radio) over SDIO, except here the classic ESP32 itself would be
the radio-side slave. Niche, but worth knowing about if a user asks "can
my ESP32 be a WiFi module for another microcontroller" — the answer is
yes, via SDIO slave (or, more commonly in practice, via a simpler SPI/UART
AT-command-style link).

## Hall sensor — deprecated, don't build on it

Classic ESP32 has a built-in Hall-effect sensor, read via a differential
measurement across two fixed GPIOs (traditionally GPIO36/GPIO39, which are
also ADC1 channels). It was **removed from ESP-IDF's public API starting
with ESP-IDF 5.0** (and the Arduino-ESP32 core's `hallRead()` is likewise
deprecated/removed in current versions) due to accuracy/reliability
concerns Espressif documented when pulling it. If a user's code calls
`hallRead()` and won't compile on a current toolchain, that's why — point
them at an external magnetometer/Hall-effect breakout instead of trying to
resurrect the internal one, unless they're specifically maintaining a
legacy codebase pinned to an old ESP-IDF/Arduino-ESP32 version.

## GPTimer and dedicated GPIO

Standard general-purpose hardware timers (4 on this chip, in two timer
groups of 2) for scheduling/timeouts independent of RMT/LEDC/MCPWM's
purpose-built timing hardware, plus the usual low-latency bit-banged GPIO
path for cases where even the fastest software toggle loop isn't fast or
jitter-free enough.

## GPIO strapping and input-only pins — wiring gotchas

- **Strapping pins** (GPIO0, GPIO2, GPIO5, GPIO12, GPIO15): sampled at
  reset to select boot mode (UART download vs. normal boot) and a couple
  of other startup options. Pulling one of these to an unexpected level
  with external circuitry (an LED, a button wired the wrong way, a
  pull-up/down that conflicts with the chip's internal default) is a
  classic cause of "board won't boot" or "board boots into download mode
  randomly" reports — worth checking first when a board bricks itself
  intermittently. GPIO12 in particular also affects flash voltage
  selection (VDD_SDIO) at boot on some module configurations — don't
  drive it externally without checking the specific module's strapping
  table.
- **Input-only pins** (GPIO34, 35, 36, 37, 38, 39): no output driver, no
  internal pull-up/pull-down resistors. Fine for sensor inputs
  (several are also ADC1 channels) but cannot be used for anything needing
  an output or an internal pull — an external pull-up/down resistor is
  required if the signal needs one.
