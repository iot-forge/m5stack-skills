# ESP-IDF (bare-metal / RTOS) development

Use this path when the user explicitly wants ESP-IDF rather than Arduino —
e.g. they need FreeRTOS task control, are optimizing flash/RAM footprint, or
are building on top of M5Stack's own factory firmware.

**Chip-level capabilities live in a separate skill.** This file covers what's
specific to the Cardputer Adv's *board* (which chip sits at which I2C
address, which pins go where). For the ESP32-S3 *chip* itself — RMT, LEDC,
I2S, ULP-FSM/ULP-RISC-V, deep sleep, native USB OTG vs. the USB-Serial-JTAG
controller, dual-core task pinning, PSRAM config, WiFi/BLE coexistence, the
SIMD instructions behind esp-dsp/ESP-DL — see the `esp32-s3` skill instead
(shipped in the `esp32-chips` plugin of this same marketplace; install it
with `claude plugin install esp32-chips@m5stack` if it isn't present).
Reach for it whenever the user wants to do something with the chip that
isn't about this board's specific keyboard/IMU/audio/display wiring (e.g.
driving the IR emitter via RMT, tuning deep-sleep wake behavior, or pinning
tasks to cores).

## Reference implementation

M5Stack publishes the factory firmware for this board on the `CardputerADV`
branch of M5Cardputer-UserDemo:
https://github.com/m5stack/M5Cardputer-UserDemo/tree/CardputerADV

That's the most reliable source for exact register sequences and driver
code — point the user there for anything this file doesn't cover, and treat
what's below as orientation rather than a complete driver.

## I2C bus

Keyboard (TCA8418, 0x34), IMU (BMI270, 0x68), and audio codec (ES8311, 0x18)
all sit on one I2C bus (SDA=G8, SCL=G9). When writing the `i2c_master`
driver setup:

- Keep the bus in **synchronous transaction mode** (`trans_queue_depth = 0`
  in the `i2c_master_bus_config_t`/device config). Async queuing has been
  reported to exhaust the driver's internal transaction pool during the
  TCA8418's init register burst, surfacing as `ESP_ERR_INVALID_STATE`.
  Since all three devices share one bus/master handle, set this for the bus
  as a whole rather than per-device.

## TCA8418 keyboard controller

- I2C address `0x34`. Interrupt line on **G11**, active-low, falling-edge —
  wire a GPIO ISR to it rather than polling the bus continuously.
- Key event FIFO protocol:
  1. Read the `KEY_LCK_EC` register to get the pending event count.
  2. Read `KEY_EVENT_A` that many times to drain the FIFO. Each byte encodes
     one event: bit 7 = 1 for press / 0 for release, bits 6-0 = a 1-based
     key number (matrix position, not ASCII — you decode that yourself
     against the physical key layout).
  3. After draining, manually clear the `K_INT` bit in the `INT_STAT`
     register — the interrupt will not re-fire until this is cleared.
- A clean structure that several community ESP-IDF ports use: GPIO ISR sets
  a FreeRTOS queue/semaphore -> a dedicated keyboard task drains the FIFO,
  decodes key numbers to characters (handling shift/fn/capslock in
  software), and pushes decoded chars/events wherever the app needs them.
  This keeps I2C traffic and key decoding off the ISR.

## BMI270 IMU

I2C address `0x68`. It's a standard Bosch BMI270 — if the user needs a
full driver rather than hand-rolled register access, Bosch's own
`BMI270-Sensor-API` (C, MIT-licensed) is the reference implementation and
drops into an ESP-IDF component cleanly.

## ES8311 audio codec

I2C address `0x18` for control; audio data moves over I2S (bit clock G41,
LR clock G43, data out G46 to the speaker path, data in G42 from the mic).
Espressif's `esp-adf` / `audio_codec` components include an ES8311 driver
that's a reasonable starting point instead of writing register init from
scratch.

## Display (ST7789V2)

Standard SPI TFT — pins are CS=G37, DC/RS=G34, reset=G33, backlight=G38,
data/MOSI=G35, clock=G36. `esp_lcd` with the `esp_lcd_panel_st7789` driver
component is the standard ESP-IDF path; the Arduino-side `M5GFX` library's
ST7789 panel config is a useful cross-reference for correct init sequence
and offsets if the display shows a shifted or mirrored image.

---

# UIFlow2 (Blockly / MicroPython)

UIFlow2 is M5Stack's browser-based visual/MicroPython environment. It's the
fastest way to get something running with no toolchain install, at the cost
of less control over timing-sensitive code (interrupt-driven keyboard
handling, tight audio loops).

- Flash/connect the board through UIFlow2's web IDE (https://uiflow2.m5stack.com) — it talks to the board over USB serial, no separate flashing tool needed for normal use.
- Cardputer Adv support in UIFlow2 exposes the keyboard, display, IMU, and
  speaker as high-level blocks/MicroPython objects analogous to the Arduino
  `M5Cardputer` API — same peripherals, friendlier but less granular
  surface.
- For anything needing precise timing (audio DSP, fast interrupt-driven
  keyboard scanning, custom I2S handling), steer the user to Arduino or
  ESP-IDF instead — MicroPython's overhead makes that class of task harder.
- If the user reports UIFlow2-specific behavior this file doesn't cover, the
  authoritative source is M5Stack's UIFlow2 docs
  (https://docs.m5stack.com/en/uiflow2/introduction) rather than this skill,
  since the visual/MicroPython API surface changes independently of the
  Arduino library.
