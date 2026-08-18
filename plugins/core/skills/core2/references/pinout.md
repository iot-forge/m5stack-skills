# Core2 family pinout and peripheral map

Source: official spec/pinout tables at https://docs.m5stack.com/en/core/core2,
https://docs.m5stack.com/en/core/Core2_v1.3, https://docs.m5stack.com/en/core/core2_for_aws,
and https://docs.m5stack.com/en/core/Core2_For_AWS_v1.3, cross-checked against
each other (the four pages agree on every pin below except where a
per-revision difference is called out). GPIO numbers are the ESP32 GPIO
numbers as M5Stack labels them (e.g. "G21" means GPIO21). This is classic
ESP32 (`ESP32-D0WDQ6-V3`), not S3/P4 — don't assume S3-only peripherals
(native USB, dedicated GPIO, RMT with S3's extra channels) apply here.

## Shared internal I2C bus (SDA=G21, SCL=G22)

Every onboard chip that talks I2C shares this one bus. A bus-level fault
(missing pull-ups, wrong init, another driver holding the bus) breaks all
of them at once; a single wrong address only breaks one peripheral.

| Device | Function | I2C address | All revisions? |
|---|---|---|---|
| AXP192 | Power management IC | 0x34 | yes |
| BM8563 | RTC | 0x51 | yes |
| FT6336U | Capacitive touch controller | 0x38 | yes |
| MPU6886 **or** BMI270 | 6-axis IMU | 0x68 | yes (chip differs by revision — see SKILL.md's hardware-revisions table) |
| ATECC608B-TNGTLSU-G | Hardware crypto / secure element | 0x35 | **AWS line only** (For AWS, For AWS v1.3) |

- Touch controller also has a dedicated interrupt line: **G39**, asserted
  on touch events.
- If a probe/scan doesn't find the IMU or ATECC608 at the expected address,
  double check which physical revision the board actually is before
  assuming the code is wrong — see SKILL.md's hardware-revisions table.

## Display (ILI9342C, SPI, 320x240, 2.0" IPS)

| Pin | Function |
|---|---|
| G18 | SCK (clock) |
| G23 | MOSI (data out) |
| G38 | MISO (data in) |
| G5 | CS (chip select) |
| G15 | DC (data/command) |

## Touch (FT6336U, I2C — shares the bus above)

| Pin | Function |
|---|---|
| G21 | SDA (shared bus) |
| G22 | SCL (shared bus) |
| G39 | INT |

## Audio

| Pin | Function |
|---|---|
| G12 | I2S BCLK (bit clock) |
| G0 | I2S LRCK (word select) — also doubles as the PDM mic clock line |
| G2 | I2S DATA (to NS4168 amp / speaker) |
| G34 | SPM1423 mic DATA (PDM) |

- Speaker: NS4168 I2S amplifier driving a 1W speaker.
- Mic: SPM1423, PDM digital microphone.

## microSD card slot (SPI — shares display SCK/MOSI/MISO)

| Pin | Function |
|---|---|
| G18 | SCK (shared with display) |
| G23 | MOSI (shared with display) |
| G38 | MISO (shared with display) |
| G4 | CS |

Supports up to 16GB per official spec pages.

## AWS-line-only hardware

Present on Core2 For AWS and Core2 For AWS v1.3; **absent on plain Core2 /
Core2 v1.3**.

| Pin | Function |
|---|---|
| G21/G22 | ATECC608B I2C (shared bus, address 0x35) |
| G25 | SK6812 RGB LED data line (10x LEDs, NeoPixel-compatible timing) |

## Power / AXP192 (I2C 0x34, shared bus)

The AXP192 owns power sequencing for the whole board — battery
charge/monitor, all onboard voltage rails (including the ESP32's own core
rail), the vibration motor, and the status LED. It is not a simple GPIO
expander; use a proper AXP192 driver (M5Unified's `M5.Power`, M5Core2's
`Axp` object, or an ESP-IDF AXP192 component) rather than bit-banging
registers unless you specifically need to.

- Vibration motor: driven off one of the AXP192's LDO outputs (commonly
  documented as LDO3 in M5Stack's own material) — control it through the
  power-management API, not a plain GPIO write.
- Power button: short-press wakes/interacts, long-press powers off — this
  behavior is implemented by the AXP192 itself, not application firmware.
- RST button: hardware reset, separate from the power button.

## Serial / programming

| Pin | Function |
|---|---|
| G1 | UART TX (to USB-serial bridge) |
| G3 | UART RX (from USB-serial bridge) |

USB-serial bridge chip is CP2104 (plain Core2 pre-1.3, Core2 For AWS
pre-1.3) or CH9102F (Core2 v1.3, Core2 For AWS v1.3) — see SKILL.md's
hardware-revisions table. This is a USB-UART bridge, not native USB-CDC on
the ESP32 itself (classic ESP32 has no native USB peripheral).

## Expansion ports (HY2.0-4P)

Labeled PORT.A / PORT.B / PORT.C on the AWS-line base; the plain Core2 line
exposes the same style of HY2.0-4P port(s) plus an M5-Bus socket, but
official docs describe the plain line's Grove-style port only generically
("GROVE connector (I2C+I/O+UART)") without the A/B/C pin table below being
confirmed to apply — treat the table as AWS-line-confirmed and verify
against the plain Core2 schematic before relying on it for a non-AWS board.

| Port | Pins | Typical use |
|---|---|---|
| PORT.A | G32, G33 | I2C (SDA/SCL) |
| PORT.B | G26, G36 | Analog (DAC/ADC) |
| PORT.C | G13, G14 | UART (RXD2/TXD2) |

## Physical dimensions (by revision)

| Revision | Dimensions | Weight | Operating temp |
|---|---|---|---|
| Core2 (v1.0/v1.1) | 54.0 x 54.0 x 16.5mm | 54.9g | 0-60°C |
| Core2 v1.3 | 54.0 x 54.0 x 16.5mm | 58.8g | 0-60°C |
| Core2 For AWS | 54.0 x 54.0 x 23.5mm | 69.5g | 0-40°C |
| Core2 For AWS v1.3 | 54.0 x 54.0 x 23.7mm | 72.1g | 0-40°C |

The AWS line is thicker/heavier than the plain line because its base
integrates the RGB LED ring, larger antenna, and vibration motor housing
alongside the crypto chip — not just a firmware difference.

## Power draw (plain Core2, official figures — treat AWS line as similar
order of magnitude, not independently confirmed)

- Charging: ~0.219A
- Idle, powered off: ~0.055A
- Idle, powered on: ~0.147A
